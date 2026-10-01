#!/usr/bin/env python3
"""Send a published issue once through the Mac's configured Mail app."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
issue_date = sys.argv[1]
issue = json.loads((ROOT / "issues" / f"{issue_date}.json").read_text())
text_file = ROOT / "outbox" / f"{issue_date}.txt"
sent_marker = ROOT / "outbox" / f"{issue_date}.sent"
if sent_marker.exists():
    raise SystemExit("This issue was already sent.")
if not text_file.exists():
    raise SystemExit("Render the issue first with scripts/publish.py.")
recipient = os.environ.get("LAI_RECIPIENT", "").strip()
if not recipient or "@" not in recipient:
    raise SystemExit("Set LAI_RECIPIENT to the email address selected by the user.")
subject = "A LAI que pegou · " + issue["headline"]
subprocess.run(["osascript", str(ROOT / "scripts" / "send_email.applescript"), recipient, subject, str(text_file)], check=True)
sent_marker.write_text(recipient + "\n")
print("Issue sent to " + recipient)
