# Review changes

Review staged or recent changes for correctness, style, and potential issues.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && git diff HEAD
```

Review the diff above and report:
1. Any violations of the coding style rules (see `.claude/rules/cpp-style.md`)
2. Potential bugs or logic errors
3. Missing error handling at system boundaries
4. Any security concerns
