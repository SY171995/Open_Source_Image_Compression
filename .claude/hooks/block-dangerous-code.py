#!/usr/bin/env python3
"""
PreToolUse Hook — Block dangerous code/syntax patterns in Bash commands.

Catches:
  - Destructive filesystem operations (rm -rf /)
  - Shell injection vectors (eval, exec with unsanitized input)
  - Hardcoded secrets being echoed/printed
  - Dangerous permission changes (chmod 777)
  - Network listeners that could expose the machine

Critical/High: exit 2 (blocked).
Medium: stderr warning, exit 0 (non-blocking).
"""

import json
import sys
import re

input_data = json.loads(sys.stdin.read())
tool_name  = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command    = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(0)

PATTERNS = [
    # CRITICAL
    ("critical", r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+/\s*$",
     "rm -rf / — would destroy the entire filesystem"),
    ("critical", r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+/[a-z]+\s*$",
     "rm -rf on a root-level directory — extremely dangerous"),
    ("critical", r"\bmkfs\b",
     "mkfs — formats a filesystem"),
    ("critical", r"\bdd\s+.*of=/dev/[sh]d",
     "dd writing to a block device"),
    ("critical", r">\s*/dev/[sh]d[a-z]",
     "redirecting output to a block device"),
    ("critical", r"\b:\(\)\s*\{\s*:\|\s*:\s*&\s*\}\s*;?\s*:",
     "fork bomb detected"),

    # HIGH
    ("high", r"\bchmod\s+777\b",
     "chmod 777 — overly permissive, use 755 or more restrictive"),
    ("high", r"\bchmod\s+-R\s+777\b",
     "recursive chmod 777 — extremely dangerous"),
    ("high", r"\beval\s+.*\$",
     "eval with variable expansion — shell injection risk"),
    ("high", r"\bsudo\s+rm\b",
     "sudo rm — elevated deletion is risky"),
    ("high", r"\bsudo\s+chmod\b",
     "sudo chmod — elevated permission change is risky"),
    ("high", r"(?:password|secret|api_key|token|private_key)\s*=\s*['\"][^'\"]{8,}['\"]",
     "hardcoded secret in command — never put secrets in commands"),
    ("high", r"\becho\s+.*(?:password|secret|api_key|token)=",
     "echoing secrets — they'll appear in logs and history"),

    # MEDIUM
    ("medium", r"\bcurl\s+.*\|\s*(?:sudo\s+)?(?:bash|sh|zsh)\b",
     "curl | bash — executing remote code without review"),
    ("medium", r"\bpython3?\s+-c\s+['\"].*(?:import\s+os|subprocess|exec|eval)",
     "inline python with dangerous imports"),
    ("medium", r"\b0\.0\.0\.0\b",
     "binding to all interfaces — may expose services"),
    ("medium", r"\bnc\s+-[a-zA-Z]*l",
     "netcat listener — opens a network port"),
]

findings = []
max_severity = "medium"

for severity, pattern, reason in PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        findings.append((severity, reason))
        if severity == "critical":
            max_severity = "critical"
        elif severity == "high" and max_severity != "critical":
            max_severity = "high"

if not findings:
    sys.exit(0)

if max_severity in ("critical", "high"):
    reasons = "\n".join(f"  [{s.upper()}] {r}" for s, r in findings)
    sys.stderr.write(
        f"DANGEROUS COMMAND BLOCKED:\n{reasons}\n\n"
        "This command has been blocked for safety. "
        "If the user needs this operation, suggest a safer alternative "
        "or ask the user to run it manually after reviewing the risk.\n"
    )
    sys.exit(2)
else:
    reasons = "\n".join(f"  [{s.upper()}] {r}" for s, r in findings)
    sys.stderr.write(
        f"Safety warning (non-blocking):\n{reasons}\n"
        "Proceeding, but review this command carefully.\n"
    )
    sys.exit(0)
