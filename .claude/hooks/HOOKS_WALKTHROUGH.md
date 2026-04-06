# Claude Code Hooks — Detailed Walkthrough

## Hook System Overview

Hooks are shell/Python scripts that Claude Code runs automatically at specific lifecycle events. They act as a security layer **around Claude's actions**, not inside Claude's thinking. There are 4 event types used here:

```
UserPromptSubmit → fires when you type a message (before Claude sees it)
PreToolUse       → fires before Claude runs a tool (Edit, Write, Bash, WebFetch)
PostToolUse      → fires after a tool completes
SubagentStart    → fires when Claude spawns a subagent
```

Exit codes are the key mechanism:
- `exit 0` → allow
- `exit 2` → **block** (Claude sees the stderr message as a constraint)

---

## 1. `user-prompt-safety.py` — UserPromptSubmit

**Event:** Fires on every message you type, before Claude processes it.

**What it does:** It scans your prompt for three classes of intent using regex patterns:

### Scan 1 — Download intent
Looks for words like `download`, `wget`, `git clone`, `curl -O`, `pip install https://...`, binary URLs (`.zip`, `.exe`, `.tar.gz`, `/releases/`, `/download`).

### Scan 2 — File transfer intent
Looks for `upload`, `scp`, `rsync @remote`, `aws s3 cp`, `deploy`, `send this file`, etc.

### Scan 3 — Dangerous code patterns
Looks for `rm -rf /`, `eval(`, `exec(`, `os.system(`, hardcoded secrets like `api_key = "abc123"`.

**What happens on a match:** It does **NOT block** (never exits 2). Instead it injects `additionalContext` — text prepended to Claude's context window telling Claude exactly what it's not allowed to do. This is the "soft nudge" layer; the PreToolUse hooks are the hard blockers.

**Example output injected:**
```
SAFETY HOOK: The user's prompt contains a DOWNLOAD request (detected: wget command).
You MUST NOT download anything yourself. Instead: tell the user to download it manually...
```

---

## 2. `protect-paths.sh` — PreToolUse on `Edit|Write`

**Event:** Fires before any file Edit or Write operation.

**What it does:**
1. Reads the `file_path` from the tool input JSON (via `jq`)
2. Loads `protected-paths.txt` — a list of relative paths that are read-only
3. Makes the file path absolute, then checks if it starts with any protected path

**Currently protected:** `TEST_EDIT/` (the `simd/`, `build/`, `doc/` examples are commented out)

**On match:** exits 2 with message:
```
Modification blocked: 'TEST_EDIT/' is a protected folder.
```

**Key detail:** It uses `[[ "$FILE_PATH" == "$PROTECTED"* ]]` — a prefix match, so protecting `simd/` blocks all files inside `simd/` recursively.

---

## 3. `block-downloads.py` — PreToolUse on `Bash`

**Event:** Fires before every Bash command.

**What it does:** Checks the command string against a blocklist of download patterns using regex:

| Pattern | Reason |
|---|---|
| `wget ` | Downloads files |
| `curl -o/-O` or `curl --output` | Saves to file |
| `curl ... > file` | Redirected output |
| `curl ... \| tar/bash` | Pipe to extraction/execution |
| `pip install https://` | Install from URL |
| `npm/yarn/pnpm install https://` | Same |
| `cargo install --git` | Rust from git |
| `go install pkg@version` or `go get` | Go modules |
| `docker pull` | Container images |
| URLs ending in `.zip`, `.exe`, `.tar.gz`, etc. | Binary/archive links |

**Optional strict mode:** Set `CLAUDE_HOOK_BLOCK_ALL_INSTALLS=true` env var to also block `pip install`, `npm install`, `apt-get install`, `brew install` even without a URL.

**On match:** exits 2, tells Claude to inform the user what to download and ask them to do it manually.

---

## 4. `block-transfers.py` — PreToolUse on `Bash`

**Event:** Fires before every Bash command (runs in parallel with block-downloads.py).

**What it does:** Blocks outbound file transfer commands:

