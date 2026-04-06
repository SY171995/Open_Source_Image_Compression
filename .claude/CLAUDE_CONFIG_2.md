# Claude Code Configuration — libjpeg-turbo

Reference for the `.claude/` folder. Share with team or use as a quick reference.

---

## Folder Structure

```
.claude/
├── CLAUDE.md               # Project instructions always in Claude's context
├── settings.json           # Tool permissions + hook wiring
├── commands/               # Slash commands (/project:<name>)
├── skills/                 # Auto-triggered AI pipelines
├── hooks/                  # Security/safety scripts
├── rules/                  # Coding standards
└── logs/                   # Audit logs (auto-written)
```

---

## Development Pipeline

All coding work flows through this pipeline (defined in `CLAUDE.md`):

```
1. Describe feature/fix
        ↓
2. codebase-planner  →  produces plan.md
        ↓
3. "go ahead"
        ↓
4. codebase-developer  →  file-by-file changes with approval, writes changelog.md
        ↓
5. "verify"
        ↓
6. codebase-verifier  →  build + tests + code review  →  PASS / FAIL
        ↓
7. /commit-and-push
   Gate 1: make -j 1         (STOP if fails)
   Gate 2: ctest             (STOP if fails)
   Propose message → confirm → git commit -F /tmp/commit_msg.txt → git push
```

> **Commit message rule:** Never use heredoc or `-m "..."` with `>` in the shell — the `check-url-safety.py` hook false-positives on `>` in email addresses. Always write to `/tmp/commit_msg.txt` and use `git commit -F`.

---

## Skills (Auto-Triggered)

| Skill | Triggers on | What it does |
|---|---|---|
| `codebase-planner` | "implement X", "add feature", "fix bug", "refactor", any multi-file request | Reads codebase (read-only), traces dependencies, produces structured `plan.md`, waits for approval |
| `codebase-developer` | "go ahead", "execute the plan", "start implementing" | Executes `plan.md` one file at a time, requires explicit approval per file, logs to `changelog.md` |
| `codebase-verifier` | "verify", "check my changes", "validate", "did it work" | Checks plan conformance, runs build + tests (with approval), code quality review, issues PASS/FAIL verdict |

---

## Slash Commands

### Build & Test

| Command | What it does |
|---|---|
| `/configure` | `cmake .. -G"Unix Makefiles"` from `build/` |
| `/build` | `make -j 1` from `build/` |
| `/rebuild` | Wipes `build/`, reconfigures, full rebuild |
| `/test` | `ctest --output-on-failure` |
| `/test-single <name>` | `ctest -R <name> --output-on-failure` |
| `/lint` | `cppcheck` on `src/` (warning/style/performance) |

### Code Review & Navigation

| Command | What it does |
|---|---|
| `/review` | Reviews `git diff HEAD` against style rules and bug criteria |
| `/what-changed` | Summarizes uncommitted changes, flags areas needing testing |
| `/find-symbol <name>` | Greps for function/struct/macro across `src/`, `simd/`, `sharedlib/` |
| `/explain <file-or-symbol>` | Explains purpose, parameters, and architecture |
| `/new-feature <description>` | Clarifies scope, proposes plan, waits for approval before coding |

### Git

| Command | What it does |
|---|---|
| `/git-status` | Working tree state — staged, modified, untracked, ahead/behind |
| `/git-log` | Last 20 commits as a graph |
| `/git-commit [message]` | Stages, proposes message, asks confirmation |
| `/git-push` | Push — blocked by hook if remote not whitelisted |
| `/commit-and-push` | Build gate → test gate → commit → push |

---

## Hooks

### `UserPromptSubmit`

| Script | Blocks? | Purpose |
|---|---|---|
| `user-prompt-safety.py` | No (injects context) | Detects download/transfer/danger intent; informs Claude to defer network ops to user |

### `PreToolUse`

| Trigger | Script | Blocks? | What it checks |
|---|---|---|---|
| Edit / Write | `protect-paths.sh` | Yes | Writes to paths in `protected-paths.txt` |
| Bash | `block-downloads.py` | Yes | `wget`, `curl -o`, binary URLs, `pip/npm install` from URLs |
| Bash | `block-transfers.py` | Yes | `scp`, `rsync` to remote, AWS S3/GCS/Azure, `docker push`, netcat |
| Bash | `block-dangerous-code.py` | Critical/High | `rm -rf /`, fork bombs, `mkfs`, `dd` to block device, `chmod 777`, hardcoded secrets |
| Bash (git *) | `check-git-remotes.py` | Yes | Blocks remote git ops unless remote is in `allowed-git-remotes.txt`; local ops free |
| Bash (curl *) | `check-url-safety.py` | Yes (saves) | Blocks `curl -o`/`> file`/`\| bash`; allows API calls; warns on untrusted domains |
| Bash (git clone *) | `check-repo-safety.py` | Always | Blocks all clones; fetches GitHub stats (stars, forks, issues, size, license) for user review |
| WebFetch | `webfetch-guard.sh` | Yes | Blocks any domain not in `allowed-domains.txt` |

### `SubagentStart`

| Script | Purpose |
|---|---|
| `subagent-guardrail.py` | Logs spawn to `logs/subagent-audit.jsonl`; injects no-download/no-transfer rules into subagent |

### `PostToolUse`

| Script | Purpose |
|---|---|
| `audit-log.py` | Appends every Bash command to `logs/bash-audit.jsonl` — timestamp, session ID, command, cwd, output preview |

---

## Permissions (`settings.json`)

Pre-approved — no confirmation prompt:

```
make  cmake  ctest  git  nasm  cat  head  tail  awk  find  grep  ls
```

All other Bash commands require user approval.

---

## Config Files

| File | Current state | How to change |
|---|---|---|
| `hooks/protected-paths.txt` | `TEST_EDIT/` protected | Add/remove folder paths (relative to project root) |
| `hooks/allowed-git-remotes.txt` | **Empty** — all remote git ops blocked | Add `github.com/org/repo` (one per line) to allow |
| `hooks/allowed-domains.txt` | `docs.anthropic.com`, `code.claude.com` | Add domain names to allow WebFetch |

---

## Coding Rules (`rules/`)

Always loaded into Claude's context.

| File | Summary |
|---|---|
| `cpp-style.md` | C++20/23; trailing `_` for member vars; camelCase; PascalCase for classes; `const`/`constexpr`; inline in `.hpp`, else `.cpp` |
| `simd.md` | SIMD in `simd/`; x86-64 = NASM `.asm`; Arm = C intrinsics; always verify non-SIMD fallback |
| `tests.md` | Tests via `ctest`; reference images in `testimages/`; MD5 checksums validate output |

---

## Logs

| File | Written by | Contents |
|---|---|---|
| `logs/bash-audit.jsonl` | `audit-log.py` | Every Bash command: timestamp, session ID, command, cwd, output preview |
| `logs/subagent-audit.jsonl` | `subagent-guardrail.py` | Every subagent spawn: timestamp, session ID, cwd |

---

## Unused Scripts (not wired in `settings.json`)

Present as reference/fallback but inactive:

- `hooks/bash-network-guard.sh` — bash version of download/transfer blocking (superseded by Python hooks)
- `hooks/prompt-network-check.sh` — bash version of prompt intent detection (superseded by `user-prompt-safety.py`)
