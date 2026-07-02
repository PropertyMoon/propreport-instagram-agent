"""
PropReport Instagram posting agent.

Runs as a small Flask web service on Railway:
- GET  /                 health check
- GET  /images/<name>    serves generated post images (must be publicly reachable
                          for Instagram's Graph API to fetch them)
- POST /run              renders the next post in rotation and publishes it to
                          Instagram. This is the endpoint Railway's Cron Schedule
                          should hit (see railway.json).
- GET  /run              same as POST, for convenience/manual testing in a browser
                          (protected by RUN_SECRET query param, see below)
- GET  /debug-token      diagnostic endpoint: verifies IG_ACCESS_TOKEN /
                          IG_BUSINESS_ACCOUNT_ID work against Graph API without
                          posting anything.

Required environment variables (set these in the Railway dashboard -> Variables,
never commit them to the repo):

  IG_ACCESS_TOKEN         Long-lived Instagram access token (IGAA... from the
                           Instagram Business Login flow, or EAA... from the
                           older Facebook Login for Business flow)
  IG_BUSINESS_ACCOUNT_ID  The Instagram-scoped User ID tied to that token.
                           NOTE: for the Instagram Business Login (IGAA...) flow
                           this is NOT the Page-scoped ID shown in the "Generate
                           access tokens" table in the app dashboard -- it's the
                           id returned by GET /v21.0/me?access_token=... (or the
                           id field returned alongside username when you test
                           the token). See README for how to find it.
  PUBLIC_BASE_URL         The public URL Railway assigns this service,
                           e.g. https://propreport-instagram.up.railway.app
                           (no trailing slash). Needed so Instagram can fetch
                           the generated image over the internet.
  RUN_SECRET              A random string you choose. Required as ?secret=...
                           on manual GET /run calls and used by the cron job,
                           so randos on the internet can't trigger posts.

Local test:
  pip install -r requirements.txt
  export IG_ACCESS_TOKEN=... IG_BUSINESS_ACCOUNT_ID=... PUBLIC_BASE_URL=http://localhost:8080 RUN_SECRET=test
  python app.py
  curl "http://localhost:8080/run?secret=test"
"""
import json
import logging
import os
import time

from flask import Flask, send_from_directory, jsonify, request
import requests

from content_library import POSTS
from render import render_post

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("propreport-instagram-agent")

BASE_DIR = os.path.dirname(__file__)
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
STATE_FILE = os.path.join(BASE_DIR, "rotation_state.json")

os.makedirs(GENERATED_DIR, exist_ok=True)

GRAPH_API_VERSION = "v21.0"

# Which host to call depends on how the access token was generated:
# - IGAA... tokens (Instagram Business Login / "API setup with Instagram login")
#   must use graph.instagram.com
# - EAA... tokens (Facebook Login for Business, IG linked via a Facebook Page)
#   must use graph.facebook.com
# Set GRAPH_HOST env var to override; defaults to graph.instagram.com since
# that's the flow this project's README walks through.
GRAPH_HOST = os.environ.get("GRAPH_HOST", "graph.instagram.com")
GRAPH_BASE = f"https://{GRAPH_HOST}/{GRAPH_API_VERSION}"

# How long to wait for a media container to finish processing before giving up.
CONTAINER_POLL_MAX_ATTEMPTS = 15
CONTAINER_POLL_INTERVAL_SECONDS = 4


def _redact_url(url, params):
    """Build the full request URL (query string included) with the access_token
    value masked, safe to write to logs."""
    safe_params = dict(params or {})
    if "access_token" in safe_params and safe_params["access_token"]:
        tok = safe_params["access_token"]
        safe_params["access_token"] = f"{tok[:8]}...{tok[-4:]}" if len(tok) > 12 else "***"
    query = "&".join(f"{k}={v}" for k, v in safe_params.items())
    return f"{url}?{query}" if query else url


def load_rotation_index():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f).get("next_index", 0)
        except (json.JSONDecodeError, OSError):
            return 0
    return 0


def save_rotation_index(idx):
    with open(STATE_FILE, "w") as f:
        json.dump({"next_index": idx, "updated_at": time.time()}, f)


def create_media_container(ig_user_id, access_token, image_url, caption):
    # access_token is sent as a query param (not a POST body field) -- graph.instagram.com
    # has been observed to reject/mis-handle access_token when it's only in the form body
    # on some endpoints/versions, returning "Cannot parse access token" even for a valid token.
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    params = {"access_token": access_token}
    logger.info("POST create_media_container -> %s", _redact_url(url, params))
    resp = requests.post(
        url,
        params=params,
        data={
            "image_url": image_url,
            "caption": caption,
        },
        timeout=60,
    )
    logger.info("create_media_container response: %s %s", resp.status_code, resp.text)
    if not resp.ok:
        raise RuntimeError(f"create_media_container failed: {resp.status_code} {resp.text}")
    return resp.json()["id"]


