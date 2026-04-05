#!/usr/bin/env python3
"""
UserPromptSubmit Hook — Scans user prompt BEFORE Claude processes it.

Checks:
  1. Is the user asking to download something from the internet?
  2. Is the user asking to transfer/upload a file over the network?
  3. Does the prompt contain dangerous code patterns?

Behavior:
  - Exit 0 + additionalContext → inject safety guidance into Claude's context
  - Exit 2 → block the prompt entirely (used for extreme cases)

This hook does NOT block — it injects context so Claude knows the rules.
The PreToolUse hooks handle the actual blocking.
"""

import json
import sys
import re

# ── Read hook input from stdin ──────────────────────────────
input_data = json.loads(sys.stdin.read())
prompt = input_data.get("prompt", "")

findings = []

# ── 1. Detect download intent ──────────────────────────────
DOWNLOAD_PATTERNS = [
    (r"\bdownload\s+(?:this|that|the|a|from|it)\b", "download request"),
    (r"\bfetch\s+(?:this|that|the|a|from)\b", "fetch request"),
    (r"\bpull\s+(?:down|from)\b", "pull request"),
    (r"\bgit\s+clone\b", "git clone"),
    (r"\bwget\b", "wget command"),
    (r"\bcurl\s+.*-[oO]\b", "curl download"),
    (r"\bpip\s+install\s+https?://", "pip install from URL"),
    (r"\bnpm\s+install\s+https?://", "npm install from URL"),
    (r"\bcargo\s+install\s+--git\b", "cargo install from git"),
    (r"\bgo\s+install\s+\S+@", "go install from remote"),
    (r"https?://\S+\.(?:zip|tar|gz|exe|dmg|msi|deb|rpm|pkg|bin|iso|AppImage)\b", "binary URL"),
    (r"https?://\S+/releases/", "release URL"),
    (r"https?://\S+/download", "download URL"),
    (r"\binstall\s+.*from\s+(?:the\s+)?(?:internet|web|url|github|npm|pip)\b", "install from internet"),
]

for pattern, label in DOWNLOAD_PATTERNS:
    if re.search(pattern, prompt, re.IGNORECASE):
        findings.append(("download", label))

# ── 2. Detect file transfer intent ─────────────────────────
TRANSFER_PATTERNS = [
    (r"\bupload\s+(?:this|that|the|a|to|it)\b", "upload request"),
    (r"\bsend\s+(?:this|that|the|a)\s+(?:file|data|report|log)\b", "send file"),
    (r"\btransfer\s+(?:this|that|the|a)\s+(?:file|data)\b", "transfer file"),
    (r"\bpush\s+to\s+(?:s3|gcs|azure|bucket|server|remote|cloud)\b", "push to cloud"),
    (r"\bscp\b", "scp command"),
    (r"\brsync\b.*@", "rsync to remote"),
    (r"\baws\s+s3\s+(?:cp|mv|sync)\b", "AWS S3 transfer"),
    (r"\bgsutil\s+cp\b", "GCS transfer"),
    (r"\bdeploy\s+(?:this|the|to)\b", "deploy request"),
]

for pattern, label in TRANSFER_PATTERNS:
    if re.search(pattern, prompt, re.IGNORECASE):
        findings.append(("transfer", label))

# ── 3. Detect dangerous code patterns ──────────────────────
DANGER_PATTERNS = [
    (r"\brm\s+-rf\s+/", "rm -rf / (catastrophic delete)"),
    (r"\beval\s*\(", "eval() usage"),
    (r"\bexec\s*\(", "exec() usage"),
    (r"\bos\.system\s*\(", "os.system() call"),
    (r"\b(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded secret"),
]

for pattern, label in DANGER_PATTERNS:
    if re.search(pattern, prompt, re.IGNORECASE):
        findings.append(("danger", label))


# ── Build output ────────────────────────────────────────────
if not findings:
    sys.exit(0)

urls = re.findall(r"https?://\S+", prompt)

context_parts = []

download_findings = [f for f in findings if f[0] == "download"]
transfer_findings = [f for f in findings if f[0] == "transfer"]
danger_findings   = [f for f in findings if f[0] == "danger"]

if download_findings:
    context_parts.append(
        "SAFETY HOOK: The user's prompt contains a DOWNLOAD request "
        f"(detected: {', '.join(f[1] for f in download_findings)}). "
        "You MUST NOT download anything yourself. Instead:\n"
        "1. Analyze the URL/resource (check if domain is trusted, check file extension)\n"
        "2. If it's a GitHub repo, tell the user to check stars, recent commits, and open issues\n"
        "3. Estimate the file size if possible\n"
        "4. Tell the user: 'Please download this yourself, place it in the project directory, "
        "and tell me when it's done. I'll continue from there.'\n"
        "5. Do NOT run wget, curl -O, git clone, or any download command."
    )
    if urls:
        context_parts.append(f"URLs detected in prompt: {', '.join(urls)}")

if transfer_findings:
    context_parts.append(
        "SAFETY HOOK: The user's prompt contains a FILE TRANSFER request "
        f"(detected: {', '.join(f[1] for f in transfer_findings)}). "
        "You MUST NOT transfer files over the network yourself. Instead:\n"
        "1. Prepare the file(s) locally if needed\n"
        "2. Tell the user: 'Please transfer this file yourself using your preferred method, "
        "and tell me when it's done. I'll continue from there.'\n"
        "3. Do NOT run scp, rsync, aws s3 cp, or any upload/transfer command."
    )

if danger_findings:
    context_parts.append(
        "SAFETY HOOK: The user's prompt contains DANGEROUS CODE patterns "
        f"(detected: {', '.join(f[1] for f in danger_findings)}). "
        "Review carefully before executing. Avoid running destructive or "
        "injection-prone commands. Suggest safer alternatives."
    )

output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "\n\n".join(context_parts)
    }
}

print(json.dumps(output))
sys.exit(0)
