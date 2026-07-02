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

Required environment variables (set these in the Railway dashboard -> Variables,
never commit them to the repo):

  IG_ACCESS_TOKEN         Long-lived Instagram Graph API access token
  IG_BUSINESS_ACCOUNT_ID  Instagram Business Account numeric ID
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
import os
import time

from flask import Flask, send_from_directory, jsonify, request
import requests

from content_library import POSTS
from render import render_post

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
STATE_FILE = os.path.join(BASE_DIR, "rotation_state.json")

os.makedirs(GENERATED_DIR, exist_ok=True)

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


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
    url = f"{GRAPH_BASE}/{ig_user_id}/media"
    resp = requests.post(url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }, timeout=60)
    if not resp.ok:
        raise RuntimeError(f"create_media_container failed: {resp.status_code} {resp.text}")
    return resp.json()["id"]


def publish_media_container(ig_user_id, access_token, container_id):
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    resp = requests.post(url, data={
        "creation_id": container_id,
        "access_token": access_token,
    }, timeout=60)
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

    container_id = create_media_container(ig_user_id, access_token, image_url, post["caption"])
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
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
