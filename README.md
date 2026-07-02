# PropReport Instagram Posting Agent

Automatically posts Dan-Koe-style minimalist marketing graphics for
[propreport.com.au](https://propreport.com.au) to your Instagram Business
account, on a schedule, using Railway.

The app is a small Flask web service with two jobs:

1. Serve generated post images at a public URL (Instagram's API requires a
   public `image_url`, it can't accept a direct file upload).
2. Expose a `/run` endpoint that renders the next post in the rotation and
   publishes it to Instagram. Railway's Cron Schedule feature calls this
   endpoint on your chosen cadence (default: daily).

Posts are rendered at **1080x1350 (4:5 portrait)** — Instagram's current
recommended feed format. Earlier versions of this app used a 1:1 square
canvas, but Instagram's profile grid now crops all thumbnails to a 3:4 shape
regardless of upload ratio, which cut off the left/right edges of square
posts in the grid view. 4:5 only loses a small sliver off the top/bottom in
that grid crop instead of the sides.

The rotation advances automatically through `content_library.py` in order
and **does not loop back to the start** once it reaches the end — see
"Content rotation & running low on content" below. Add more posts any time
by editing that file.

---

## 1. Get your Instagram Graph API credentials

Meta's app dashboard now uses a **Use Cases** model (the old "Add Products" /
Graph API Explorer flow is deprecated for this purpose). This project is set
up for the **Instagram Business Login** flow, which does not require linking
a Facebook Page.

You need an Instagram **Business or Creator account** (Professional account).

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
   and create an app → select **Business** as the app type.
2. In your app dashboard, open **Use Cases** in the left sidebar and add/select
   **Instagram Business**.
3. Click **API setup with Instagram login**.
4. Under permissions, make sure these are enabled:
   `instagram_business_basic`, `instagram_business_content_publish`
   (add `instagram_business_manage_messages` / `instagram_business_manage_comments`
   only if you plan to use DMs/comments later — not required for posting).
5. Scroll to the **Generate access tokens** section on that same page and
   click **Add account**. Log in with the Instagram account for
   propreport.com.au and authorize the requested permissions.
6. Generate the token. It will start with `IGAA...` — this is an
   **Instagram User access token**, valid for **60 days**.
7. On the same page, note the **Instagram User ID** shown next to your
   connected account — this is the value to use for `IG_BUSINESS_ACCOUNT_ID`
   below (despite the variable name, it's your Instagram User ID from this
   flow, not a Facebook-Page-linked Business Account ID).
8. Copy the token **directly** from this page into Railway's variable —
   don't paste it through Notes, Slack, or any other app first. Some apps
   silently mangle long tokens (smart quotes, hidden line breaks, invisible
   characters), which causes an "Invalid OAuth access token — Cannot parse
   access token" error even though the value looks correct visually.

You'll end up with two values: `IG_ACCESS_TOKEN` (the `IGAA...` token) and
`IG_BUSINESS_ACCOUNT_ID` (the Instagram User ID from step 7).

**Important — API host:** tokens from this Instagram Business Login flow
(`IGAA...`) only work against the `graph.instagram.com` host, not
`graph.facebook.com`. This app defaults `GRAPH_HOST` to `graph.instagram.com`
already. If you instead generated an `EAA...` token via the older Facebook
Login for Business flow (Instagram linked through a Facebook Page), set the
Railway env var `GRAPH_HOST=graph.facebook.com` to match.

**Note:** long-lived tokens expire after ~60 days. Refresh with:
```
GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=<current long-lived token>
```
and update the Railway environment variable with the new token before day 60
(tokens not refreshed within 60 days of issue can no longer be refreshed and
must be regenerated from scratch).

---

## 2. Deploy to Railway

1. Push this folder to a new GitHub repository (or use Railway's
   "Deploy from local directory" via the Railway CLI if you don't want to
   use GitHub).
2. In [Railway](https://railway.app), create a **New Project** → **Deploy
   from GitHub repo** → select this repo.
3. Railway will detect the `Procfile` / `railway.json` and build it
   automatically (Nixpacks, Python).
4. Once deployed, Railway assigns a public domain
   (Settings → Networking → **Generate Domain**). Copy that URL, e.g.
   `https://propreport-instagram-production.up.railway.app`.

---

## 3. Set environment variables

In the Railway project → your service → **Variables**, add:

| Variable | Value |
|---|---|
| `IG_ACCESS_TOKEN` | the `IGAA...` long-lived token from step 1 |
| `IG_BUSINESS_ACCOUNT_ID` | the Instagram User ID from step 1 |
| `PUBLIC_BASE_URL` | the Railway domain from step 2 (no trailing slash) |
| `RUN_SECRET` | any random string you make up, e.g. `openssl rand -hex 16` |
| `GRAPH_HOST` | optional — only set if using an `EAA...` Facebook-Login token instead; value `graph.facebook.com`. Leave unset for `IGAA...` tokens (defaults to `graph.instagram.com`). |

Optional — low-content email alerts (see "Content rotation & running low on
content" below for full behavior):

| Variable | Value |
|---|---|
| `ALERT_EMAIL_TO` | your email address, e.g. `siddhartha.sachdev@gmail.com` |
| `SMTP_HOST` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | `587` (default if unset) |
| `SMTP_USERNAME` | your email address (for Gmail, the account you're sending from) |
| `SMTP_PASSWORD` | an **app password**, not your normal Gmail password — see below |
| `SMTP_FROM` | optional, defaults to `SMTP_USERNAME` |
| `POSTS_PER_WEEK` | how many times/week the cron posts, e.g. `7` (default — daily) |
| `LOW_CONTENT_ALERT_DAYS` | send the alert once this many days' worth of posts remain, e.g. `2` (default) |

**Using Gmail for SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD:** Gmail requires an
app password, not your regular password. In your Google Account go to
**Security → 2-Step Verification → App passwords**, generate one for "Mail",
and use that 16-character value as `SMTP_PASSWORD`. `SMTP_HOST` is
`smtp.gmail.com`, `SMTP_PORT` is `587`.

If you'd rather use a transactional email service (SendGrid, Postmark, etc.)
instead of Gmail, use that provider's SMTP host/username/password instead —
the app doesn't care which SMTP server you point it at.

If `ALERT_EMAIL_TO` is left unset, email alerts are simply skipped (logged
but not sent) — the app will still stop posting at the end of the rotation
either way, alerts are just for your awareness.

Redeploy after saving (Railway usually does this automatically).

---

## 4. Test it manually

Before posting for real, verify the token/ID are wired up correctly with the
diagnostic endpoint (does not post anything):

```
https://<your-railway-domain>/debug-token?secret=<your RUN_SECRET>
```

This calls `GET /{IG_BUSINESS_ACCOUNT_ID}?fields=username` against Graph API
using your env vars and returns the raw response, plus the token's length and
first/last few characters (never the full token) so you can sanity-check it
matches what you generated in Meta's dashboard. If this returns your
Instagram username, the credentials are good and any remaining error is in
the posting step itself, not auth.

Then test the real posting flow. Visit in your browser (or curl):

```
https://<your-railway-domain>/run?secret=<your RUN_SECRET>
```

If it works, you'll get a JSON response like:

```json
{"success": true, "posted": "p01", "media_id": "...", "image_url": "...", "next_index": 1}
```

And the post will appear on your Instagram account within a few seconds.
Check `/` for a basic health check any time.

**Note on `access_token` placement:** the app sends `access_token` as a query
parameter on every request (not as a POST body field). `graph.instagram.com`
has been observed to return `"Cannot parse access token"` for a perfectly
valid token when it's only included in the POST body on some endpoints/API
versions — sending it as a query param avoids that.

**Logs:** every outgoing request URL (with the token redacted) and the raw
Graph API response are logged via Python's `logging` module, viewable in
Railway's **Deployments → Logs** tab. Useful for debugging without exposing
your token.

---

## 5. Set up the recurring schedule (daily)

Railway has a built-in **Cron Schedule** feature for services:

1. In your Railway service → **Settings** → **Cron Schedule**.
2. Enable it and set a cron expression. For daily at 9am Melbourne time:
   ```
   0 23 * * *
   ```
   (23:00 UTC = 9am AEST, the UTC+10 offset Melbourne uses outside daylight
   saving, e.g. April–September. During AEDT/daylight saving, UTC+11—roughly
   October–April—use `0 22 * * *` instead so it still lands at 9am local
   time. Update the cron expression when daylight saving changes if you want
   the posting time to stay fixed at 9am local.)
3. Point the cron job at the `/run?secret=<RUN_SECRET>` endpoint. If Railway's
   cron feature runs a command rather than hitting a URL in your plan, use a
   tiny curl command as the cron command instead:
   ```
   curl -s "https://<your-railway-domain>/run?secret=<RUN_SECRET>"
   ```

If your Railway plan's Cron Schedule triggers a full redeploy/run of the
service rather than hitting an existing running service, an easy alternative
is any free external scheduler (e.g. [cron-job.org](https://cron-job.org)) set
to hit your `/run?secret=...` URL once a day — the app doesn't care who calls
it, only that the secret matches.

**Note on content runway at daily cadence:** with 12 posts in
`content_library.py` and daily posting, the full library lasts 12 days
before rotation stops (see "Content rotation & running low on content"
below). Add more posts well before then, or expect (and welcome) the
low-content email alert as your cue to top up the queue.

---

## Project structure

```
app.py               Flask app: image serving + /run publish endpoint
render.py             Draws the 1080x1350 (4:5) branded graphics
content_library.py    All post content (headline/caption/style) — edit to add more posts
fonts/                Inter font files used for rendering
generated/            Output images get written here at runtime
rotation_state.json   Tracks which post is next (auto-created/updated)
requirements.txt      Python dependencies
Procfile              Start command for Railway/gunicorn
railway.json          Railway build/deploy config
```

## Adding more content

Open `content_library.py` and append a new dict to the `POSTS` list. Three
supported styles:

- `dark_statement` / `light_statement` — a bold headline statement with an
  optional small tag label above it.
- `stat` — a large number/figure with a supporting line underneath.

Each entry needs a unique `id` and a `caption` (the Instagram caption text).

## Content rotation & running low on content

Posts are published in order (`p01`, `p02`, ... in whatever order they appear
in `POSTS`) and progress is tracked in `rotation_state.json` (auto-created on
Railway's persistent filesystem). Unlike earlier versions of this app,
**rotation does NOT loop back to the start** once it reaches the end.

- While posts remain: `/run` renders and publishes the next post as usual.
- When remaining posts drop to `LOW_CONTENT_ALERT_DAYS` worth (based on
  `POSTS_PER_WEEK`, default 2 days at 7 posts/week → alerts with 2 posts
  left): if `ALERT_EMAIL_TO` and the `SMTP_*` variables are set, you get one
  email warning you to add more content. It only fires once per depletion
  cycle, not on every run.
- When the last post has been published: `/run` stops posting and returns
  `{"success": true, "out_of_content": true, ...}` instead of an error. You
  also get a second, separate "out of content" email (if alerts are
  configured). Every subsequent `/run` call is a safe no-op until you add
  more content — it won't loop back to `p01` or throw errors.
- Check `GET /status?secret=<RUN_SECRET>` any time to see posts remaining,
  an estimated days-remaining figure, and which alerts have already fired —
  without posting anything.

**To resume after running out:** add new entries to `content_library.py` and
redeploy. New posts are appended after the existing ones by index, so
rotation picks up right where it left off (post 13, 14, ...) — you don't
need to touch `rotation_state.json`. If you'd instead like to restart from
the top of the (now-updated) list, delete `rotation_state.json` before or
after redeploying so `next_index` resets to 0.

## Security notes

- Never commit `IG_ACCESS_TOKEN` or `RUN_SECRET` to the repo — they're
  Railway environment variables only.
- The `/run` endpoint is protected by `RUN_SECRET`. Keep it private.
- Long-lived Instagram tokens expire ~60 days after issue — set a reminder to
  refresh it.

## Troubleshooting: "Media ID is not available" (code 9007)

If `/run` fails with an error like:

```
publish_media_container failed: 400 {"error":{"message":"Media ID is not
available","code":9007,"error_subcode":2207027,...}}
```

this means Instagram's container-status endpoint reported the media as
`FINISHED`, but the publish endpoint still wasn't ready for it. Two things
address this:

1. **Images are now rendered as JPEG, not PNG.** Meta's content-publishing
   API has documented reliability issues with PNG uploads that manifest as
   exactly this error, even when the container reports `FINISHED`. `render.py`
   now saves `.jpg` files and `app.py` builds image URLs accordingly — no
   action needed, this is already applied.
2. **A minimum wait + automatic retry around publish.** `status_code` can
   report `FINISHED` in under a second while the publish endpoint is still
   catching up (an eventual-consistency gap on Meta's side). The app now:
   - Waits at least `MIN_SECONDS_BEFORE_PUBLISH` (default 5s) after container
     creation before calling publish, even if `FINISHED` shows up instantly.
   - If publish still returns the 9007/2207027 error, retries the publish
     call up to `PUBLISH_RETRY_ATTEMPTS` times (default 4) with a
     `PUBLISH_RETRY_BACKOFF_SECONDS` delay (default 5s) between attempts.
   - Any other error type fails immediately without retrying.

If you still see this error after all retries are exhausted, it's most
likely a temporary Meta-side platform issue (this exact error has been
reported as a Meta-side outage affecting multiple third-party apps at once) —
simply trigger `/run` again in a few minutes.
