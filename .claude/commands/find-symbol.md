# Find Symbol

Search for a function, variable, struct, or macro by name across the codebase.

Usage: `/project:find-symbol <name>`

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && grep -rn "$ARGUMENTS" src/ simd/ sharedlib/ --include="*.c" --include="*.h" --include="*.cpp" --include="*.hpp" --include="*.asm"
```

Present the results grouped by file, showing the line number and context for each match.
