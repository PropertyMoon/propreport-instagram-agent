# PropReport Instagram Posting Agent

Automatically posts Dan-Koe-style minimalist marketing graphics for
[propreport.com.au](https://propreport.com.au) to your Instagram Business
account, on a schedule, using Railway.

The app is a small Flask web service with two jobs:

1. Serve generated post images at a public URL (Instagram's API requires a
   public `image_url`, it can't accept a direct file upload).
2. Expose a `/run` endpoint that renders the next post in the rotation and
   publishes it to Instagram. Railway's Cron Schedule feature calls this
   endpoint on your chosen cadence (e.g. Mon/Wed/Fri).

The rotation advances automatically and loops back to the start once it
reaches the end of `content_library.py` — so you never need to manually pick
what to post next. Add more posts any time by editing that file.

---

## 1. Get your Instagram Graph API credentials

You need an Instagram **Business or Creator account** linked to a Facebook
Page.

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
   and create an app (type: "Other" → "Business").
2. Add the **Instagram Graph API** product to the app.
3. Make sure your Facebook Page (linked to your Instagram account) is added
   as an asset of the app.
4. Use the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   to generate a **User Access Token** with these permissions:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`.
5. Exchange the short-lived token for a **long-lived token** (valid ~60 days,
   renewable) — see
   [Meta's long-lived token docs](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/postman/access-tokens#long-lived-user-access-tokens).
6. Get your **Instagram Business Account ID**:
   - `GET /me/accounts` → get your Facebook Page ID
   - `GET /{page-id}?fields=instagram_business_account` → get the Instagram
     Business Account ID

You'll end up with two values: `IG_ACCESS_TOKEN` and
`IG_BUSINESS_ACCOUNT_ID`.

**Note:** long-lived tokens expire after ~60 days. You'll need to refresh it
periodically (Meta allows refreshing before expiry via
`GET /refresh_access_token`) and update the Railway environment variable.

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
| `IG_ACCESS_TOKEN` | the long-lived token from step 1 |
| `IG_BUSINESS_ACCOUNT_ID` | the numeric ID from step 1 |
| `PUBLIC_BASE_URL` | the Railway domain from step 2 (no trailing slash) |
| `RUN_SECRET` | any random string you make up, e.g. `openssl rand -hex 16` |

Redeploy after saving (Railway usually does this automatically).

---

## 4. Test it manually

Visit in your browser (or curl):

```
https://<your-railway-domain>/run?secret=<your RUN_SECRET>
```

If it works, you'll get a JSON response like:

```json
{"success": true, "posted": "p01", "media_id": "...", "image_url": "...", "next_index": 1}
```

And the post will appear on your Instagram account within a few seconds.
Check `/` for a basic health check any time.

---

## 5. Set up the recurring schedule (3x/week)

Railway has a built-in **Cron Schedule** feature for services:

1. In your Railway service → **Settings** → **Cron Schedule**.
2. Enable it and set a cron expression. For Mon/Wed/Fri at 9am AEST
   (Melbourne, UTC+10 / UTC+11 during DST — adjust for daylight saving):
   ```
   0 22 * * 0,2,4
   ```
   (22:00 UTC Sun/Tue/Thu = ~9am Mon/Wed/Fri AEDT — double check the current
   UTC offset for Melbourne when daylight saving changes, and adjust the hour
   accordingly.)
3. Point the cron job at the `/run?secret=<RUN_SECRET>` endpoint. If Railway's
   cron feature runs a command rather than hitting a URL in your plan, use a
   tiny curl command as the cron command instead:
   ```
   curl -s "https://<your-railway-domain>/run?secret=<RUN_SECRET>"
   ```

If your Railway plan's Cron Schedule triggers a full redeploy/run of the
service rather than hitting an existing running service, an easy alternative
is any free external scheduler (e.g. [cron-job.org](https://cron-job.org)) set
to hit your `/run?secret=...` URL 3x/week — the app doesn't care who calls it,
only that the secret matches.

---

## Project structure

```
app.py               Flask app: image serving + /run publish endpoint
render.py             Draws the 1080x1080 branded graphics
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

## Security notes

- Never commit `IG_ACCESS_TOKEN` or `RUN_SECRET` to the repo — they're
  Railway environment variables only.
- The `/run` endpoint is protected by `RUN_SECRET`. Keep it private.
- Long-lived Instagram tokens expire ~60 days after issue — set a reminder to
  refresh it.
