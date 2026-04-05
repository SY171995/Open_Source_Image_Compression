# Lint / Static Analysis

Run available static analysis tools on the codebase.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && which cppcheck && cppcheck --enable=warning,style,performance --std=c99 src/ 2>&1 | head -50
```

If cppcheck is not available, report that and suggest: `sudo apt install cppcheck`

Summarize any warnings or issues found, grouped by severity.
