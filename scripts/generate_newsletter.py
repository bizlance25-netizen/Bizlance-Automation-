"""
generate_newsletter.py — drafts a weekly newsletter and saves it for review/sending.

This does NOT auto-send. Newsletters go to an opted-in subscriber list, and sending
without genuine opt-in confirmation is a compliance risk the same way cold-DM spam is.
Draft is written to newsletter_drafts/ in the repo; send it manually via Brevo's
campaign UI (or wire it to Brevo's Campaigns API once you're comfortable it reads well).

Run weekly via .github/workflows/weekly-growth.yml
"""
import os
import sys
import datetime
from common import generate_text_json

OUT_DIR = "newsletter_drafts"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    prompt = (
        "Write a weekly newsletter for Bizlance, a marketplace connecting businesses with "
        "vetted AI service providers. Audience: a mixed list of businesses considering AI "
        "providers AND AI agencies/freelancers who list on Bizlance. Structure: "
        "1) A short, useful insight or trend relevant to AI automation/services this week "
        "(2-3 sentences). "
        "2) A 'For Businesses' section: one practical tip about hiring/evaluating AI providers. "
        "3) A 'For Providers' section: one practical tip about winning clients or building a "
        "stronger profile. "
        "4) A short closing line pointing both audiences toward Bizlance. "
        "Tone: helpful, plain, not salesy. "
        'Return ONLY valid JSON with keys "subject_line" and "html_body" (html_body using '
        "<h2> and <p> tags). No commentary, no code fences."
    )
    parsed = generate_text_json(prompt)

    date_str = datetime.date.today().isoformat()
    path = os.path.join(OUT_DIR, f"newsletter_{date_str}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- Subject: {parsed.get('subject_line', 'Bizlance Weekly')} -->\n")
        f.write(parsed.get("html_body", parsed.get("raw", "")))

    print(f"Draft saved: {path}")
    print(f"Subject line: {parsed.get('subject_line')}")
    print("Review and send manually via Brevo Campaigns (or your ESP of choice).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
