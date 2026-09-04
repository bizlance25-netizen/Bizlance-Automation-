"""
partnership_outreach.py — drafts partnership proposal emails to AI/startup communities,
newsletters, accelerators, and similar, from a seed list you maintain.

Unlike lead outreach, there's no free API that discovers "AI communities and
newsletters" automatically — this needs a human-curated seed list (same honest
tradeoff as the cold-email lead list). This script handles personalization + sending
+ tracking once you've listed targets.

Run weekly via .github/workflows/weekly-growth.yml
Required secrets: GOOGLE_SERVICE_ACCOUNT_JSON, PARTNERSHIPS_SHEET_ID, BREVO_API_KEY, SENDER_EMAIL

Sheet 'Partnerships' tab columns:
org_name | contact_name | email | org_type | website | status | last_sent_date

org_type examples: "AI community", "newsletter", "accelerator", "SaaS company",
"business association" — used to tailor the pitch.
"""
import sys
import json
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
from common import env, generate_text_json

WEEKLY_CAP = 10  # partnerships are lower-volume, higher-effort than cold leads

FOOTER_TEMPLATE = (
    "\n\n---\n"
    "Bizlance | 11/6A Govind Marg, Jaipur, Rajasthan, India\n"
    'Not the right fit or contact? Just let us know and we won\'t follow up again.'
)


def get_sheet():
    creds_dict = json.loads(env("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(env("PARTNERSHIPS_SHEET_ID")).worksheet("Partnerships")


def generate_proposal(org_name: str, contact_name: str, org_type: str) -> dict:
    prompt = (
        f"Write a short, genuine partnership outreach email (under 130 words) from Bizlance "
        f"(a marketplace connecting businesses with vetted AI service providers) to "
        f"{org_name}, a {org_type or 'organization'}. Address them as {contact_name or 'there'}. "
        "Propose one concrete, low-effort form of collaboration that fits their org_type "
        "(e.g. for a newsletter: a sponsored mention or content swap; for a community: "
        "an AMA or resource share; for an accelerator: a perk for portfolio companies). "
        "No hype, be specific about the ask, make it easy to say yes or no. "
        'Return ONLY valid JSON with keys "subject" and "body_text" (use \\n for line breaks). '
        "No commentary, no code fences."
    )
    return generate_text_json(prompt)


def send_via_brevo(to_email: str, to_name: str, subject: str, body_text: str):
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": env("BREVO_API_KEY"), "Content-Type": "application/json"},
        json={
            "sender": {"name": "Bizlance Partnerships", "email": env("SENDER_EMAIL")},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "textContent": body_text,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    sheet = get_sheet()
    records = sheet.get_all_records()
    header = sheet.row_values(1)

    sent_count = 0
    for idx, row in enumerate(records, start=2):
        if sent_count >= WEEKLY_CAP:
            break
        email = (row.get("email") or "").strip()
        status = (row.get("status") or "").strip()
        if not email or status:
            continue

        org_name = row.get("org_name", "")
        contact = row.get("contact_name", "")
        org_type = row.get("org_type", "")

        try:
            content = generate_proposal(org_name, contact, org_type)
            subject = content.get("subject", f"Partnership idea for {org_name}")
            body = content.get("body_text", content.get("raw", "")) + FOOTER_TEMPLATE

            send_via_brevo(email, org_name, subject, body)

            status_col = header.index("status") + 1
            date_col = header.index("last_sent_date") + 1
            sheet.update_cell(idx, status_col, "sent")
            sheet.update_cell(idx, date_col, datetime.date.today().isoformat())

            sent_count += 1
            print(f"Sent partnership proposal to {org_name} <{email}>")
        except Exception as e:
            print(f"Skipped {org_name} <{email}>: {e}", file=sys.stderr)

    print(f"Done. Sent {sent_count} partnership email(s) this week.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
