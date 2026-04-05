#!/usr/bin/env python3
"""
PreToolUse Hook — Block Bash commands that transfer files over the network.

Exit 0: allowed.
Exit 2: BLOCKED — stderr message sent to Claude.
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

# ── Transfer patterns ───────────────────────────────────────
TRANSFER_BLOCKLIST = [
    (r"\bscp\s+",                                               "scp transfers files over the network"),
    (r"\bsftp\s+",                                             "sftp transfers files over the network"),
    (r"\bftp\s+.*put\b",                                       "ftp put uploads files"),
    (r"\brsync\s+.*\S+@\S+:",                                  "rsync to remote host transfers files over the network"),
    (r"\baws\s+s3\s+(?:cp|mv|sync)\b",                         "AWS S3 cp/mv/sync transfers files to cloud"),
    (r"\baws\s+s3api\s+put-object\b",                          "AWS S3 put-object uploads files"),
    (r"\bgsutil\s+(?:cp|mv|rsync)\b",                          "gsutil transfers files to GCS"),
    (r"\bgcloud\s+storage\s+cp\b",                             "gcloud storage cp transfers files"),
    (r"\baz\s+storage\s+blob\s+upload\b",                      "Azure blob upload transfers files"),
    (r"\bazcopy\s+",                                           "azcopy transfers files to Azure"),
    (r"\bcurl\s+.*-X\s*POST\s+.*(?:-d\s*@|-F\s+)",            "curl POST with file data uploads files"),
    (r"\bcurl\s+.*(?:--upload-file|--data-binary\s*@)",        "curl upload transfers files"),
    (r"\brequests\.(?:post|put)\s*\(.*files\s*=",              "Python requests upload transfers files"),
    (r"\bfetch\s*\(.*method:\s*['\"](?:POST|PUT)['\"].*(?:body|formData)", "fetch POST/PUT may transfer files"),
    (r"\bdocker\s+push\b",                                     "docker push uploads images to a registry"),
    # git push is handled by check-git-remotes.py
    (r"\bnc\s+.*<",                                            "netcat sending data over network"),
    (r"\b(?:ncat|netcat)\s+",                                  "netcat may transfer data over network"),
]

for pattern, reason in TRANSFER_BLOCKLIST:
    if re.search(pattern, command, re.IGNORECASE):
        sys.stderr.write(
            f"FILE TRANSFER BLOCKED: {reason}.\n\n"
            "You are not allowed to transfer files over the network. "
            "Instead, do the following:\n"
            "1. Tell the user exactly what file needs to be transferred and where.\n"
            "2. Prepare the file locally if needed (e.g., zip it, format it).\n"
            "3. Provide the exact command the user should run themselves.\n"
            "4. Ask the user to perform the transfer manually and say "
            "'done' or 'transferred' when ready.\n"
            "5. Wait for the user's confirmation before continuing.\n"
        )
        sys.exit(2)

sys.exit(0)
