#!/usr/bin/env python3
"""
AM Weekly Briefing — ScaleOps
Runs every Sunday at 9am via GitHub Actions cron.
Calls Claude API and prints the briefing to stdout (visible in GitHub Actions logs).
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
    sys.exit(1)

now = datetime.now(timezone.utc)
today = now.strftime("%Y-%m-%d")
prev_month = now.replace(day=1)
# Go back one month
if prev_month.month == 1:
    prev_month = prev_month.replace(year=prev_month.year - 1, month=12)
else:
    prev_month = prev_month.replace(month=prev_month.month - 1)
prev_month_str = prev_month.strftime("%B %Y")

payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 8000,
    "system": (
        "You are an Account Manager assistant for ScaleOps. "
        "Generate a complete weekly briefing for the following customers: "
        "SentinelOne, Temenos, Epic Games. "
        "For each customer cover: "
        "1) Financial summary (ARR, committed plan, actual usage, overusage charge), "
        "2) Issues identified (OOM, evictions, unschedulable pods), "
        "3) Expansion opportunities (from Gong calls, Slack, web signals including GPU), "
        "4) External signals (news, engineering blogs, LinkedIn posts). "
        "End with a prioritized action items table. Be concise and data-driven."
    ),
    "messages": [
        {
            "role": "user",
            "content": (
                f"Génère mon briefing hebdomadaire complet pour SentinelOne, Temenos et Epic Games. "
                f"Aujourd'hui nous sommes le {today}. "
                f"Le mois précédent est {prev_month_str}."
            )
        }
    ]
}

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    method="POST"
)

print(f"=== AM Weekly Briefing — ScaleOps ({today}) ===\n")

with urllib.request.urlopen(req, timeout=180) as resp:
    result = json.loads(resp.read().decode("utf-8"))

briefing = ""
for block in result.get("content", []):
    if block.get("type") == "text":
        briefing += block["text"]

print(briefing)
