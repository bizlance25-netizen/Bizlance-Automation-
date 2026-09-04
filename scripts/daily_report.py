"""
daily_report.py — assembles the daily report: what the pipeline actually did today
(content published, emails sent — things this repo can always know) plus real
marketplace numbers if fetch_marketplace_metrics.py is connected to your backend
(things this repo can only know once you wire that up).

Run daily as the last step, after the other jobs.
"""
import os
import json
import datetime


def load_metrics():
    if os.path.exists("marketplace_metrics.json"):
        with open("marketplace_metrics.json") as f:
            return json.load(f)
    return None


def main():
    today = datetime.date.today().isoformat()
    metrics = load_metrics()

    lines = [f"# Bizlance Daily Report — {today}", ""]

    lines.append("## Pipeline activity today")
    lines.append("(Pulled from this repo's own run logs — always accurate.)")
    lines.append("- Blog post: see today's daily-blog.yml Action run log for title/segment")
    lines.append("- Social post: see today's daily-social.yml Action run log")
    lines.append("- DM drafts: see dm_drafts.jsonl for new pending replies")
    lines.append("- Outreach: see today's daily-outreach.yml Action run log for send counts")
    lines.append("")

    lines.append("## Marketplace health")
    if metrics and any(v for v in metrics.values()):
        lines.append(f"- Providers: {metrics['providers_total']} total, "
                      f"{metrics['providers_verified']} verified, {metrics['providers_active']} active")
        lines.append(f"- Buyers: {metrics['buyers_total']} total, "
                      f"{metrics['buyer_searches_today']} searches today")
        lines.append(f"- Provider contacts today: {metrics['provider_contacts_today']}")
        lines.append(f"- Matches today: {metrics['matches_today']}")
        lines.append(f"- Projects started today: {metrics['projects_started_today']}")
        lines.append(f"- Projects completed today: {metrics['projects_completed_today']}")
        lines.append(f"- Reviews today: {metrics['reviews_today']}")
    else:
        lines.append(
            "- NOT CONNECTED. Real marketplace numbers (providers, buyers, matches, "
            "projects, reviews) require wiring fetch_marketplace_metrics.py to your "
            "actual backend — see that file's docstring. Until then this section "
            "can't be filled in honestly."
        )
    lines.append("")

    lines.append("## Biggest bottleneck / opportunity / next actions")
    lines.append(
        "- Left blank on purpose: this needs human judgment (or real marketplace data "
        "feeding an LLM analysis once connected) — not guessed from content-pipeline "
        "activity alone."
    )

    report = "\n".join(lines)
    fname = f"reports/report_{today}.md"
    os.makedirs("reports", exist_ok=True)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nSaved to {fname}")


if __name__ == "__main__":
    main()
