#!/usr/bin/env python3
"""
PreToolUse Hook — Git remote operation whitelist.

Local git operations (commit, log, status, diff, branch, add, etc.) are allowed freely.

Remote operations (clone, push, pull, fetch, submodule add) are blocked unless
the remote URL is listed in allowed-git-remotes.txt.

Named remotes (e.g. "origin") are resolved to their URLs via .git/config.

allowed-git-remotes.txt format (one per line, no protocol, no .git suffix):
  github.com/myorg/myrepo
  github.com/myorg/another-repo
"""

import json
import sys
import re
import os
import configparser

# ── Read input ───────────────────────────────────────────────
input_data = json.loads(sys.stdin.read())
command    = input_data.get("tool_input", {}).get("command", "")
cwd        = input_data.get("cwd", os.getcwd())

if not command:
    sys.exit(0)

# ── Only process git commands ────────────────────────────────
git_match = re.match(r'^\s*git\s+(\S+)(.*)', command, re.IGNORECASE | re.DOTALL)
if not git_match:
    sys.exit(0)

op   = git_match.group(1).lower()
args = git_match.group(2).strip()

# ── Remote operations to intercept ──────────────────────────
REMOTE_OPS = {'clone', 'push', 'pull', 'fetch', 'submodule'}
if op not in REMOTE_OPS:
    sys.exit(0)  # Local operation — allow freely

# ── For submodule update without --remote, allow (local op) ──
if op == 'submodule':
    tokens = args.split()
    sub_op = tokens[0] if tokens else ''
    if sub_op == 'update' and '--remote' not in tokens:
        sys.exit(0)  # Local submodule update — no network involved

# ── Load whitelist ───────────────────────────────────────────
script_dir    = os.path.dirname(os.path.abspath(__file__))
whitelist_file = os.path.join(script_dir, "allowed-git-remotes.txt")

allowed_remotes = set()
if os.path.exists(whitelist_file):
    with open(whitelist_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                allowed_remotes.add(line.lower())

# ── Helpers ──────────────────────────────────────────────────
def normalize_url(url):
    """Strip protocol, credentials, and .git suffix for comparison."""
    url = url.strip()
    # git@github.com:org/repo.git → github.com/org/repo
    url = re.sub(r'^git@([^:]+):', r'\1/', url)
    # Strip protocol
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^git://', '', url)
    url = re.sub(r'^ssh://', '', url)
    # Strip credentials (user:pass@host → host)
    url = re.sub(r'^[^@]+@', '', url)
    # Strip .git suffix and trailing slash
    url = re.sub(r'\.git$', '', url)
    url = url.rstrip('/')
    return url.lower()

def resolve_named_remote(remote_name, cwd):
    """Look up a named remote in .git/config and return its URL."""
    git_config = os.path.join(cwd, '.git', 'config')
    if not os.path.exists(git_config):
        return None
    config = configparser.ConfigParser()
    config.read(git_config)
    section = f'remote "{remote_name}"'
    if section in config:
        return config[section].get('url')
    return None

def extract_remote_url(op, args, cwd):
    """Extract and resolve the remote URL from the git command."""
    # Strip flags (tokens starting with -)
    tokens = [t for t in args.split() if not t.startswith('-')]

    if op == 'clone':
        # git clone <url> [dir] [-- ...]
        raw = tokens[0] if tokens else None

    elif op in ('push', 'pull', 'fetch'):
        # git push [remote_or_url] [refspec]
        # If no remote specified, default is 'origin'
        raw = tokens[0] if tokens else 'origin'

    elif op == 'submodule':
        # git submodule add <url> [path]
        # git submodule update --remote (already allowed-checked above)
        raw = tokens[1] if len(tokens) > 1 else None

    else:
        return None

    if not raw:
        return None

    # If it's already a URL, return normalized
    if re.match(r'https?://|git@|git://|ssh://', raw):
        return normalize_url(raw)

    # Otherwise it's a named remote — resolve from .git/config
    resolved = resolve_named_remote(raw, cwd)
    if resolved:
        return normalize_url(resolved)

    # Could not resolve — return the raw name as-is for error message
    return raw

# ── Check ────────────────────────────────────────────────────
remote_url = extract_remote_url(op, args, cwd)

if remote_url is None:
    # Can't determine remote — block to be safe
    sys.stderr.write(
        f"GIT REMOTE BLOCKED: Could not determine remote URL for: {command}\n"
        "Cannot verify the remote against the whitelist.\n"
        "Add the remote URL to .claude/hooks/allowed-git-remotes.txt to allow it.\n"
    )
    sys.exit(2)

if remote_url in allowed_remotes:
    sys.exit(0)  # Whitelisted — allow

# ── Not whitelisted — block ──────────────────────────────────
sys.stderr.write(
    f"GIT REMOTE BLOCKED: '{remote_url}' is not in the allowed remotes list.\n\n"
    f"Command attempted: {command}\n\n"
    "To allow this remote, add it to .claude/hooks/allowed-git-remotes.txt:\n"
    f"  {remote_url}\n\n"
    "Then ask the user to run the git command manually and notify you when done.\n"
)
sys.exit(2)
