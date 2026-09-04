"""
send_outreach.py — personalizes and sends business-only cold emails from a Google Sheet
lead list, split into two segments: BUYERS (businesses who'd hire an AI provider) and
PROVIDERS (AI agencies/freelancers who'd want to be listed on Bizlance).

Run on weekdays via .github/workflows/daily-outreach.yml
Required secrets: GOOGLE_SERVICE_ACCOUNT_JSON, LEADS_SHEET_ID, BREVO_API_KEY, SENDER_EMAIL
Optional secrets: DAILY_CAP_PROVIDER (default 30), DAILY_CAP_BUYER (default 30)

Sheet 'Leads' tab columns:
company_name | contact_name | email | industry | website | segment | status | last_sent_date

'segment' must be exactly "provider" or "buyer" — rows with anything else are skipped,
so nothing gets emailed with the wrong pitch by mistake.
"""
import os
import sys
import json
import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
from common import env, generate_text_json

CONSUMER_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "aol.com", "protonmail.com",
}
DAILY_CAP_PROVIDER = int(os.environ.get("DAILY_CAP_PROVIDER", "30"))
DAILY_CAP_BUYER = int(os.environ.get("DAILY_CAP_BUYER", "30"))

FOOTER_TEMPLATE = (
    "\n\n---\n"
    "Bizlance | 11/6A Govind Marg, Jaipur, Rajasthan, India\n"
    'Don\'t want these emails? Reply "unsubscribe" and we\'ll remove you immediately.'
)


def get_sheet():
    creds_dict = json.loads(env("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(env("LEADS_SHEET_ID")).worksheet("Leads")


def is_business_email(email: str) -> bool:
    domain = email.lower().split("@")[-1] if "@" in email else ""
    return bool(domain) and domain not in CONSUMER_DOMAINS


def generate_email(segment: str, company_name: str, contact_name: str, industry: str) -> dict:
    if segment == "provider":
        pitch = (
            "invite them to list their AI agency/services on Bizlance, a marketplace "
            "that connects them with businesses actively looking to hire AI providers. "
            "Mention that a strong profile with a real case study converts far better "
            "than a generic listing."
        )
    else:
        pitch = (
            "introduce Bizlance, a marketplace where they can find vetted, proven AI "
            "service providers for a specific business need, without the risk of a "
            "random freelancer hire."
        )
    prompt = (
        f"Write a short, human, non-spammy cold outreach email (under 120 words) from Bizlance to "
        f"{company_name}, a company in the {industry or 'business'} industry. "
        f"Address them as {contact_name or 'there'}. Goal: {pitch} "
        "No hype, no exclamation marks, no generic flattery. "
        "End with a soft, low-pressure call to action. "
        'Return ONLY valid JSON with keys "subject" and "body_text" (use \\n for line breaks). '
        "No commentary, no code fences."
    )
    return generate_text_json(prompt)


def send_via_brevo(to_email: str, to_name: str, subject: str, body_text: str):
    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": env("BREVO_API_KEY"), "Content-Type": "application/json"},
        json={
            "sender": {"name": "Bizlance", "email": env("SENDER_EMAIL")},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "textContent": body_text,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def process_segment(sheet, records, header, segment: str, cap: int) -> int:
    sent_count = 0
    for idx, row in enumerate(records, start=2):  # row 1 is header
        if sent_count >= cap:
            break
        email = (row.get("email") or "").strip()
        status = (row.get("status") or "").strip()
        row_segment = (row.get("segment") or "").strip().lower()
        if not email or status or row_segment != segment or not is_business_email(email):
            continue

        company = row.get("company_name", "")
        contact = row.get("contact_name", "")
        industry = row.get("industry", "")

        try:
            content = generate_email(segment, company, contact, industry)
            subject = content.get("subject", f"Quick idea for {company}")
            body = content.get("body_text", content.get("raw", "")) + FOOTER_TEMPLATE

            send_via_brevo(email, company, subject, body)

            status_col = header.index("status") + 1
            date_col = header.index("last_sent_date") + 1
            sheet.update_cell(idx, status_col, "sent")
            sheet.update_cell(idx, date_col, datetime.date.today().isoformat())

            sent_count += 1
            print(f"[{segment}] Sent to {company} <{email}>")
        except Exception as e:
            print(f"[{segment}] Skipped {company} <{email}>: {e}", file=sys.stderr)
    return sent_count


def main():
    sheet = get_sheet()
    records = sheet.get_all_records()
    header = sheet.row_values(1)
    if "segment" not in header:
        raise RuntimeError(
            "Leads sheet is missing a 'segment' column (must contain 'buyer' or 'provider' "
            "per row). Add it before running — see OUTREACH_SETUP.md."
        )

    provider_sent = process_segment(sheet, records, header, "provider", DAILY_CAP_PROVIDER)
    # re-fetch records so status updates from the provider pass aren't stale for the buyer pass
    records = sheet.get_all_records()
    buyer_sent = process_segment(sheet, records, header, "buyer", DAILY_CAP_BUYER)

    print(f"Done. Sent {provider_sent} provider email(s), {buyer_sent} buyer email(s) today.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
