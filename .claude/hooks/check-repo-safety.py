#!/usr/bin/env python3
"""
PreToolUse Hook — Specifically for `git clone` commands.
Uses the `if: "Bash(git clone *)"` filter.

Always blocks the clone (exit 2). If it's a GitHub repo, first calls
the GitHub API to fetch stars, forks, last commit, size, etc., and
includes that analysis in the block message so Claude can relay it to the user.
"""

import json
import sys
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

input_data = json.loads(sys.stdin.read())
command = input_data.get("tool_input", {}).get("command", "")

if not command:
    sys.exit(0)

# ── Extract repo URL ────────────────────────────────────────
url_match = re.search(r"git\s+clone\s+(?:--[^\s]+\s+)*(\S+)", command)
if not url_match:
    sys.exit(0)

repo_url = url_match.group(1).rstrip("/").rstrip(".git")

# ── Try GitHub API ──────────────────────────────────────────
github_match = re.search(r"github\.com[/:]([^/]+)/([^/\s.]+)", repo_url)
repo_info = None

if github_match:
    owner = github_match.group(1)
    repo  = github_match.group(2)
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        req = urllib.request.Request(api_url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-code-safety-hook"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

            pushed_at = data.get("pushed_at", "")
            days_since_push = "unknown"
            if pushed_at:
                try:
                    push_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    delta = datetime.now(timezone.utc) - push_date
                    days_since_push = f"{delta.days} days ago"
                except Exception:
                    days_since_push = pushed_at

            repo_info = {
                "name":        data.get("full_name", f"{owner}/{repo}"),
                "description": data.get("description", "No description"),
                "stars":       data.get("stargazers_count", "?"),
                "forks":       data.get("forks_count", "?"),
                "open_issues": data.get("open_issues_count", "?"),
                "last_push":   days_since_push,
                "archived":    data.get("archived", False),
                "license":     (data.get("license") or {}).get("spdx_id", "None"),
                "size_kb":     data.get("size", "?"),
            }
    except urllib.error.HTTPError as e:
        repo_info = {"error": f"GitHub API returned {e.code}"}
    except Exception as e:
        repo_info = {"error": f"Could not reach GitHub API: {str(e)}"}

# ── Build block message ─────────────────────────────────────
lines = [
    f"GIT CLONE BLOCKED: {repo_url}",
    "",
    "You must NOT clone repositories. Share this analysis with the user:",
    "",
]

if repo_info and "error" not in repo_info:
    size_kb = repo_info['size_kb']
    size_str = f"~{size_kb / 1024:.1f} MB" if isinstance(size_kb, (int, float)) else "unknown"
    lines += [
        f"Repository Analysis for {repo_info['name']}:",
        f"  Description : {repo_info['description']}",
        f"  Stars       : {repo_info['stars']}",
        f"  Forks       : {repo_info['forks']}",
        f"  Open issues : {repo_info['open_issues']}",
        f"  Last push   : {repo_info['last_push']}",
        f"  License     : {repo_info['license']}",
        f"  Size        : {size_str}",
        f"  Archived    : {'YES (no longer maintained)' if repo_info['archived'] else 'No'}",
    ]
    stars = repo_info["stars"]
    if isinstance(stars, int):
        if stars < 10:
            lines.append("  WARNING: LOW STAR COUNT — repo may be untrusted or unmaintained")
        elif stars < 100:
            lines.append("  NOTE: Moderate star count — review before using")
        else:
            lines.append("  OK: Good star count")
    if repo_info.get("archived"):
        lines.append("  WARNING: ARCHIVED — no longer maintained")

elif repo_info and "error" in repo_info:
    lines.append(f"  Could not fetch repo info: {repo_info['error']}")
    lines.append("  Tell the user to verify the repository manually.")
else:
    lines.append("  Non-GitHub repo — cannot auto-analyze.")
    lines.append("  Tell the user to check the repo's health manually.")

lines += [
    "",
    "Tell the user to:",
    f"  1. Review the analysis above",
    f"  2. Clone it themselves:  {command}",
    "  3. Say 'done' or 'cloned' when it's in the project directory",
]

sys.stderr.write("\n".join(lines) + "\n")
sys.exit(2)
