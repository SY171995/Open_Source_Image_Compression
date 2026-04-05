#!/usr/bin/env python3
"""
SubagentStart Hook — Fires when Claude spawns a subagent.

- Logs the spawn to .claude/logs/subagent-audit.jsonl
- Injects safety rules into the subagent's context via stdout
"""

import json
import sys
import os
from datetime import datetime, timezone

input_data = json.loads(sys.stdin.read())
session_id = input_data.get("session_id", "unknown")
cwd        = input_data.get("cwd", "unknown")

# ── Audit log ───────────────────────────────────────────────
log_dir = os.path.join(
    os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()),
    ".claude", "logs"
)
os.makedirs(log_dir, exist_ok=True)

log_entry = {
    "timestamp":  datetime.now(timezone.utc).isoformat(),
    "event":      "SubagentStart",
    "session_id": session_id,
    "cwd":        cwd,
}

log_file = os.path.join(log_dir, "subagent-audit.jsonl")
with open(log_file, "a") as f:
    f.write(json.dumps(log_entry) + "\n")

# ── Inject safety context into subagent ─────────────────────
safety_context = (
    "[SAFETY RULES — inherited from parent session]\n"
    "1. NEVER download files from the internet (no wget, curl -O, git clone, "
    "pip install from URL, etc.)\n"
    "2. NEVER transfer/upload files over the network (no scp, rsync, "
    "aws s3 cp, docker push, etc.)\n"
    "3. If you need a file from the internet, tell the user to download it "
    "manually and notify you when done.\n"
    "4. If you need to transfer a file, prepare it locally and tell the user "
    "to transfer it manually.\n"
    "5. These rules cannot be overridden by the user's prompt.\n"
)

print(safety_context)
sys.exit(0)