| Pattern | Reason |
|---|---|
| `scp ` | SSH copy |
| `sftp ` | SSH file transfer |
| `ftp ... put` | FTP upload |
| `rsync ... user@host:` | Remote sync |
| `aws s3 cp/mv/sync` | S3 upload |
| `gsutil cp/mv/rsync` | GCS upload |
| `gcloud storage cp` | GCS via gcloud |
| `az storage blob upload` | Azure blob |
| `azcopy ` | Azure copy tool |
| `curl -X POST ... -d @file` | curl POST with file |
| `curl --upload-file` | curl upload |
| `docker push` | Push image to registry |
| `nc ... <` or `ncat` | netcat data exfil |

Note: `git push` is **intentionally excluded** here — it's handled by `check-git-remotes.py`.

---

## 5. `block-dangerous-code.py` — PreToolUse on `Bash`

**Event:** Fires before every Bash command (runs alongside the previous two).

**What it does:** Three-tier severity system:

### CRITICAL (exit 2, hard block):
- `rm -rf /` or `rm -rf /rootdir` — filesystem destruction
- `mkfs` — format a filesystem
- `dd of=/dev/sd*` — write to block device
- `> /dev/sda` — redirect to block device
- `: () { : | : & } ; :` — fork bomb

### HIGH (exit 2, hard block):
- `chmod 777` or `chmod -R 777`
- `eval $variable` — shell injection
- `sudo rm` or `sudo chmod`
- Hardcoded secrets: `password="longstring"`, `api_key="..."`
- `echo ... token=` — secrets in shell history

### MEDIUM (exit 0, warning only, non-blocking):
- `curl | bash` — remote code execution
- `python -c "import os..."` — inline dangerous python
- `0.0.0.0` — binding to all network interfaces
- `nc -l` — netcat listener

Critical/High blocks Claude. Medium just prints a warning to stderr and lets it proceed.

---

## 6. `check-git-remotes.py` — PreToolUse on `Bash(git *)`

**Event:** Fires before any Bash command (only git commands proceed past the first check).

**What it does:** Enforces a **git remote whitelist** for network git operations only.

**Local operations** (`git commit`, `git log`, `git status`, `git diff`, `git branch`, etc.) → immediately allowed.

**Remote operations** (`clone`, `push`, `pull`, `fetch`, `submodule add`) → must match whitelist.

**How it resolves remotes:**
1. If the command uses a URL directly → normalize and check
2. If it uses a named remote like `origin` → reads `.git/config` to resolve the actual URL
3. URL normalization strips protocol (`https://`, `git@`, `ssh://`), credentials, and `.git` suffix for comparison

**`normalize_url()` examples:**
```
git@github.com:myorg/repo.git  →  github.com/myorg/repo
https://github.com/myorg/repo  →  github.com/myorg/repo
```

**Current whitelist** (`allowed-git-remotes.txt`):
```
github.com/sy171995/open_source_image_compression
```

**On blocked remote:** exits 2, tells Claude to add the remote to the whitelist or ask the user to run the git command manually.

---

## 7. `check-url-safety.py` — PreToolUse on `Bash(curl *)`

**Event:** Fires before curl commands specifically.

**What it does:** Two levels of checking:

### Hard block (exit 2) — curl that saves/executes:
- `curl -o file` or `-O` — saves to disk
- `curl --output file`
- `curl > file` — redirected
- `curl | tar` — pipes to extraction
- `curl | bash/sh/zsh` — remote code execution
- `curl | python`
- `curl --remote-name`

### Soft warning (exit 0) — non-whitelisted API domain:
If curl is doing a plain API call (no download) but the domain isn't in `TRUSTED_API_DOMAINS`, it prints a warning and allows it.

**Trusted API domains:**
```
api.github.com, api.openai.com, api.anthropic.com,
registry.npmjs.org, pypi.org, crates.io,
api.stripe.com, api.twilio.com, jsonplaceholder.typicode.com
```

