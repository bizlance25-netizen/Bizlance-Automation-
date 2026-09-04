"""
post_blog.py — generates a blog post and publishes it to Blogger.

Run daily via .github/workflows/daily-blog.yml
Required secrets: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, BLOGGER_BLOG_ID

SEO NOTE: Blogger's public API does not expose a settable "meta description" field
per post (that field only exists in the Blogger UI's per-post "Search description"
box, which isn't part of the REST API). This script still generates one and prints
it in the logs so you can paste it in manually if you want the meta tag set exactly -
takes 10 seconds in the Blogger dashboard after each post. Everything else (keyword-
targeted title, H2 structure, labels/tags, keyword-rich image alt text) IS fully
automated through the API.
"""
import sys
import datetime
import requests
from common import env, generate_text_json, generate_image_url, pick_alternating

BUYER_TOPICS = [
    "How much does an AI automation project actually cost?",
    "How to choose an AI agency",
    "5 AI workflows every small business should consider",
    "How to evaluate an AI provider before you hire one",
    "AI automation vs. hiring another employee",
    "How to calculate ROI from an AI project",
    "Why AI projects fail (and how to avoid it)",
]

PROVIDER_TOPICS = [
    "How AI agencies can get more clients",
    "How to build an AI case study that actually converts",
    "How to demonstrate AI ROI to a skeptical buyer",
    "How to create a high-converting provider profile",
    "Why proof matters more than promises in AI sales",
    "How to win AI clients without racing to the bottom on price",
]


def get_google_access_token() -> str:
    """Exchange the long-lived refresh token for a short-lived access token."""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": env("GOOGLE_CLIENT_ID"),
        "client_secret": env("GOOGLE_CLIENT_SECRET"),
        "refresh_token": env("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def pick_topic() -> str:
    day_index = (datetime.date.today() - datetime.date(2026, 1, 1)).days % len(TOPICS)
    return TOPICS[day_index]


def main():
    segment, topic = pick_alternating(BUYER_TOPICS, PROVIDER_TOPICS)
    print(f"Segment: {segment} | Topic: {topic}")

    audience_line = (
        "businesses looking to hire AI service providers"
        if segment == "buyer"
        else "AI agencies, freelancers, and providers looking for clients"
    )

    # SEO-aware generation: ask for a focus keyword, an SEO title, on-page structure,
    # labels (Blogger's equivalent of tags/categories, which do get indexed), and
    # a meta-description-style opening line built around the focus keyword.
    prompt = (
        f"Write an SEO-optimized 600-700 word blog post for Bizlance, a marketplace "
        f"connecting businesses with vetted AI service providers, written for {audience_line}, "
        f"about: {topic}. Requirements: "
        "1) Pick ONE realistic focus keyword/phrase this audience would actually search. "
        "2) Title under 60 characters, includes the focus keyword naturally, no clickbait. "
        "3) First paragraph (2-3 sentences, this doubles as the meta description) must "
        "include the focus keyword in the first sentence. "
        "4) Use 2-4 <h2> subheadings that include natural variations of the keyword/topic. "
        "5) Body in short <p> paragraphs, no walls of text. "
        f"6) Include one CTA near the end pointing this specific audience ({audience_line}) "
        "toward Bizlance (as plain text, not a fake link). "
        "7) Suggest 3-5 short label/tag keywords for the post. "
        'Return ONLY valid JSON with keys "title", "focus_keyword", "meta_description", '
        '"html_body", "labels" (labels = array of 3-5 short strings). '
        "No commentary, no code fences, no markdown outside the HTML in html_body."
    )
    parsed = generate_text_json(prompt)
    if "title" not in parsed or "html_body" not in parsed:
        print("Model didn't return clean SEO JSON, using fallback formatting.")
        parsed = {
            "title": topic,
            "focus_keyword": topic,
            "meta_description": topic,
            "html_body": f"<p>{parsed.get('raw', '')}</p>",
            "labels": [],
        }

    labels = parsed.get("labels", [])
    labels = list(labels) + [segment]  # tag every post Buyer or Provider for tracking

    # Image alt text uses the focus keyword — meaningful for image search SEO,
    # unlike a generic alt tag.
    focus_kw = parsed.get("focus_keyword", parsed["title"])
    image_url = generate_image_url(
        f"professional blog header illustration, {parsed['title']}, clean modern flat design"
    )
    html_body = (
        f'<img src="{image_url}" alt="{focus_kw}" title="{focus_kw}" '
        f'style="max-width:100%;height:auto;margin-bottom:16px;"/>' + parsed["html_body"]
    )

    token = get_google_access_token()
    blog_id = env("BLOGGER_BLOG_ID")
    post_body = {
        "kind": "blogger#post",
        "title": parsed["title"],
        "content": html_body,
        "labels": labels,
    }
    resp = requests.post(
        f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/",
        headers={"Authorization": f"Bearer {token}"},
        json=post_body,
        timeout=30,
    )
    resp.raise_for_status()
    print(f"Published: {resp.json().get('url')}")
    print(f"Focus keyword: {focus_kw}")
    print(f"Meta description (for reference, see note below): {parsed.get('meta_description')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
