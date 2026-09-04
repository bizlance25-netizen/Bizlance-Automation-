"""
fetch_marketplace_metrics.py — pulls real marketplace numbers (providers, buyers,
matches, projects, reviews) so the daily/weekly report can be about actual business
health, not just "how much content did we publish."

IMPORTANT — this cannot work until you configure it:
I don't have any existing connection to Bizlance's actual product database or
analytics. This script expects your backend to expose a simple JSON endpoint (or you
adapt the fetch_from_api() function below to query your database directly). Until
BIZLANCE_METRICS_API_URL is set, this script returns all-zero placeholder metrics
and prints a warning — it will NOT silently fabricate numbers.

Two ways to wire this up for real, pick whichever matches your stack:

OPTION A — REST endpoint (simplest):
  Expose one authenticated endpoint on your own backend, e.g.
  GET https://bizlance.online/api/internal/metrics
  returning JSON: {"providers_total": int, "providers_verified": int,
  "providers_active": int, "buyers_total": int, "buyer_searches_today": int,
  "provider_contacts_today": int, "matches_today": int, "projects_started_today": int,
  "projects_completed_today": int, "reviews_today": int}
  Set secrets: BIZLANCE_METRICS_API_URL, BIZLANCE_METRICS_API_KEY

OPTION B — direct database query:
  If Bizlance's data lives in a Postgres/MySQL DB you can reach from GitHub Actions
  (e.g. via a connection string secret), replace fetch_from_api() with a real query.
  Ask Claude Code to fill this in once you share your schema — it's a 10-minute change,
  not a rebuild.
"""
import os
import sys
import json
import requests

METRIC_KEYS = [
    "providers_total", "providers_verified", "providers_active",
    "buyers_total", "buyer_searches_today", "provider_contacts_today",
    "matches_today", "projects_started_today", "projects_completed_today",
    "reviews_today",
]


def fetch_from_api() -> dict:
    url = os.environ.get("BIZLANCE_METRICS_API_URL")
    key = os.environ.get("BIZLANCE_METRICS_API_KEY")

    if not url:
        print(
            "WARNING: BIZLANCE_METRICS_API_URL is not set. No real marketplace data "
            "source is connected yet — returning placeholder zeros. See the module "
            "docstring for how to connect your actual backend.",
            file=sys.stderr,
        )
        return {k: 0 for k in METRIC_KEYS}

    headers = {"Authorization": f"Bearer {key}"} if key else {}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return {k: data.get(k, 0) for k in METRIC_KEYS}


def main():
    metrics = fetch_from_api()
    with open("marketplace_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
