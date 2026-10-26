# PropReport Instagram Agent — Feature Map

This document is the fast orientation guide for future changes. It describes
the behavior implemented by the current code, where each feature lives, and
the operational assumptions that are easy to miss.

## System at a glance

```text
Scheduler or operator
        |
        | GET/POST /run + RUN_SECRET
        v
Flask app (app.py)
        |
        +--> read next_index from rotation_state.json
        +--> select the next entry from content_library.py
        +--> render JPEG through render.py and bundled Inter fonts
        +--> expose JPEG at /images/<post-id>.jpg
        +--> create and poll an Instagram media container
        +--> publish the container
        +--> advance rotation_state.json
        +--> optionally send low-content email through SMTP
```

The service is deployed as a Gunicorn-backed Flask application. Railway or an
external scheduler is expected to invoke `/run`; there is no in-process
scheduler.

## Feature ownership

| Feature | Entry point or data | Implementation | Notes |
|---|---|---|---|
| Health check | `GET /` | `app.py:health` | Public, returns service name and `ok`. |
| Trigger a post | `GET` or `POST /run` | `app.py:run`, `_do_run` | Accepts `secret` query parameter or `X-Run-Secret` header. |
| Serve rendered media | `GET /images/<filename>` | `app.py:serve_image` | Public by design so Meta can fetch the image. |
| Check credentials | `GET /debug-token` | `app.py:debug_token` | Calls Graph API without publishing or changing rotation state. |
| Inspect queue | `GET /status` | `app.py:status` | Reports remaining posts, estimated runway, and alert flags. |
| Content queue | `POSTS` | `content_library.py` | Ordered list; the list index is the queue position. Current library: 24 posts. |
| Card rendering | `render_post` | `render.py` | Produces 1080×1350 RGB JPEGs in `generated/`. |
| Dark/light statement cards | `dark_statement`, `light_statement` | `render.py:render_statement` | Optional tag plus wrapped headline and brand footer. |
| Statistic cards | `stat` | `render.py:render_stat` | Large number, supporting line, configurable light/dark background. |
| Rotation persistence | `rotation_state.json` | `load_rotation_state`, `save_rotation_state` | Atomic state file on the attached Railway Volume or configured `STATE_DIR`. |
| Low-content alerts | SMTP environment variables | `_maybe_send_low_content_alert`, `send_alert_email` | Threshold derives from posts per week and alert days. |
| Meta publishing | Instagram Graph API | `create_media_container`, `wait_for_container_ready`, `publish_media_container` | Polls processing state and retries Meta error 9007/2207027. |
| Deployment | `railway.json`, `Procfile` | Gunicorn | Both currently specify 2 workers, 4 threads, and a 120-second timeout. |

## Posting lifecycle

1. `/run` compares the supplied secret with `RUN_SECRET`. A missing server-side
   secret returns HTTP 503; an incorrect client secret returns HTTP 401.
2. `_do_run` verifies persistent storage on Railway, takes the cross-process
   rotation lock, loads `rotation_state.json`, and selects a post by `next_index`.
3. If the index is past the end of `POSTS`, it records the out-of-content alert
   and returns a successful no-op response.
4. `render_post` writes `generated/<id>.jpg`.
5. The public image URL is formed from `PUBLIC_BASE_URL` and passed to Meta with
   the post caption.
6. The service polls the media container until it is `FINISHED`. It enforces a
   minimum five-second delay before publishing.
7. Publishing retries up to four times for the known transient “media ID not
   available” response.
8. Only after Meta returns a media ID does the app increment `next_index`,
   evaluate low-content alerting, and atomically replace the state file.

This ordering prevents a normal API failure from advancing the queue. It does
not provide idempotency if the publish succeeds but the process dies before
the state file is saved.

## Content contract

Every post requires:

- a unique `id`, used as the image filename and returned in API responses;
- a supported `style`;
- a `caption` sent to Instagram.

Statement posts also require `headline` and may supply `tag`. Statistic posts
require `big_number` and `sub_line`, and may supply `dark_bg` (defaults to
`True`). The renderer raises `ValueError` for unknown styles. There is no
startup schema validation, so missing fields fail only when that post reaches
the front of the queue.

The queue is position-based. Append new posts to preserve progress. Reordering,
inserting, or deleting earlier entries while retaining an existing
`next_index` can skip or repeat content.

`CONTENT_VERSION` identifies a complete series. Changing it intentionally
resets a state file from another series to index 0 with empty alert flags. Do
not change it when merely appending posts.

### Editorial direction

- Keep `PROPREPORT` as the Instagram identity, without a website address,
  product pitch, engagement request or promotional call to action.
- Give the reader a usable checklist, calculation, question, or research step
  in every caption.
- Write for Australian buyers and name Australian concepts such as strata,
  council planning controls, bushfire risk and conveyancing where relevant.
- Prefer official maps, government guidance and address-specific checks over
  broad market rules.
- Avoid universal price predictions and unsupported fixed percentages. If a
  post uses current rates or market statistics, record the source and review
  date and expect to update it.
