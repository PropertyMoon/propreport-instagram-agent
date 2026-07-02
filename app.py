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
- GET  /status           read-only view of rotation state: posts remaining,
                          estimated days of content left, whether alerts have
                          already fired. Does not post anything.

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

Optional environment variables (content rotation + low-content email alerts):

  POSTS_PER_WEEK          How many times/week the cron job posts. Default 3.
                           Used only to convert "days of content left" into a
                           post count for the low-content alert.
  LOW_CONTENT_ALERT_DAYS  Send an email alert once remaining unposted content
                           drops to this many days' worth (based on
                           POSTS_PER_WEEK). Default 2.
  ALERT_EMAIL_TO          Email address to send low-content / out-of-content
                           alerts to. If unset, alerting is disabled (the app
                           still stops posting at the end of rotation either way).
  SMTP_HOST, SMTP_PORT,
  SMTP_USERNAME,
  SMTP_PASSWORD,
  SMTP_FROM               SMTP credentials used to send the alert email.
                           Works with a Gmail app password (smtp.gmail.com,
                           port 587) or any transactional email provider's
                           SMTP endpoint. SMTP_FROM defaults to SMTP_USERNAME.

Rotation behavior: posts are published in order (p01, p02, ...) and do NOT
loop back to the start. Once the last post has been published, /run returns
an "out of content" response and does not post anything until you add more
entries to content_library.py. An email alert (if ALERT_EMAIL_TO is set) is
sent once when remaining content drops to LOW_CONTENT_ALERT_DAYS worth, and
again when content is fully exhausted.

Local test:
  pip install -r requirements.txt
  export IG_ACCESS_TOKEN=... IG_BUSINESS_ACCOUNT_ID=... PUBLIC_BASE_URL=http://localhost:8080 RUN_SECRET=test
  python app.py
  curl "http://localhost:8080/run?secret=test"
