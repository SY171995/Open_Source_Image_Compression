# Commit and Push

Commit all changes and push to the remote. Run this after the codebase-verifier skill gives a PASS.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && git status && git diff HEAD --stat
```

Steps:
1. Show the diff summary above
2. Check if `changelog.md` exists — if so, read it for a commit message summary
3. Propose a concise commit message based on the changes (and `plan.md` if it exists)
4. Ask the user to confirm the commit message before proceeding
5. Stage and commit:
   ```bash
   git add -A && git commit -m "<confirmed message>"
   ```
6. Attempt to push:
   ```bash
   git push
   ```
   - If the push is blocked by `check-git-remotes.py` (remote not whitelisted), tell the user:
     - The exact command to run manually
     - To add the remote to `.claude/hooks/allowed-git-remotes.txt` if they want Claude to push in future
7. If `changelog.md` exists, offer to archive or delete it after a successful commit.
