"""
post_threads.py — generates a short SEO caption and posts it to Threads.

REQUIRES its own Meta App Review approval — Threads uses a DIFFERENT permission
set (threads_basic, threads_content_publish) from Instagram/Facebook, even though
it's the same Meta family of APIs. You cannot reuse your Instagram/Facebook
approval for this — it's a second (smaller, usually faster) review. Fold it into
the same submission round as your IG/FB one if you haven't submitted yet — see
META_APP_REVIEW.md.

Threads is a text-first platform — this posts text-only by default (image posting
is supported by the API too, but adds another OpenAI+imgbb round trip for a
platform where plain text performs perfectly well; ask Claude Code to add an image
if you want one later, same pattern as post_social.py).

Run daily via .github/workflows/daily-social.yml (as an extra step)
Required secrets: THREADS_ACCESS_TOKEN, THREADS_USER_ID
"""
import os
import sys
import time
import requests
from common import generate_text_json

THREADS_BASE = "https://graph.threads.net/v1.0"

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


def pick_topic():
    import datetime
    day = datetime.date.today().toordinal()
    segment = "buyer" if day % 2 == 0 else "provider"
    topics = BUYER_TOPICS if segment == "buyer" else PROVIDER_TOPICS
    return segment, topics[day % len(topics)]


def generate_thread_post(segment: str, topic: str) -> str:
    audience = (
        "businesses looking to hire AI providers" if segment == "buyer"
        else "AI agencies and providers looking for clients"
    )
    prompt = (
        f"Write a single Threads post (under 400 characters, conversational, no "
        f"corporate voice) for Bizlance, a marketplace connecting businesses with "
        f"vetted AI service providers, written for {audience}, about: {topic}. "
        "Naturally include one real search-style keyword phrase this audience would "
        "actually use. End with exactly 5 relevant hashtags. "
        'Return ONLY valid JSON with key "post_text". No commentary, no code fences.'
    )
    parsed = generate_text_json(prompt)
    return parsed.get("post_text", parsed.get("raw", "")).strip()


def post_to_threads(text: str, user_id: str, token: str):
    # Step 1: create the media container
    container = requests.post(f"{THREADS_BASE}/{user_id}/threads", data={
        "media_type": "TEXT",
        "text": text,
        "access_token": token,
    }, timeout=30)
    container.raise_for_status()
    creation_id = container.json()["id"]

    # Step 2: publish it (Threads recommends a short wait before publishing)
    time.sleep(5)
    publish = requests.post(f"{THREADS_BASE}/{user_id}/threads_publish", data={
        "creation_id": creation_id,
        "access_token": token,
    }, timeout=30)
    publish.raise_for_status()
    return publish.json()


def main():
    segment, topic = pick_topic()
    print(f"Segment: {segment} | Topic: {topic}")

    post_text = generate_thread_post(segment, topic)
    print(f"Post text: {post_text}")

    token = os.environ["THREADS_ACCESS_TOKEN"]
    user_id = os.environ["THREADS_USER_ID"]

    result = post_to_threads(post_text, user_id, token)
    print(f"Threads post published: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED (expected until Threads App Review is approved): {e}", file=sys.stderr)
        sys.exit(1)
