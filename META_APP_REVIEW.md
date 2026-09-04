# Meta App Review Submission — Bizlance Automation

Everything below is written to paste directly into Meta's App Review request form
(developers.facebook.com → your app → App Review → Permissions and Features).

---

## 1. App setup checklist (before you can even submit)

- [ ] Facebook Page for Bizlance exists and is set to Business/Creator, not personal
- [ ] Instagram account is a **Business** or **Creator** account (not personal)
- [ ] Instagram account is **linked** to the Facebook Page (Meta Business Suite → Settings → Linked Accounts)
- [ ] You are an **admin** of both the Page and the Meta Business Portfolio
- [ ] Business Verification is completed for your Meta Business Portfolio (Business Settings → Security Center) — Meta increasingly requires this before granting advanced permissions
- [ ] A live, working **Privacy Policy URL** exists on bizlance.online (required — Meta rejects apps without one)
- [ ] App icon (1024x1024) and a short app description are filled in under App Settings → Basic

---

## 2. Permissions to request

Request exactly these — asking for extra unused permissions is a common rejection reason:

| Permission | Why you need it |
|---|---|
| `pages_show_list` | To let the app identify which Page it's posting to |
| `pages_read_engagement` | To read post performance / comments (used by the DM-draft review step) |
| `pages_manage_posts` | To publish posts to the Facebook Page |
| `instagram_basic` | To read basic Instagram account/media info |
| `instagram_content_publish` | To publish photos to the Instagram Business account |
| `business_management` | To manage the connection between the app and your Business Portfolio |

---

## 3. App use case description (paste into the "How will your business use this permission" field for each)

Use one consistent narrative across all permissions — reviewers check for consistency:

> Bizlance is a platform connecting businesses with vetted AI service providers. We use the Meta Graph API to automate publishing our own marketing content — daily educational and promotional posts about our platform — to our own Facebook Page and Instagram Business account. We also read comments on our own posts to identify users who've engaged, so our team can prepare thoughtful replies. We do not access, post on, or message on behalf of any other business or user — only our own owned Page and Instagram account, which we administer directly.

For `instagram_content_publish` specifically, add:

> Content is generated on a daily schedule (via our own backend), reviewed against our brand guidelines programmatically, and published automatically to our own Instagram Business account. No third-party accounts are posted to.

For `pages_read_engagement` / reading comments, add:

> We read comments on our own Page/Instagram posts solely to draft suggested replies for a human team member to review and send manually — we do not auto-reply or auto-message anyone.

---

## 4. Screen recording script (required for most permissions)

Meta requires a screencast showing the real, working flow — not a mockup. Record your actual screen:

**For `pages_manage_posts` + `instagram_content_publish`:**
1. Show Meta Business Suite, with the Bizlance Page and linked Instagram account visible, proving you administer both.
2. Show your app's dashboard/terminal (this can be a GitHub Actions run) triggering the post script.
3. Show the API call succeeding (the workflow log line showing `Instagram posted:` / `Facebook posted:`) — Chrome/terminal window is fine, no polish needed.
4. Immediately after, show the new post live on the actual Instagram/Facebook Page in the app or web view — this is the step reviewers look for most: proof the post really landed on your own account.

**For `pages_read_engagement`:**
1. Show a comment existing on one of your live posts.
2. Show the script (`dm_draft_replies.py` run) pulling that comment.
3. Show the resulting draft written to `dm_drafts.jsonl` in your GitHub repo — this also demonstrates you're not auto-sending, which pre-empts a common rejection reason.

**For `business_management`:**
1. Show Business Settings → the app listed as a connected technology partner under your Business Portfolio.

Keep the whole recording under 5 minutes, screen-only (no need for narration, but a soft voiceover explaining each step helps reviewers move faster).

---

## 5. Privacy Policy — minimum required content

Meta checks this URL is live and actually describes data use. At minimum, bizlance.online needs a page stating:
- What data you collect via the Instagram/Facebook connection (post content, comment text/usernames from your own account)
- That you don't sell or share this data with third parties
- That the data is used solely to operate Bizlance's own marketing and engagement workflow
- A contact email for privacy questions

I can draft this as an actual privacy policy page if you want — say the word and I'll write it.

---

## 6. Common rejection reasons to pre-empt

- **Vague use case text** — the wording above is deliberately specific about "our own Page/account only." Don't generalize it.
- **Missing Business Verification** — do this before submitting, it blocks review otherwise.
- **Screen recording shows a mockup, not the live API call** — reviewers reject on sight if it looks staged; your GitHub Actions log + the real post appearing live is exactly what they want to see.
- **Requesting permissions you don't demonstrate using** — every permission above is used in the recording; don't add ones you can't show.
- **No privacy policy, or one that doesn't mention this specific data use.**

---

## 7. Threads — a SEPARATE review, don't skip this

Threads uses its own permission set (`threads_basic`, `threads_content_publish`) —
even though it's the same Meta family, your Instagram/Facebook approval above does
**not** cover Threads. In the Meta Developer dashboard, add the "Threads API"
product to the same app and request these two permissions alongside the ones
above — submitting them together means one review cycle instead of two. Use the
same "own account only" use-case language from Section 3, adapted:

> We use the Threads API to publish our own marketing content to our own Threads account, on the same automated daily schedule as our Instagram/Facebook presence. We do not post on behalf of any other account.

Screen recording requirement is the same pattern as Section 4 — show the post
actually landing on your real Threads profile, not a mockup.

## Timeline expectation

Submission review typically takes **3-10 business days** for straightforward, well-documented requests like this one (single-business, own-account-only use case). Business Verification, if not already done, can add another 1-2 weeks before you can even submit — worth starting that first, today, in parallel with recording the screencast.
