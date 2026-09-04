# Deploying Bizlance Automation — A Guide for Total Beginners

If you've never used GitHub, a terminal, or an API key before, this is written for you.
Every step explains WHAT you're doing and WHY, not just the click-path.

---

## Part 0 — What you're actually building, in plain English

You have a folder of Python files (little programs). Each one does one job: "write a
blog post," "post to Instagram," "send an email." Right now they just sit on your
computer, doing nothing — they need somewhere to *live* that runs them automatically,
every day, forever, without your laptop needing to be on.

That "somewhere" is **GitHub Actions** — a free feature of GitHub (a website for
storing code) that can run your Python files on a schedule, in the cloud, automatically.

So the whole deployment is really just 3 kinds of steps, repeated:
1. Put the code on GitHub (once)
2. Get "keys" (passwords, basically) from each service you're using (Google, Brevo,
   OpenAI, etc.) and give them to GitHub so your scripts can use them
3. Tell GitHub to actually run things on schedule (flip one switch)

That's it. Nothing here requires you to know how to code.

---

## Part 1 — Install what you need

**1. A GitHub account**
Go to github.com → Sign up → free account, just needs an email.

**2. Windows/Mac: GitHub Desktop** (skip this if you're on Android)
Go to desktop.github.com → download → install → sign in with the GitHub account you
just made. This avoids the terminal entirely.

**Android: nothing to install yet** — Part 2B below covers the Android-specific tool
(Termux) as part of that walkthrough.

That's genuinely all you need. No coding knowledge required for either path.

---

## Part 2 — Get the code onto GitHub

**Which path applies to you:** if you're on Windows or Mac, use Part 2A below
(GitHub Desktop, no terminal). If you're on Android with no computer, skip to
Part 2B — GitHub Desktop doesn't exist for Android, so that path uses a terminal
app instead (it's genuinely not hard, just different).

### Part 2A — Windows/Mac, using GitHub Desktop

1. Unzip `bizlance-automation.zip` on your computer — you should see a folder called
   `bizlance-automation` with files like `README.md`, a `scripts` folder, etc.
2. Open **GitHub Desktop**.
3. Click **File → Add Local Repository**.
4. Browse to and select the `bizlance-automation` folder you unzipped.
5. It will say "This directory does not appear to be a Git repository" — click
   **"create a repository"** right there in that message.
6. Click **Publish repository** (top of the window). Uncheck "Keep this code private"
   only if you're fine with it being public — private is safer, keep it checked.
7. Click **Publish**.

Done — your code is now on GitHub. You'll see it at
`github.com/YOUR-USERNAME/bizlance-automation`.

**Whenever a file changes later:** GitHub Desktop will show the changed files on
the left, you type a one-line summary at the bottom, click **Commit**, then click
**Push origin** at the top. That's the entire "save my changes to the cloud"
workflow, forever.

### Part 2B — Android only, using Termux (a terminal app)

GitHub Desktop only exists for Windows/Mac. On Android, the equivalent tool is a
terminal app called **Termux** — it sounds more technical than it is; you're just
typing short commands one line at a time.

1. **Install Termux** from F-Droid.org (search "Termux," install the app) — not the
   Play Store version, which is outdated and often broken. Also install **ZArchiver**
   (free, Play Store) if your Files app can't unzip on its own.
2. Unzip `bizlance-automation.zip` using your Files app or ZArchiver — it'll land in
   your Downloads folder.
3. Open Termux and type each of these, pressing Enter after each one:
   ```
   pkg update
   pkg install git unzip -y
   termux-setup-storage
   ```
   The last command pops up an Android permission request — tap **Allow**.
4. Move into the unzipped folder:
   ```
   cd ~/storage/downloads/bizlance-automation
   ```
5. **Create the empty repo on GitHub first**, from your phone's browser (easier than
   Termux for this step): go to github.com → tap **+ → New repository** → name it
   `bizlance-automation` → keep it **Private** → do NOT check "Add a README" → **Create
   repository**.
6. **Get a Personal Access Token** (this is what lets Termux "log in" to push code —
   GitHub no longer accepts your actual password for this): github.com → tap your
   profile picture → **Settings → Developer settings → Personal access tokens →
   Tokens (classic) → Generate new token** → check the **repo** checkbox → **Generate
   token** → **copy it immediately** — you cannot view it again after leaving the page.
7. Back in Termux, push the code:
   ```
   git init
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/bizlance-automation.git
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```
   Replace `YOUR-USERNAME` with your actual GitHub username in that remote add line.
   When it asks for a username, type your GitHub username. When it asks for a
   password, **paste the token from step 6** instead.

Done — same result as Part 2A, just via command line instead of clicking buttons.

**Whenever a file changes later:** reopen Termux, `cd` back into the folder (step 4),
then run:
```
git add .
git commit -m "update"
git push
```
That's the entire "save my changes to the cloud" workflow on Android, forever.


---

## Part 3 — Understanding "secrets" (this is the only slightly fiddly part)

Your scripts need passwords to work — a password for Google, a password for the
email service, etc. You never put passwords directly in your code (anyone could see
them). Instead, GitHub has a vault called **Secrets** where you paste each password
once, and your code says "go get the password named X from the vault" instead of
containing it directly.

**Where the vault is:** on your repo's GitHub page → **Settings** tab → left sidebar
**Secrets and variables → Actions** → green button **New repository secret**.

You'll repeat this "paste a name, paste a value, save" action once for every item
below. Let's go get each password.

---

## Part 4 — Getting each key, one at a time

Do these in order. Skip any section for a feature you're not using yet (e.g. skip
Meta/social until you've done App Review) — the system is built so missing pieces
just quietly skip that one feature instead of breaking everything else.

### 4a. Blog posting (Blogger)

1. Go to console.cloud.google.com → sign in with the Google account that owns your
   Blogger blog.
2. Top left, click the project dropdown → **New Project** → name it "bizlance" → Create.
3. Left menu → **APIs & Services → Library** → search "Blogger API v3" → click it →
   **Enable**.
4. Left menu → **APIs & Services → OAuth consent screen** → choose **External** →
   fill in just the required fields (app name "Bizlance", your email) → Save through
   the steps → on "Test users" add your own Google email.
5. Left menu → **APIs & Services → Credentials** → **+ Create Credentials → OAuth
   client ID** → Application type: **Web application** → under "Authorized redirect
   URIs" add: `https://developers.google.com/oauthplayground` → Create.
6. A popup shows a **Client ID** and **Client Secret** — copy both somewhere safe.
7. Go to **developers.google.com/oauthplayground** → click the gear icon (top right)
   → check "Use your own OAuth credentials" → paste in the Client ID and Secret from
   step 6.
8. On the left, find and expand "Blogger API v3" → check the scope box → click
   **Authorize APIs** → sign in with your Google account → Allow.
9. Click **Exchange authorization code for tokens** → you'll now see a
   **Refresh token** — copy it.
10. Find your Blog ID: go to your Blogger dashboard, look at the URL of your blog's
    settings page — it contains a long number, that's your Blog ID.

**Now add these 4 secrets to GitHub** (Part 3's vault):
- `GOOGLE_CLIENT_ID` = the Client ID from step 6
- `GOOGLE_CLIENT_SECRET` = the Client Secret from step 6
- `GOOGLE_REFRESH_TOKEN` = the refresh token from step 9
- `BLOGGER_BLOG_ID` = the number from step 10

### 4b. Cold email sending (Brevo)

1. Go to brevo.com → sign up free.
2. Left menu → **Settings (gear icon) → SMTP & API → API Keys tab** → **Generate a
   new API key** → copy it.
3. Left menu → **Senders & IP → Senders** → **Add a sender** → enter the email
   address you'll send from → verify it (click the link Brevo emails you).

**Add these secrets:**
- `BREVO_API_KEY` = the key from step 2
- `SENDER_EMAIL` = the email you verified in step 3

### 4c. Lead spreadsheet (Google Sheets)

1. Make a Google Sheet. Rename the tab (bottom) to exactly `Leads`. Row 1 (headers),
   typed exactly:
   `company_name | contact_name | email | industry | website | segment | status | last_sent_date`
   (each in its own column A, B, C, D, E, F, G, H)
2. In the same Google Cloud project from step 4a: **APIs & Services → Library** →
   search "Google Sheets API" → **Enable**.
3. **APIs & Services → Credentials** → **+ Create Credentials → Service account** →
   give it any name → Create and continue → Done.
4. Click the service account you just made → **Keys tab** → **Add Key → Create new
   key → JSON** → a file downloads. Open it in a text editor, copy the entire contents.
5. Inside that JSON file, find the line `"client_email": "..."` — copy that email
   address.
6. Go back to your Google Sheet → **Share** button → paste that service account
   email in → give it **Editor** access → Share.
7. Copy your Sheet's ID: it's the long string in the sheet's URL between `/d/` and
   `/edit`.

**Add these secrets:**
- `GOOGLE_SERVICE_ACCOUNT_JSON` = paste the ENTIRE JSON file contents from step 4
- `LEADS_SHEET_ID` = the ID from step 7

Repeat steps 1-7 for a second sheet tab named `Partnerships` (columns:
`org_name | contact_name | email | org_type | website | status | last_sent_date`)
if you want the weekly partnership outreach running — secret name `PARTNERSHIPS_SHEET_ID`.

### 4d. Social images (OpenAI + imgbb)

1. Go to platform.openai.com → sign up/sign in → **Settings → Billing** → add a
   payment method (this one costs money per image, unlike everything else so far).
2. **API keys** (left menu) → **Create new secret key** → copy it immediately (you
   can't view it again later).
3. Go to api.imgbb.com → sign up free → your API key is shown on that page → copy it.

**Add these secrets:**
- `OPENAI_API_KEY` = the key from step 2
- `IMGBB_API_KEY` = the key from step 3

### 4e. Social posting itself (Meta: Instagram, Facebook, Threads) — do this LAST, it's the slow one

This needs Meta's App Review approval first (1-3 weeks), covered in the separate
`META_APP_REVIEW.md` file. **Threads needs its own separate approval** even though
it's the same Meta family — different permissions, same submission round if you
request both together (see Section 7 of that file). Come back to this section once
approved. When it is, you'll get tokens from Meta's dashboard — add them as:
- `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`, `META_PAGE_ID` (Instagram + Facebook)
- `THREADS_ACCESS_TOKEN`, `THREADS_USER_ID` (Threads)

Until then, just don't add these — those jobs will fail harmlessly and everything
else keeps running.

### 4f. X (Twitter) — skipped on purpose

X's API has no free posting tier (pay-per-use since Feb 2026, ~$0.015/post — cheap
but not free). This system stays draft-only for X: it writes post text to a file
for you to copy-paste manually, no key needed, no cost. Nothing to set up here
unless you later decide to pay for real auto-posting.

---

## Part 5 — Test everything before trusting the schedule

1. On your repo's GitHub page, click the **Actions** tab (top).
2. You'll see a list of workflows on the left: "Daily Blog Post," "Daily Business
   Outreach," etc.
3. Click one → click the **Run workflow** button (top right of that list) → **Run
   workflow** (confirm).
4. Wait ~30-60 seconds, refresh, click into the run that appears → click the job
   name → you'll see line-by-line logs, like a diary of exactly what the script did.
5. Green checkmark = it worked. Red X = something failed — click into the failed
   step, read the error message (it usually tells you plainly what's wrong, e.g.
   "Missing required environment variable: BREVO_API_KEY" means you typo'd a secret
   name).

Do this for each workflow once. Only trust the automatic daily schedule once each
one has gone green at least once manually.

---

## Part 6 — What happens now, forever, without you touching anything

Once secrets are in and you've done Part 5:
- Every day, the blog posts itself.
- Twice a day, Instagram/Facebook post + story themselves (once Meta approves).
- Every weekday, up to 30+30 cold emails send themselves.
- Every Monday, newsletter/carousel/partnership drafts get made.

You do NOT need to open your laptop, run any command, or click anything for this to
keep happening. GitHub's servers run it, on schedule, in the cloud.

---

## Part 7 — The only things that still need YOU, occasionally

- **Refill the Leads sheet** every couple weeks (new rows, using free tools like
  Hunter.io — details in `OUTREACH_SETUP.md`).
- **Check `dm_drafts.jsonl`** in your repo occasionally and manually send any reply
  you like on Instagram — this stays human-controlled on purpose.
- **Meta App Review** — a one-time approval, not repeating.
- **Glance at the Actions tab** every so often to make sure things are still green,
  not red.

---

## Troubleshooting cheat sheet

| Error mentions... | Usually means... |
|---|---|
| "Missing required environment variable: X" | You forgot to add secret X, or typed its name wrong (secret names must match EXACTLY, including capital letters) |
| 401 / "Unauthorized" | A key/token is wrong, expired, or copy-pasted with an extra space |
| "Missing a 'segment' column" | Your Leads sheet header row doesn't say exactly `segment` in one of the columns |
| Blogger/Sheets errors mentioning "insufficient permission" | You forgot to Share the sheet with the service account email, or forgot to Enable the API in Google Cloud |
| Social job fails, everything else fine | Expected until Meta App Review is approved — not a bug |

If you get stuck on any single step, tell me exactly which step number and paste the
error text — that's all I need to help you past it.
