"""
generate_x_post.py — drafts a daily X (Twitter) post. Does NOT auto-post.

X's API has no free tier for posting (pay-per-use since Feb 2026, roughly
$0.015/post) — since the rest of this system is built to stay free wherever
possible, this stays a draft-only script: it writes the post text to a file for
you to copy-paste manually, at $0 cost. If you decide the small per-post cost is
worth it later, this is where the actual X API v2 posting call (OAuth 1.0a via
requests-oauthlib) would go — ask Claude Code to wire it in once you're ready to
pay for it.

Run daily via .github/workflows/daily-extras.yml
"""
import os
import sys
import json
import datetime
from common import generate_text_json, pick_alternating

BUYER_TOPICS = [
    "the real cost of a bad AI provider hire",
    "how to know if your business actually needs AI automation",
    "one question to ask before hiring an AI agency",
]
PROVIDER_TOPICS = [
    "why case studies beat cold pitches for AI agencies",
    "the fastest way to build trust as a new AI provider",
    "one profile mistake that costs AI freelancers clients",
]

OUT_FILE = "x_post_drafts.jsonl"


def main():
    segment, topic = pick_alternating(BUYER_TOPICS, PROVIDER_TOPICS)
    print(f"Segment: {segment} | Topic: {topic}")

    prompt = (
        f"Write a single X (Twitter) post (under 260 characters, no hashtag spam, 1 hashtag "
        f"max) for Bizlance, a marketplace connecting businesses with vetted AI service "
        f"providers, about: {topic}. Plain, direct, no corporate voice. "
        'Return ONLY valid JSON with key "post_text". No commentary, no code fences.'
    )
    parsed = generate_text_json(prompt)
    post_text = parsed.get("post_text", parsed.get("raw", "")).strip()

    with open(OUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "date": datetime.date.today().isoformat(),
            "segment": segment,
            "post_text": post_text,
        }, ensure_ascii=False) + "\n")

    print(f"Draft appended to {OUT_FILE}:")
    print(post_text)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
