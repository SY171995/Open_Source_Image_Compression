# Commit and Push

Before committing, run the build and full test suite. Only proceed if both pass.

---

## Gate 1 — Build

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo/build && make -j 1
```

If the build fails:
- Print a clear **BUILD FAILED** message with the relevant error output.
- **STOP. Do not proceed to tests or commit.**

---

## Gate 2 — Full Test Suite

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo/build && ctest --output-on-failure
```

If any tests fail:
- Print a clear **TESTS FAILED** message listing the failing test names.
- **STOP. Do not proceed to commit.**

---

## Gate 3 — Commit and Push

Only reached if Gates 1 and 2 both pass.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && git status && git diff HEAD --stat
```

Steps:
1. Show the diff summary above.
2. Check if `changelog.md` exists — if so, read it for a commit message summary.
3. Propose a concise commit message based on the changes (and `plan.md` if it exists).
4. Ask the user to confirm the commit message before proceeding.
5. Write the confirmed message to `/tmp/commit_msg.txt` using the Write tool, then commit:
   ```bash
   git add -A && git commit -F /tmp/commit_msg.txt
   ```
   NOTE: Never use a heredoc or `-m "..."` with `>` characters in the shell command — the `check-url-safety.py` hook false-positives on `>` in email addresses like `<noreply@anthropic.com>`. Always use `git commit -F /tmp/commit_msg.txt`.
6. Attempt to push:
   ```bash
   git push
   ```
   - If blocked by `check-git-remotes.py` (remote not whitelisted), tell the user:
     - The exact command to run manually.
     - To add the remote to `.claude/hooks/allowed-git-remotes.txt` for future pushes.
7. If `changelog.md` exists, offer to archive or delete it after a successful commit.