def wait_for_container_ready(container_id, access_token):
    """Poll the container's status_code until it's FINISHED (or ERROR/EXPIRED).

    Instagram processes media asynchronously after /media returns a container
    id -- publishing before it reports FINISHED fails with error 9007 "Media
    ID is not available". Images are usually ready within a few seconds.
    """
    url = f"{GRAPH_BASE}/{container_id}"
    params = {"fields": "status_code", "access_token": access_token}

    for attempt in range(1, CONTAINER_POLL_MAX_ATTEMPTS + 1):
        logger.info(
            "GET container status (attempt %s/%s) -> %s",
            attempt, CONTAINER_POLL_MAX_ATTEMPTS, _redact_url(url, params),
        )
        resp = requests.get(url, params=params, timeout=30)
        logger.info("container status response: %s %s", resp.status_code, resp.text)

        if not resp.ok:
            raise RuntimeError(f"container status check failed: {resp.status_code} {resp.text}")

        status_code = resp.json().get("status_code")

        if status_code == "FINISHED":
            return
        if status_code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container processing failed with status_code={status_code}: {resp.text}")

        # IN_PROGRESS or anything else not-yet-terminal: wait and retry.
        time.sleep(CONTAINER_POLL_INTERVAL_SECONDS)

    raise RuntimeError(
        f"container {container_id} did not finish processing after "
        f"{CONTAINER_POLL_MAX_ATTEMPTS * CONTAINER_POLL_INTERVAL_SECONDS}s"
    )


def publish_media_container(ig_user_id, access_token, container_id):
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    params = {"access_token": access_token}
    logger.info("POST publish_media_container -> %s", _redact_url(url, params))
    resp = requests.post(
        url,
        params=params,
        data={
            "creation_id": container_id,
        },
        timeout=60,
    )
    logger.info("publish_media_container response: %s %s", resp.status_code, resp.text)
    if not resp.ok:
        raise RuntimeError(f"publish_media_container failed: {resp.status_code} {resp.text}")
    return resp.json()["id"]


@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "propreport-instagram-agent"})


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(GENERATED_DIR, filename)


def _do_run():
    access_token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
    public_base_url = os.environ["PUBLIC_BASE_URL"].rstrip("/")

    idx = load_rotation_index()
    post = POSTS[idx % len(POSTS)]

    image_path = render_post(post, GENERATED_DIR)
    image_filename = os.path.basename(image_path)
    image_url = f"{public_base_url}/images/{image_filename}"
    logger.info("Publishing post id=%s using image_url=%s", post["id"], image_url)

    container_id = create_media_container(ig_user_id, access_token, image_url, post["caption"])
    wait_for_container_ready(container_id, access_token)
    media_id = publish_media_container(ig_user_id, access_token, container_id)

    save_rotation_index(idx + 1)

    return {
        "posted": post["id"],
        "media_id": media_id,
        "image_url": image_url,
        "next_index": (idx + 1) % len(POSTS),
    }


@app.route("/run", methods=["GET", "POST"])
def run():
    expected_secret = os.environ.get("RUN_SECRET")
    provided_secret = request.args.get("secret") or request.headers.get("X-Run-Secret")
    if expected_secret and provided_secret != expected_secret:
        return jsonify({"error": "unauthorized"}), 401

    try:
        result = _do_run()
        return jsonify({"success": True, **result})
    except Exception as e:
        logger.exception("run() failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/debug-token")
def debug_token():
    """Manual diagnostic: confirms the token/id env vars work against Graph API
    without touching rotation state or posting anything. Protected by RUN_SECRET
    just like /run. Visit /debug-token?secret=... to use.
    """
    expected_secret = os.environ.get("RUN_SECRET")
    provided_secret = request.args.get("secret") or request.headers.get("X-Run-Secret")
    if expected_secret and provided_secret != expected_secret:
        return jsonify({"error": "unauthorized"}), 401

    access_token = os.environ.get("IG_ACCESS_TOKEN", "")
    ig_user_id = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "")

    url = f"{GRAPH_BASE}/{ig_user_id}"
    params = {"fields": "username", "access_token": access_token}
    logger.info("GET debug_token -> %s", _redact_url(url, params))
    resp = requests.get(url, params=params, timeout=30)
    logger.info("debug_token response: %s %s", resp.status_code, resp.text)

    return jsonify({
        "graph_base": GRAPH_BASE,
        "ig_user_id": ig_user_id,
        "token_length": len(access_token),
        "token_prefix": access_token[:8] if access_token else None,
        "token_suffix": access_token[-4:] if access_token else None,
        "status_code": resp.status_code,
        "response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
