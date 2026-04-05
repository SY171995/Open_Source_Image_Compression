# Git Push

Push the current branch to a whitelisted remote.

Note: git push is controlled by the hook `check-git-remotes.py`. The remote must be listed in `.claude/hooks/allowed-git-remotes.txt`, otherwise the push will be blocked and the user will need to run it manually.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && git status && git log --oneline -5
```

Review the above, then attempt: `git push $ARGUMENTS`

If blocked by the hook, tell the user:
1. The exact command to run manually
2. Which remote to add to `allowed-git-remotes.txt` if they want to allow it
