"""
post_social.py — generates an image + SEO caption and posts to Instagram + Facebook.

Runs TWICE a day (see .github/workflows/daily-social.yml), once per SLOT env var:
  SLOT=morning -> 1 Buyer-facing post + 1 Buyer-facing story
  SLOT=evening -> 1 Provider-facing post + 1 Provider-facing story
That's 2 posts + 2 stories/day total, covering both sides of the marketplace daily.

TIMING NOTE: "morning"/"evening" are generic best-practice windows (late morning and
early evening), NOT derived from your actual audience's real active hours — there's
no Instagram Insights data connected here to know that yet (the account has no
history). Once you have real follower activity data (Instagram Insights, available
once the account has enough followers/history), adjust the cron times in the
workflow file to match. Times in the workflow are UTC — convert to your audience's
actual timezone.

REQUIRES Meta App Review approval first (instagram_content_publish, pages_manage_posts).
Until then, this script will fail at the publish step by design.

Required secrets: META_PAGE_ACCESS_TOKEN, META_IG_BUSINESS_ID, META_PAGE_ID,
                   OPENAI_API_KEY, IMGBB_API_KEY
"""
import os
import sys
import time
import requests
from common import env, generate_text_json, generate_image_openai, upload_image_public

GRAPH_BASE = "https://graph.facebook.com/v19.0"

BUYER_THEMES = [
    "AI service providers helping small businesses save time",
    "How to choose the right AI provider for your business",
    "AI automation vs hiring another employee",
    "Bizlance's upcoming secure, fraud-proof payment system",
    "Why verified delivery matters when hiring AI providers",
]

PROVIDER_THEMES = [
    "How AI agencies can get more clients through Bizlance",
    "Why a strong case study wins more AI clients than a pitch deck",
    "Building trust as an AI provider: verification and proof",
    "How to write a provider profile that actually converts",
    "Winning AI clients without racing to the bottom on price",
]


def pick_theme(segment: str) -> str:
    import datetime
    themes = BUYER_THEMES if segment == "buyer" else PROVIDER_THEMES
    return themes[datetime.date.today().toordinal() % len(themes)]


def generate_post_content(theme: str, segment: str) -> dict:
    audience = (
        "businesses looking to hire AI providers" if segment == "buyer"
        else "AI agencies and providers looking for clients"
    )
    prompt = (
        f"Write an Instagram/Facebook caption for Bizlance, a marketplace connecting "
        f"businesses with vetted AI service providers, written for {audience}, about: {theme}. "
        "Requirements: "
        "1) Caption under 100 words, plain and direct, no corporate voice. "
        "2) Naturally include one clear keyword phrase this audience would actually "
        "search (this is the caption's SEO/discoverability hook — e.g. 'AI automation "
        "agency' or 'hire AI provider'). "
        "3) End with EXACTLY 5 relevant hashtags, no more, no fewer, mixing broad and "
        "specific (e.g. #AIAutomation plus something niche). "
        "4) Separately, a short visual description for an AI image generator (clean "
        "modern tech/SaaS aesthetic, no readable text baked into the image). "
        '5) Separately, a "story_headline": a punchy 4-6 word headline to render as bold '
        "text directly on the Story image (Stories can't carry a caption via the API, "
        "so the hook has to live in the image itself). "
        'Return ONLY valid JSON with keys "caption", "image_prompt", "story_headline". '
        "No commentary, no code fences."
    )
    return generate_text_json(prompt)


def make_public_image(prompt: str, size: str = "1024x1024") -> str:
    img_bytes = generate_image_openai(prompt, size=size)
    return upload_image_public(img_bytes, name="bizlance-social")


def post_feed_photo(image_url: str, caption: str, ig_id: str, token: str):
    container = requests.post(f"{GRAPH_BASE}/{ig_id}/media", data={
        "image_url": image_url, "caption": caption, "access_token": token,
    }, timeout=30)
    container.raise_for_status()
    creation_id = container.json()["id"]
    time.sleep(3)
    publish = requests.post(f"{GRAPH_BASE}/{ig_id}/media_publish", data={
        "creation_id": creation_id, "access_token": token,
    }, timeout=30)
    publish.raise_for_status()
    return publish.json()


def post_story(image_url: str, ig_id: str, token: str):
    """Instagram Stories via the Graph API do not support a caption/text field —
    any text has to be baked into the image itself (handled by story_headline above)."""
    container = requests.post(f"{GRAPH_BASE}/{ig_id}/media", data={
        "image_url": image_url, "media_type": "STORIES", "access_token": token,
    }, timeout=30)
    container.raise_for_status()
    creation_id = container.json()["id"]
    time.sleep(3)
    publish = requests.post(f"{GRAPH_BASE}/{ig_id}/media_publish", data={
        "creation_id": creation_id, "access_token": token,
    }, timeout=30)
    publish.raise_for_status()
    return publish.json()


def post_to_facebook_page(image_url: str, caption: str, page_id: str, token: str):
    resp = requests.post(f"{GRAPH_BASE}/{page_id}/photos", data={
        "url": image_url, "caption": caption, "access_token": token,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    slot = os.environ.get("SLOT", "morning").lower()
    segment = "buyer" if slot == "morning" else "provider"
    theme = pick_theme(segment)
    print(f"Slot: {slot} | Segment: {segment} | Theme: {theme}")

    content = generate_post_content(theme, segment)
    caption = content.get("caption", theme)
    image_prompt = content.get("image_prompt", theme)
    story_headline = content.get("story_headline", theme[:40])

    token = env("META_PAGE_ACCESS_TOKEN")
    ig_id = env("META_IG_BUSINESS_ID")
    page_id = env("META_PAGE_ID")

    # --- Feed post (square) ---
    post_image_url = make_public_image(image_prompt, size="1024x1024")
    ig_result = post_feed_photo(post_image_url, caption, ig_id, token)
    print(f"Instagram post published: {ig_result}")
    fb_result = post_to_facebook_page(post_image_url, caption, page_id, token)
    print(f"Facebook post published: {fb_result}")

    # --- Story (vertical, headline baked into the image prompt) ---
    story_prompt = (
        f"{image_prompt}, with bold clean white text overlay reading "
        f'"{story_headline}", vertical composition, mobile story format'
    )
    story_image_url = make_public_image(story_prompt, size="1024x1536")
    story_result = post_story(story_image_url, ig_id, token)
    print(f"Instagram story published: {story_result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED (expected until Meta App Review is approved): {e}", file=sys.stderr)
        sys.exit(1)
