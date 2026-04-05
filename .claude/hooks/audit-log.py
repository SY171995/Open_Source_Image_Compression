#!/usr/bin/env python3
"""
PostToolUse Hook — Audit log every Bash command that executed.

Records: timestamp, session_id, command, cwd, output preview (truncated).
Writes to .claude/logs/bash-audit.jsonl
Non-blocking (always exits 0).
"""

import json
import sys
import os
from datetime import datetime, timezone

input_data = json.loads(sys.stdin.read())

tool_name = input_data.get("tool_name", "")
if tool_name != "Bash":
    sys.exit(0)

tool_input  = input_data.get("tool_input", {})
tool_output = input_data.get("tool_output", "")

if isinstance(tool_output, str) and len(tool_output) > 500:
    tool_output = tool_output[:500] + "...[truncated]"

log_entry = {
    "timestamp":      datetime.now(timezone.utc).isoformat(),
    "event":          "PostToolUse",
    "session_id":     input_data.get("session_id", "unknown"),
    "command":        tool_input.get("command", ""),
    "cwd":            input_data.get("cwd", ""),
    "output_preview": tool_output,
}

log_dir = os.path.join(
    os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()),
    ".claude", "logs"
)
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "bash-audit.jsonl")
with open(log_file, "a") as f:
    f.write(json.dumps(log_entry) + "\n")

sys.exit(0)
