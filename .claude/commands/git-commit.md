# Git Commit

Stage all modified tracked files and create a commit. Use $ARGUMENTS as the commit message if provided, otherwise summarize the changes and propose one.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && git status && git diff
```

Review the staged and unstaged changes above, then:
1. Stage relevant files with `git add <files>`
2. Propose a commit message based on the changes
3. Ask the user to confirm before committing
4. Run: `git commit -m "<message>"`
