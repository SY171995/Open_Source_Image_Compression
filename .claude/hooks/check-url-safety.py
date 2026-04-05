#!/usr/bin/env python3
"""
PreToolUse Hook — Specifically for curl commands.
Uses the `if: "Bash(curl *)"` filter so this only fires on curl commands.

Logic:
  - curl for API calls (JSON responses, no -o/-O) → ALLOWED
  - curl that saves to a file (-o, -O, >, --output) → BLOCKED (exit 2)
  - curl piped to bash/sh → BLOCKED (exit 2)
  - curl to untrusted domains → stderr warning, allowed
"""

import json
import sys
import re
from urllib.parse import urlparse

input_data = json.loads(sys.stdin.read())
command = input_data.get("tool_input", {}).get("command", "")

if not command:
    sys.exit(0)

TRUSTED_API_DOMAINS = {
    "api.github.com", "api.openai.com", "api.anthropic.com",
    "registry.npmjs.org", "pypi.org", "crates.io",
    "api.stripe.com", "api.twilio.com",
    "jsonplaceholder.typicode.com",
}

DOWNLOAD_INDICATORS = [
    (r"-[a-zA-Z]*[oO]\s+",              "curl -o/-O saves to a file"),
    (r"--output\s+",                     "curl --output saves to a file"),
    (r">\s*\S+",                         "curl output redirected to a file"),
    (r"\|\s*tar\b",                      "curl piped to tar (extracting download)"),
    (r"\|\s*gunzip\b",                   "curl piped to gunzip"),
    (r"\|\s*(?:sudo\s+)?(?:bash|sh|zsh)\b", "curl piped to shell — remote code execution"),
    (r"\|\s*python",                     "curl piped to python interpreter"),
    (r"--remote-name",                   "curl --remote-name saves to a file"),
]

for pattern, reason in DOWNLOAD_INDICATORS:
    if re.search(pattern, command, re.IGNORECASE):
        urls = re.findall(r"https?://\S+", command)
        url_str = ', '.join(urls) if urls else 'unknown'
        sys.stderr.write(
            f"CURL DOWNLOAD BLOCKED: {reason}.\n"
            f"URL(s): {url_str}\n\n"
            "curl for reading API responses is fine, but saving files "
            "from the internet is not allowed. Tell the user to:\n"
            "1. Review the URL and what it contains\n"
            "2. Download it themselves: provide the exact curl command\n"
            "3. Say 'done' when the file is in the project directory\n"
        )
        sys.exit(2)

# Non-blocking domain warning
urls = re.findall(r"https?://[^\s'\"]+", command)
for url in urls:
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        if domain and domain not in TRUSTED_API_DOMAINS:
            sys.stderr.write(
                f"curl to non-trusted domain: {domain}\n"
                "Proceeding (API call, not download), but verify this is intended.\n"
            )
    except Exception:
        pass

sys.exit(0)
