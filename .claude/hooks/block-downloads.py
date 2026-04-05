#!/usr/bin/env python3
"""
PreToolUse Hook — Block Bash commands that download from the internet.

Exit codes:
  - 0: command is safe, proceed
  - 2: BLOCKED — stderr message sent to Claude
"""

import json
import sys
import re
import os

# ── Config ──────────────────────────────────────────────────
BLOCK_ALL_PACKAGE_INSTALLS = os.environ.get("CLAUDE_HOOK_BLOCK_ALL_INSTALLS", "false").lower() == "true"

# ── Read hook input ─────────────────────────────────────────
input_data = json.loads(sys.stdin.read())
tool_name  = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command    = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(0)

# ── Download patterns ───────────────────────────────────────
DOWNLOAD_BLOCKLIST = [
    (r"\bwget\s+",                                          "wget downloads files from the internet"),
    (r"\bcurl\s+.*-[oO]\s+",                               "curl -o/-O saves files from the internet"),
    (r"\bcurl\s+.*--output\s+",                            "curl --output saves files from the internet"),
    (r"\bcurl\s+.*>\s*\S+",                                "curl redirecting output to a file"),
    (r"\bcurl\s+.*\|\s*(?:tar|gunzip|bunzip|sh|bash)",     "curl piping to extraction or execution"),
    # git remote ops (clone, pull, fetch, submodule) are handled by check-git-remotes.py
    (r"\bpip\s+install\s+https?://",                       "pip install from URL downloads from the internet"),
    (r"\bpip\s+install\s+git\+",                           "pip install from git repo downloads from the internet"),
    (r"\bnpm\s+install\s+https?://",                       "npm install from URL downloads from the internet"),
    (r"\bnpm\s+install\s+git[\+:]",                        "npm install from git downloads from the internet"),
    (r"\byarn\s+add\s+https?://",                          "yarn add from URL downloads from the internet"),
    (r"\bpnpm\s+add\s+https?://",                          "pnpm add from URL downloads from the internet"),
    (r"\bcargo\s+install\s+--git\b",                       "cargo install --git downloads from the internet"),
    (r"\bgo\s+install\s+\S+@",                             "go install downloads from the internet"),
    (r"\bgo\s+get\b",                                      "go get downloads modules from the internet"),
    (r"\bdocker\s+pull\b",                                 "docker pull downloads images from the internet"),
    (r"https?://\S+\.(?:zip|tar|gz|tgz|bz2|xz|exe|dmg|msi|deb|rpm|pkg|bin|iso|AppImage)\b",
     "URL points to a downloadable binary/archive"),
]

if BLOCK_ALL_PACKAGE_INSTALLS:
    DOWNLOAD_BLOCKLIST.extend([
        (r"\bpip\s+install\b",      "pip install downloads packages"),
        (r"\bnpm\s+install\b",      "npm install downloads packages"),
        (r"\byarn\s+add\b",         "yarn add downloads packages"),
        (r"\bpnpm\s+add\b",         "pnpm add downloads packages"),
        (r"\bapt-get\s+install\b",  "apt-get install downloads packages"),
        (r"\bbrew\s+install\b",     "brew install downloads packages"),
    ])

# ── Check command ───────────────────────────────────────────
for pattern, reason in DOWNLOAD_BLOCKLIST:
    if re.search(pattern, command, re.IGNORECASE):
        urls = re.findall(r"https?://\S+", command)
        url_info = f" (URL: {urls[0]})" if urls else ""
        sys.stderr.write(
            f"DOWNLOAD BLOCKED: {reason}{url_info}.\n\n"
            "You are not allowed to download files from the internet. "
            "Instead, do the following:\n"
            "1. Tell the user exactly what needs to be downloaded and from where.\n"
            "2. If it's a GitHub repo, suggest they check: stars, recent commits, "
            "open issues, and last release date.\n"
            "3. Mention the estimated size if known.\n"
            "4. Ask the user to download it manually, place it in the project, "
            "and say 'done' or 'downloaded' when ready.\n"
            "5. Wait for the user's confirmation before continuing.\n"
        )
        sys.exit(2)

sys.exit(0)
