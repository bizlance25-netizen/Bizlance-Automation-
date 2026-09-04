"""
dm_draft_replies.py — drafts reply suggestions for people who've already engaged with
Bizlance's Instagram (comments/mentions), for a HUMAN to review and send manually.

This deliberately does NOT auto-send DMs. Bulk automated outbound DMs to people who
haven't engaged first violate Meta's platform policy and risk the account being
disabled — which would take down the whole pipeline (blog, social, email) with it.
This script only drafts replies to inbound engagement, within Meta's allowed window.

Run daily via .github/workflows/daily-social.yml (or on its own schedule)
Required secrets: META_PAGE_ACCESS_TOKEN, META_IG_BUSINESS_ID
Output: drafts written to dm_drafts.jsonl in the repo for a human to review each morning.
"""
import sys
import requests
from common import env, generate_text, load_json_lines, append_json_line

GRAPH_BASE = "https://graph.facebook.com/v19.0"
DRAFTS_FILE = "dm_drafts.jsonl"


def fetch_recent_comments(ig_id: str, token: str) -> list:
    """Pull comments on recent media - these are people who've already engaged."""
    media_resp = requests.get(f"{GRAPH_BASE}/{ig_id}/media", params={
        "fields": "id,caption,comments{id,text,username,timestamp}",
        "access_token": token,
        "limit": 10,
    }, timeout=30)
    media_resp.raise_for_status()
    comments = []
    for post in media_resp.json().get("data", []):
        for c in post.get("comments", {}).get("data", []):
            comments.append({
                "comment_id": c["id"],
                "username": c.get("username", "unknown"),
                "text": c.get("text", ""),
            })
    return comments


def draft_reply(username: str, comment_text: str) -> str:
    prompt = (
        f'An Instagram user "{username}" commented: "{comment_text}" on a Bizlance post '
        "(a platform connecting businesses with vetted AI service providers). "
        "Write a short, warm, genuine reply (under 40 words) a human at Bizlance could send. "
        "No hard selling. Plain text only, no JSON."
    )
    return generate_text(prompt).strip()


def main():
    token = env("META_PAGE_ACCESS_TOKEN")
    ig_id = env("META_IG_BUSINESS_ID")

    already_drafted = {d["comment_id"] for d in load_json_lines(DRAFTS_FILE)}
    comments = fetch_recent_comments(ig_id, token)

    new_drafts = 0
    for c in comments:
        if c["comment_id"] in already_drafted:
            continue
        reply = draft_reply(c["username"], c["text"])
        append_json_line(DRAFTS_FILE, {
            "comment_id": c["comment_id"],
            "username": c["username"],
            "original_comment": c["text"],
            "drafted_reply": reply,
            "status": "pending_human_review",
        })
        new_drafts += 1

    print(f"Drafted {new_drafts} new reply suggestion(s) into {DRAFTS_FILE}.")
    print("Review and send these manually from Instagram/Meta Business Suite.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
