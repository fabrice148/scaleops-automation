#!/usr/bin/env python3
"""
AM Weekly Briefing — ScaleOps
Runs every Sunday at 9am via GitHub Actions cron.
Calls Claude API and sends the briefing as a Slack DM via webhook.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
    sys.exit(1)

if not SLACK_WEBHOOK_URL:
    print("ERROR: SLACK_WEBHOOK_URL environment variable is not set.")
    sys.exit(1)

now = datetime.now(timezone.utc)
today = now.strftime("%Y-%m-%d")
prev_month = now.replace(day=1)
if prev_month.month == 1:
    prev_month = prev_month.replace(year=prev_month.year - 1, month=12)
else:
    prev_month = prev_month.replace(month=prev_month.month - 1)
prev_month_str = prev_month.strftime("%B %Y")

# Call Claude API
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

print(f"Calling Claude API...")
with urllib.request.urlopen(req, timeout=180) as resp:
    result = json.loads(resp.read().decode("utf-8"))

briefing = ""
for block in result.get("content", []):
    if block.get("type") == "text":
        briefing += block["text"]

print("Briefing generated. Sending to Slack...")

# Slack has a 4000 char limit per block — split if needed
MAX_LEN = 3900
header = f"*📊 AM Weekly Briefing — ScaleOps ({today})*\n\n"
full_message = header + briefing

chunks = []
if len(full_message) <= MAX_LEN:
    chunks = [full_message]
else:
    chunks.append(full_message[:MAX_LEN])
    rest = full_message[MAX_LEN:]
    while rest:
        chunks.append(rest[:MAX_LEN])
        rest = rest[MAX_LEN:]

for i, chunk in enumerate(chunks):
    slack_payload = {"text": chunk}
    slack_req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps(slack_payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(slack_req, timeout=30) as slack_resp:
        slack_resp.read()
    print(f"Slack message {i+1}/{len(chunks)} sent.")

print("Done.")
