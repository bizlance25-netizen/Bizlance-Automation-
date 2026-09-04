# Bizlance Automation — Claude Code + Python + GitHub Actions

One repo, scheduled jobs covering content, social, blog, and outreach:

| Job | Schedule | What it does | File |
|---|---|---|---|
| Blog | daily 9 AM UTC | Writes + publishes an SEO blog post to Blogger, alternating Buyer/Provider audience | `scripts/post_blog.py` |
| Social — Buyer slot | daily ~11:30 AM UTC | 1 Buyer-facing feed post + 1 story, IG + Facebook | `scripts/post_social.py` |
| Social — Provider slot | daily ~6:00 PM UTC | 1 Provider-facing feed post + 1 story, IG + Facebook | `scripts/post_social.py` |
| Threads | daily, with the morning slot | 1 text post, alternating Buyer/Provider | `scripts/post_threads.py` |
| X draft | daily 10 AM UTC | Drafts an X/Twitter post — NOT auto-posted (X has no free posting tier) | `scripts/generate_x_post.py` |
| Daily report | daily 10 AM UTC | Assembles pipeline activity + real marketplace metrics, if connected | `scripts/daily_report.py`, `scripts/fetch_marketplace_metrics.py` |
| DM drafts | daily 10 AM UTC | Drafts reply suggestions for inbound IG comments (human sends them) | `scripts/dm_draft_replies.py` |
| Outreach | weekdays 8 AM UTC | Emails up to 30 provider + 30 buyer business leads from your Google Sheet | `scripts/send_outreach.py` |
| Newsletter | weekly, Monday | Drafts a newsletter for manual review/send | `scripts/generate_newsletter.py` |
| Carousel | weekly, Monday | Generates 5 branded slide images for LinkedIn/Instagram | `scripts/generate_carousel.py` |
| Partnerships | weekly, Monday | Emails up to 10 partnership targets from your seed list | `scripts/partnership_outreach.py` |

That's **2 posts + 2 stories/day** (one Buyer-facing pair, one Provider-facing pair — both sides of the marketplace get covered daily), plus the blog, outreach, and weekly extras.

**Stack:** GitHub (hosting + free CI scheduler via Actions) · Python · Pollinations.ai (free, for text/captions) · **OpenAI Images API (paid — see cost note below)** for post/story visuals · imgbb (free image hosting, needed because OpenAI returns raw image bytes, not a hotlink URL like Pollinations did) · Blogger API (free) · Meta Graph API (free, needs App Review) · Google Sheets (free, as your lead database) · Brevo (free, 300 emails/day).

**Cost note — this is no longer a $0/month system:** the OpenAI Images API is pay-per-image, not free. Rough math: 4 images/day (2 posts + 2 stories) × 30 days ≈ 120 images/month — check current OpenAI image pricing at openai.com/api/pricing before budgeting, since it changes. If you want to go back to fully free, swap `generate_image_openai()` back to the original `generate_image_url()` (Pollinations) in `post_social.py` — one function call to change.

**No video in this version** — dropped by request to keep the system reliably shippable rather than half-working. The blog/social/email pipeline below is fully built and tested (syntax-verified); video can be added later as its own module if you want it back.

**Claude Code's role:** this repo is meant to be opened and extended with Claude Code (`claude` in your terminal, inside this folder) — ask it to add a new content theme, debug a failing Action run from the logs, add a new platform, tighten the email copy, etc. Everything here is plain, readable Python on purpose so Claude Code (or you) can safely modify any piece.


---

## 1. Create the repo

```bash
git init bizlance-automation
cd bizlance-automation
# copy in the scripts/, .github/, requirements.txt, README.md from this delivery
git add .
git commit -m "Initial Bizlance automation pipeline"
gh repo create bizlance-automation --private --source=. --push
# (or create the repo on github.com and `git remote add origin ...` + `git push`)
```

A **private** repo is fine — GitHub Actions still gives you 2,000 free minutes/month on private repos, and these jobs take seconds each, so you won't come close to that limit.

## 2. Add your secrets

GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**. Add each of these (leave out any pipeline piece you're not using yet):

**Blog (Blogger API)**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — from Google Cloud Console (same OAuth client used before)
- `GOOGLE_REFRESH_TOKEN` — obtained once via OAuth consent, then reused headlessly forever (see note below)
- `BLOGGER_BLOG_ID` — your numeric blog ID

**Social (Meta Graph API — requires App Review approval first)**
- `META_PAGE_ACCESS_TOKEN` — long-lived Page access token
- `META_IG_BUSINESS_ID`, `META_PAGE_ID`
- `OPENAI_API_KEY` — from platform.openai.com, used for post/story images (paid — see cost note above)
- `IMGBB_API_KEY` — free, sign up at api.imgbb.com to get one; used to host the generated images at a public URL Instagram/Facebook can fetch

**Threads (separate App Review from Instagram/Facebook — different permissions: `threads_basic`, `threads_content_publish`)**
- `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID` — from developers.facebook.com's Threads API product, once approved

**X (Twitter) — intentionally NOT auto-posting**
X's API has no free tier for posting (pay-per-use since Feb 2026, roughly $0.015/post — cheap, but not free). Since this system defaults to free wherever possible, X stays draft-only: `generate_x_post.py` writes the post text to `x_post_drafts.jsonl` for you to copy-paste manually, no secret/cost required. If you decide the small per-post cost is worth automating later, say so and I'll wire in real posting via X API v2.

**Outreach (Google Sheets + Brevo)**
- `GOOGLE_SERVICE_ACCOUNT_JSON` — full JSON key of a Google Service Account with access to your Leads sheet (share the sheet with the service account's email)
- `LEADS_SHEET_ID`, `BREVO_API_KEY`, `SENDER_EMAIL`

**Optional, all pipelines**
- `POLLINATIONS_KEY` — free key from enter.pollinations.ai, improves reliability over the keyless tier

> **Getting `GOOGLE_REFRESH_TOKEN` (one-time, manual):** this is the one step that can't run headlessly the first time, since it needs you to click "Allow" once. Easiest path: run Google's OAuth Playground (developers.google.com/oauthplayground), plug in your client ID/secret under the gear icon, authorize the Blogger scope with your account, and copy the refresh token it gives you. That token then works forever in the Action without you touching a browser again (unless you revoke it).

## 3. Set up the Leads sheet

Google Sheet, tab named `Leads`, header row:
```
company_name | contact_name | email | industry | website | segment | status | last_sent_date
```
`segment` must be exactly `provider` or `buyer` per row — this is what splits your 30/30 daily cap and picks the right pitch. Share the sheet with your service account's email (found inside the JSON key as `client_email`) with Editor access. Populate leads using free tools (Hunter/Apollo free tiers, company contact pages) — see the outreach notes below for sourcing tips.

**For partnerships:** a second sheet, tab named `Partnerships`, header row:
```
org_name | contact_name | email | org_type | website | status | last_sent_date
```
Same sharing step. This is a seed list you curate (AI communities, newsletters, accelerators you've found) — no free API discovers these automatically, so this one stays manually sourced by design.

## 4. Test each job manually before trusting the schedule

Repo → **Actions** tab → pick a workflow → **Run workflow** (this is what `workflow_dispatch` in each YAML enables). Watch the logs. Fix any secret typos. Only once a manual run succeeds does the daily cron matter.

## 5. Turn scripts on/off independently

Don't want social posting live yet (still waiting on Meta App Review)? Just don't add the `META_*` secrets — that job will fail gracefully (`continue-on-error: true`) without blocking the DM-draft step or breaking anything else. Same logic applies to any piece you want to stage in later.

---

## Connecting real marketplace data (optional, unlocks real reporting)

Everything above tracks what the *pipeline* does (posts published, emails sent). It cannot tell you how Bizlance the marketplace is actually doing — providers, buyers, matches, projects, reviews — because nothing here has ever been connected to Bizlance's actual product database. If you want that:
1. Expose one authenticated JSON endpoint on your backend returning the metrics listed in `scripts/fetch_marketplace_metrics.py`'s docstring, OR
2. Give Claude Code your database schema and connection details and ask it to wire a direct query into that same file.

Until one of those exists, the daily report will honestly say "not connected" in that section rather than guess.

## X (Twitter) posting

`generate_x_post.py` only drafts — X's API has required a paid tier for posting since 2023. Check current pricing at developer.x.com if you want to add real auto-posting later; it's a small addition once you have the key.

## Notes on each piece

- **Blog & Social content quality**: both use Pollinations' free text model. It's decent, not GPT/Claude-level. Swap the `generate_text_json()` calls in `common.py` for a paid Anthropic/OpenAI call if quality matters more than $0 — every script already funnels through that one shared function, so it's a one-file change.
- **Social posting will fail until Meta App Review is approved** — that's expected, not a bug. The workflow is written to keep running the DM-draft step regardless.
- **DMs are draft-only, on purpose** — see the comment block at the top of `dm_draft_replies.py`. Automated bulk outbound DMs risk the Instagram account getting disabled.
- **Outreach compliance**: every email includes a real unsubscribe path and Bizlance's physical address (edit the placeholder address in `send_outreach.py` if it changes) — required under CAN-SPAM/GDPR, not optional.
- **Lead sourcing stays semi-manual**: no free API sustains 30 fresh business leads/day forever. Batch-source ~100-150 leads every couple weeks (Hunter/Apollo free tiers, company contact pages) into the sheet; the script paces itself at 30/day so you don't run dry mid-week.
