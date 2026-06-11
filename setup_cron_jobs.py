"""
One-time setup: creates 3 cron-job.org jobs that trigger GitHub Actions
workflows at exact IST times every weekday.

Run via the setup_cron.yml GitHub Actions workflow.
"""
import os
import json
import requests
import sys

CRONJOB_API  = "https://api.cron-job.org"
REPO         = "stockzdoctors/stock-market-bot"
GITHUB_API   = f"https://api.github.com/repos/{REPO}/actions/workflows"

cronjob_key  = os.environ["CRONJOB_API_KEY"]
gh_pat       = os.environ["GH_DISPATCH_TOKEN"]

JOBS = [
    {
        "title":    "StockBot — Morning Alert (9:20 AM IST)",
        "url":      f"{GITHUB_API}/morning_alert.yml/dispatches",
        "hours":    [3],
        "minutes":  [50],
    },
    {
        "title":    "StockBot — Breakout Alert (9:32 AM IST)",
        "url":      f"{GITHUB_API}/breakout.yml/dispatches",
        "hours":    [4],
        "minutes":  [2],
    },
    {
        "title":    "StockBot — EOD Report (4:00 PM IST)",
        "url":      f"{GITHUB_API}/eod.yml/dispatches",
        "hours":    [10],
        "minutes":  [30],
    },
]

headers = {
    "Authorization": f"Bearer {cronjob_key}",
    "Content-Type":  "application/json",
}

# Delete any existing StockBot jobs first to avoid duplicates
print("Checking for existing StockBot jobs...")
r = requests.get(f"{CRONJOB_API}/jobs", headers=headers, timeout=15)
if r.status_code == 200:
    existing = r.json().get("jobs", [])
    for job in existing:
        if "StockBot" in job.get("title", ""):
            jid = job["jobId"]
            requests.delete(f"{CRONJOB_API}/jobs/{jid}", headers=headers, timeout=15)
            print(f"  Deleted old job: {job['title']}")

# Create the 3 jobs
print("\nCreating cron jobs...")
for job in JOBS:
    payload = {
        "job": {
            "url":           job["url"],
            "title":         job["title"],
            "enabled":       True,
            "saveResponses": True,
            "schedule": {
                "timezone": "UTC",
                "hours":    job["hours"],
                "minutes":  job["minutes"],
                "mdays":    [-1],
                "months":   [-1],
                "wdays":    [1, 2, 3, 4, 5],  # Mon–Fri
            },
            "requestMethod": 1,  # POST
            "extendedData": {
                "headers": {
                    "Authorization":  f"Bearer {gh_pat}",
                    "Content-Type":   "application/json",
                    "Accept":         "application/vnd.github+json",
                },
                "body": json.dumps({"ref": "main"}),
            },
        }
    }

    r = requests.put(
        f"{CRONJOB_API}/jobs",
        headers=headers,
        json=payload,
        timeout=15,
    )
    if r.status_code in (200, 201):
        jid = r.json().get("jobId", "?")
        utc_time = f"{job['hours'][0]:02d}:{job['minutes'][0]:02d} UTC"
        print(f"  ✅ Created: {job['title']}  (job ID: {jid}, runs at {utc_time})")
    else:
        print(f"  ❌ Failed: {job['title']} — {r.status_code}: {r.text[:200]}")
        sys.exit(1)

print("\n✅ All 3 cron jobs created on cron-job.org!")
print("Alerts will fire at exact times every weekday:")
print("  9:20 AM IST — Morning Market Pulse")
print("  9:32 AM IST — 15-min Breakout Signals")
print("  4:00 PM IST — EOD Performance Report")