"""
import json
import logging
import math
import os
import smtplib
import time
from email.mime.text import MIMEText

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

# --- Content rotation + low-content alerting config ---
# Posting cadence, used only to convert "days of content left" to a post count.
POSTS_PER_WEEK = float(os.environ.get("POSTS_PER_WEEK", "3"))
POSTS_PER_DAY = POSTS_PER_WEEK / 7.0

# Send an email alert once remaining unposted content drops to this many
# days' worth (at the configured posting cadence).
LOW_CONTENT_ALERT_DAYS = float(os.environ.get("LOW_CONTENT_ALERT_DAYS", "2"))

ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USERNAME)

# Instagram's container status_code has been observed to report FINISHED
# almost instantly (sub-second) while media_publish still rejects the
# creation_id with "Media ID is not available" (code 9007 / 2207027) a
# moment later. This appears to be Meta-side eventual consistency between
# the status endpoint and the publish endpoint, not something client-side
# polling alone can detect. As a buffer, always wait a minimum amount of
# time after container creation before attempting to publish, regardless
# of how fast status_code reports FINISHED.
MIN_SECONDS_BEFORE_PUBLISH = 5

# If publish still fails with the transient "Media ID is not available"
# error after the status check passed, retry the publish call itself a
# few times with a short backoff -- this is a documented, sometimes
# purely Meta-side transient condition that commonly succeeds on retry.
PUBLISH_RETRY_ATTEMPTS = 4
PUBLISH_RETRY_BACKOFF_SECONDS = 5


def _redact_url(url, params):
    """Build the full request URL (query string included) with the access_token
    value masked, safe to write to logs."""
    safe_params = dict(params or {})
    if "access_token" in safe_params and safe_params["access_token"]:
        tok = safe_params["access_token"]
        safe_params["access_token"] = f"{tok[:8]}...{tok[-4:]}" if len(tok) > 12 else "***"
    query = "&".join(f"{k}={v}" for k, v in safe_params.items())
    return f"{url}?{query}" if query else url


def load_rotation_state():
    """Returns a dict with next_index (int) and alerted (list of alert names
    already sent, so we don't email the same alert every run)."""
    default = {"next_index": 0, "alerted": []}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                return {
                    "next_index": data.get("next_index", 0),
                    "alerted": data.get("alerted", []),
                }
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_rotation_state(idx, alerted):
    with open(STATE_FILE, "w") as f:
        json.dump(
            {"next_index": idx, "alerted": alerted, "updated_at": time.time()},
            f,
        )


def send_alert_email(subject, body):
    """Best-effort email alert via SMTP. Silently no-ops (with a log line) if
    ALERT_EMAIL_TO or SMTP credentials aren't configured, and never raises --
    a failed alert email should never break the posting run itself."""
    if not ALERT_EMAIL_TO:
        logger.info("send_alert_email skipped (ALERT_EMAIL_TO not set): %s", subject)
        return
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD):
        logger.warning(
            "send_alert_email skipped (SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD not "
            "fully configured): %s",
            subject,
        )
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM or SMTP_USERNAME
    msg["To"] = ALERT_EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(msg["From"], [ALERT_EMAIL_TO], msg.as_string())
        logger.info("Sent alert email to %s: %s", ALERT_EMAIL_TO, subject)
    except Exception:
        logger.exception("Failed to send alert email: %s", subject)


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

    Also enforces MIN_SECONDS_BEFORE_PUBLISH: status_code has been observed
    to report FINISHED in well under a second, but media_publish can still
    reject the same container moments later with the identical 9007 error --
    Meta's status endpoint and publish endpoint appear to become consistent
    on slightly different timelines. Waiting a small minimum amount of time
    regardless of how fast FINISHED shows up gives that a chance to settle.
    """
    url = f"{GRAPH_BASE}/{container_id}"
    params = {"fields": "status_code", "access_token": access_token}
    started_at = time.monotonic()

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
            elapsed = time.monotonic() - started_at
            remaining = MIN_SECONDS_BEFORE_PUBLISH - elapsed
            if remaining > 0:
                logger.info(
                    "status_code=FINISHED after %.2fs (suspiciously fast); "
                    "waiting %.2fs more before publish as a buffer",
                    elapsed, remaining,
                )
                time.sleep(remaining)
            return
        if status_code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container processing failed with status_code={status_code}: {resp.text}")

        # IN_PROGRESS or anything else not-yet-terminal: wait and retry.
        time.sleep(CONTAINER_POLL_INTERVAL_SECONDS)

    raise RuntimeError(
        f"container {container_id} did not finish processing after "
        f"{CONTAINER_POLL_MAX_ATTEMPTS * CONTAINER_POLL_INTERVAL_SECONDS}s"
    )


def _is_media_not_ready_error(resp):
    """True if the response body is Meta's transient 'Media ID is not
    available' / 'not ready for publishing' error (code 9007, subcode
    2207027). This is documented across multiple third-party integrations
    as sometimes purely Meta-side and transient -- retrying the publish
    call after a short delay commonly succeeds."""
    try:
        err = resp.json().get("error", {})
    except ValueError:
        return False
    return err.get("code") == 9007 or err.get("error_subcode") == 2207027


def publish_media_container(ig_user_id, access_token, container_id):
    url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    params = {"access_token": access_token}

    last_resp = None
    for attempt in range(1, PUBLISH_RETRY_ATTEMPTS + 1):
        logger.info(
            "POST publish_media_container (attempt %s/%s) -> %s",
            attempt, PUBLISH_RETRY_ATTEMPTS, _redact_url(url, params),
        )
        resp = requests.post(
            url,
            params=params,
            data={
                "creation_id": container_id,
            },
            timeout=60,
        )
        logger.info("publish_media_container response: %s %s", resp.status_code, resp.text)

        if resp.ok:
            return resp.json()["id"]

        last_resp = resp
        if _is_media_not_ready_error(resp) and attempt < PUBLISH_RETRY_ATTEMPTS:
            logger.info(
                "Transient 'Media ID is not available' error on attempt %s/%s; "
                "retrying in %ss",
                attempt, PUBLISH_RETRY_ATTEMPTS, PUBLISH_RETRY_BACKOFF_SECONDS,
            )
            time.sleep(PUBLISH_RETRY_BACKOFF_SECONDS)
            continue

        # Not the transient error, or out of retries: fail now.
        break

    raise RuntimeError(f"publish_media_container failed: {last_resp.status_code} {last_resp.text}")


@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "propreport-instagram-agent"})


@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(GENERATED_DIR, filename)


def _maybe_send_low_content_alert(state, remaining_after_this_post):
    """Fires the low-content email alert once when remaining posts drop to
    LOW_CONTENT_ALERT_DAYS worth (at POSTS_PER_WEEK cadence), and never again
    until the state file's 'alerted' list is reset (e.g. after adding more
    content and manually clearing rotation_state.json, or it naturally
    resets once you add posts and the count rises back above threshold is
    not tracked -- simplest mental model: it fires once per depletion cycle).
    """
    # Round up so "N days worth" always means at least enough posts to cover
    # that many days -- e.g. at 3 posts/week, 2 days worth is <1 post
    # mathematically, but the alert should still fire with 1 post left, not
    # never fire at all.
    threshold_posts = max(1, math.ceil(LOW_CONTENT_ALERT_DAYS * POSTS_PER_DAY))
    alerted = set(state.get("alerted", []))

    if remaining_after_this_post <= 0:
        return alerted  # handled separately as the "out of content" alert

    if remaining_after_this_post <= threshold_posts and "low_content" not in alerted:
        days_left = remaining_after_this_post / POSTS_PER_DAY if POSTS_PER_DAY > 0 else 0
        send_alert_email(
            subject="PropReport Instagram: running low on content",
            body=(
                f"Only {remaining_after_this_post} unposted post(s) left in "
                f"content_library.py -- about {days_left:.1f} day(s) worth at "
                f"{POSTS_PER_WEEK:g} posts/week.\n\n"
                "Add more entries to content_library.py before the queue runs "
                "out, otherwise posting will stop automatically once the last "
                "post is published."
            ),
        )
        alerted.add("low_content")

    return alerted


def _do_run():
    access_token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
    public_base_url = os.environ["PUBLIC_BASE_URL"].rstrip("/")

    state = load_rotation_state()
    idx = state["next_index"]

    if idx >= len(POSTS):
        # Rotation is exhausted -- do NOT loop back to post 1. Alert once per
        # depletion cycle instead of every single run.
        alerted = set(state.get("alerted", []))
        if "out_of_content" not in alerted:
            send_alert_email(
                subject="PropReport Instagram: out of content -- posting stopped",
                body=(
                    "All posts in content_library.py have been published. "
                    "No new posts will be published until you add more entries "
                    "and the app is redeployed.\n\n"
                    "Once you've added more content, reset rotation_state.json "
                    "(or delete it) if you want the new posts to start from the "
                    "top, or leave it as-is to continue appending new posts "
                    "after the existing ones."
                ),
            )
            alerted.add("out_of_content")
            save_rotation_state(idx, sorted(alerted))
        return {
            "posted": None,
            "out_of_content": True,
            "next_index": idx,
        }

    post = POSTS[idx]

    image_path = render_post(post, GENERATED_DIR)
    image_filename = os.path.basename(image_path)
    image_url = f"{public_base_url}/images/{image_filename}"
    logger.info("Publishing post id=%s using image_url=%s", post["id"], image_url)

    container_id = create_media_container(ig_user_id, access_token, image_url, post["caption"])
    wait_for_container_ready(container_id, access_token)
    media_id = publish_media_container(ig_user_id, access_token, container_id)

    new_idx = idx + 1
    remaining = len(POSTS) - new_idx
    alerted = _maybe_send_low_content_alert(state, remaining)
    save_rotation_state(new_idx, sorted(alerted))

    return {
        "posted": post["id"],
        "media_id": media_id,
        "image_url": image_url,
        "next_index": new_idx,
        "posts_remaining": remaining,
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


@app.route("/status")
def status():
    """Read-only view of rotation state: how many posts remain, whether
    alerts have fired, and current alerting config. Does not post anything.
    Protected by RUN_SECRET like /run.
    """
    expected_secret = os.environ.get("RUN_SECRET")
    provided_secret = request.args.get("secret") or request.headers.get("X-Run-Secret")
    if expected_secret and provided_secret != expected_secret:
        return jsonify({"error": "unauthorized"}), 401

    state = load_rotation_state()
    idx = state["next_index"]
    remaining = max(len(POSTS) - idx, 0)
    days_left = remaining / POSTS_PER_DAY if POSTS_PER_DAY > 0 else None

    return jsonify({
        "total_posts": len(POSTS),
        "next_index": idx,
        "posts_remaining": remaining,
        "days_remaining_estimate": round(days_left, 1) if days_left is not None else None,
        "posts_per_week": POSTS_PER_WEEK,
        "low_content_alert_days": LOW_CONTENT_ALERT_DAYS,
        "out_of_content": remaining == 0,
        "alerts_sent": state.get("alerted", []),
        "alert_email_configured": bool(ALERT_EMAIL_TO and SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