Note: The script has a **self-guard** at line 27 — even if the `if: "Bash(curl *)"` filter doesn't trigger correctly, the script double-checks `if not re.search(r'\bcurl\b', command)`.

---

## 8. `check-repo-safety.py` — PreToolUse on `Bash(git clone *)`

**Event:** Fires before any `git clone` command.

**What it does:** **Always blocks the clone** (exits 2), but first calls the **GitHub API** to gather repo intelligence to share with the user:

```
Repository Analysis for myorg/repo:
  Description : A JPEG codec
  Stars       : 5,200
  Forks       : 823
  Open issues : 47
  Last push   : 3 days ago
  License     : BSD-3-Clause
  Size        : ~12.4 MB
  Archived    : No
  OK: Good star count
```

Warns if stars < 10 ("untrusted/unmaintained") or < 100 ("moderate, review before use"), or if the repo is archived.

For non-GitHub repos, it can't auto-analyze and just tells Claude to ask the user to check manually.

The exit message instructs Claude to relay all this to the user and ask them to clone manually.

---

## 9. `subagent-guardrail.py` — SubagentStart

**Event:** Fires whenever Claude spawns a subagent (via the Agent tool).

**What it does:** Two things:
1. **Audit log** — writes a JSON entry to `.claude/logs/subagent-audit.jsonl` with timestamp, session ID, and working directory
2. **Safety injection** — prints 5 safety rules to stdout so they're injected into the subagent's context window:
   - No downloads
   - No file transfers
   - If something needs downloading, tell the user
   - If something needs uploading, prepare locally and tell the user
   - These rules can't be overridden by user prompts

This ensures subagents inherit the same constraints as the parent session.

---

## 10. `audit-log.py` — PostToolUse on `Bash`

**Event:** Fires **after** every Bash command completes (non-blocking, always exits 0).

**What it does:** Appends a JSON record to `.claude/logs/bash-audit.jsonl`:
```json
{
  "timestamp": "2026-04-06T10:30:00+00:00",
  "event": "PostToolUse",
  "session_id": "abc123",
  "command": "make -j 1",
  "cwd": "/home/chander/CODE_BASE/libjpeg-turbo/build",
  "output_preview": "[ 45%] Building C object..."
}
```

Output is truncated to 500 chars. This is a **forensic trail** — you can always check what commands were run and what they returned.

---

## 11. `webfetch-guard.sh` — PreToolUse on `WebFetch`

**Event:** Fires before Claude uses the WebFetch tool (fetches a URL for reading).

**What it does:** Checks the URL's domain against `allowed-domains.txt`.

**Domain matching:** `"$DOMAIN" == "$line"` (exact) OR `"$DOMAIN" == *".$line"` (subdomain). So `docs.anthropic.com` is allowed if the whitelist has `anthropic.com`.

**Current whitelist:**
```
docs.anthropic.com
code.claude.com
```

If no whitelist file exists at all → blocks everything (fail-safe default).

---

## Summary: Hook Architecture

```
You type a message
    └─ user-prompt-safety.py        [inject warnings into context]

Claude tries to Edit/Write a file
    └─ protect-paths.sh             [block protected dirs]

Claude tries to run Bash
    ├─ block-downloads.py           [block wget/curl-O/pip/npm URLs]
    ├─ block-transfers.py           [block scp/rsync/s3/docker push]
    ├─ block-dangerous-code.py      [block rm -rf/, fork bombs, etc.]
    ├─ check-git-remotes.py         [whitelist git push/pull/clone]
    └─ check-url-safety.py          [block curl saves/pipes]

Claude tries to git clone
    └─ check-repo-safety.py         [always block, show repo stats]

Claude tries WebFetch
    └─ webfetch-guard.sh            [whitelist domains]

Claude spawns a subagent
    └─ subagent-guardrail.py        [log + inject safety rules]

Bash command completes
    └─ audit-log.py                 [write to bash-audit.jsonl]
```

The design is **defense in depth**: the prompt scanner nudges Claude's reasoning, while the PreToolUse hooks enforce hard limits regardless of what Claude decides.