- Account for state differences by directing readers to their relevant state,
  council, lender, insurer or legal professional rather than presenting one
  jurisdiction's process as national.

## State and alert semantics

`rotation_state.json` has this shape:

```json
{
  "next_index": 7,
  "alerted": ["low_content"],
  "content_version": "australian_buyer_education_v1_2026_10",
  "updated_at": 1730000000.0
}
```

The low-content threshold is:

```text
max(1, ceil(LOW_CONTENT_ALERT_DAYS * POSTS_PER_WEEK / 7))
```

The low-content check runs after a successful publish. The out-of-content
email runs on the next `/run` call after the final post, because the successful
final-post path does not send it. Alert names are recorded even if email is
disabled or SMTP delivery fails; `alerts_sent` therefore means “attempted or
handled,” not confirmed delivery.

## Configuration

Required for publishing:

| Variable | Purpose |
|---|---|
| `IG_ACCESS_TOKEN` | Instagram/Facebook access token. |
| `IG_BUSINESS_ACCOUNT_ID` | Instagram user/account ID used by publishing endpoints. |
| `PUBLIC_BASE_URL` | Public service origin used to build Meta-fetchable image URLs. |
| `RUN_SECRET` | Shared secret required by trigger and diagnostic endpoints. |

Optional:

| Variable | Default | Purpose |
|---|---:|---|
| `GRAPH_HOST` | `graph.instagram.com` | Selects the API host for the token type. |
| `STATE_DIR` | project directory locally | Persistent state directory on non-Railway hosts. Railway uses `RAILWAY_VOLUME_MOUNT_PATH` automatically. |
| `POSTS_PER_WEEK` | `7` | Converts remaining posts into estimated days. |
| `LOW_CONTENT_ALERT_DAYS` | `2` | Selects the low-content threshold. |
| `ALERT_EMAIL_TO` | empty | Enables email alerts when SMTP is also configured. |
| `SMTP_HOST` | empty | SMTP server. |
| `SMTP_PORT` | `587` | SMTP STARTTLS port. |
| `SMTP_USERNAME` | empty | SMTP login. |
| `SMTP_PASSWORD` | empty | SMTP password or app password. |
| `SMTP_FROM` | `SMTP_USERNAME` | Message sender. |
| `PORT` | `8080` locally | Flask development-server port; Railway supplies it. |

Most configuration is read when `app.py` is imported. Tests or tools that
change environment variables after import must reload the module or patch its
module-level values.

## External boundaries

- Instagram Graph API: create media, query container status, and publish.
- Public HTTP: Meta fetches generated JPEGs from this service.
- SMTP: optional STARTTLS email delivery.
- Local filesystem: generated images and queue state.
- Railway: process hosting and external scheduling configuration.

No database, object storage, task queue, webhook receiver, or token refresh job
is implemented.

## Known risks and maintenance traps

1. **Publishing has an acknowledgement gap.** If Instagram publishes the post
   and the process stops before saving the new index, the next run can publish
   it again.
2. **Secrets in query strings can leak.** The header option is safer for
   schedulers because URLs commonly appear in access logs and browser history.
## Implemented safety controls

- Protected endpoints fail closed when `RUN_SECRET` is missing and compare
  supplied secrets with `hmac.compare_digest`.
- A thread lock plus an operating-system file lock serializes the complete
  read, publish, and state-update lifecycle across Gunicorn threads and workers.
- State is written to a temporary file, flushed, synced, and atomically moved
  into place. Invalid or corrupt state stops execution instead of resetting the
  queue.
- Railway publishing is refused unless `RAILWAY_VOLUME_MOUNT_PATH` confirms an
  attached persistent Volume.

## Safe extension points

- Add a post: append to `POSTS`, keep the ID unique, render it locally, and
  inspect the resulting card for overflow.
- Add a visual style: implement a renderer, add a branch in `render_post`, and
  document the new content fields here.
- Change Meta API behavior: keep token redaction, request timeouts, terminal
  container-state handling, and publish-after-success state advancement.
- Replace local state: preserve `next_index` and alert semantics or migrate to a
  post-ID-based record with an idempotency strategy.
- Keep endpoint protection centralized through `_authorization_error` so
  `/run`, `/status`, and `/debug-token` cannot drift apart.

## Review and validation baseline

As of 2026-10-26:

- Python compilation succeeds for `app.py`, `render.py`, `content_library.py`,
  `test_app.py`, and `test_content_library.py`.
- All 24 post IDs are unique.
- The library contains 8 dark statements, 8 light statements, and 8 statistic
  cards.
- All 24 entries render successfully as 1080×1350 RGB JPEGs.
- Six automated safety tests cover fail-closed authentication, corrupt-state
  handling, atomic writes, Railway volume enforcement, and concurrent runs.
- Three content tests enforce unique IDs, supported schemas, the retired
  website-callout rule, and the absence of common promotional CTAs.
- One rotation test verifies that a new `CONTENT_VERSION` restarts a retired
  series at its first post.
