# libjpeg-turbo Project

## Overview
libjpeg-turbo is a JPEG image codec that uses SIMD instructions to accelerate baseline JPEG compression and decompression on x86, x86-64, Arm, and other platforms.

## Build System
- Uses CMake (v3.15+) as the build system
- Assembler: NASM (2.13+) required for x86/x86-64 SIMD
- Build output directory: `build/`

## Build Commands

### Configure (first time or after CMakeLists changes)
```bash
cd build
cmake .. -G"Unix Makefiles"
```

### Build
## because it has 2 cores without hyper threading
```bash
cd build
make -j 1
```

### Run Tests
```bash
cd build
ctest
```

## Key Directories
- `src/` — core JPEG codec source
- `simd/` — SIMD-optimized routines (x86, arm, etc.)
- `sharedlib/` — shared library and CLI tools (cjpeg, djpeg, jpegtran)
- `test/` — test scripts
- `testimages/` — reference images for testing
- `fuzz/` — fuzz testing targets
- `jna/` — TurboJPEG Java Native Access bindings
- `doc/` — documentation
- `cmakescripts/` — CMake helper scripts

## Important Notes
- Always use `make -j 1` (single-threaded), not parallel builds
- The `build/` directory is the CMake binary dir and should not be committed

## Committing
- Never use a heredoc (`cat <<'EOF'`) for commit messages — the `check-url-safety.py` hook scans the full bash command string and false-positives on `>` in `<noreply@anthropic.com>`
- Always write the commit message to a temp file and use `git commit -F`:
  ```bash
  # Write message (no > in the shell command)
  # then:
  git commit -F /tmp/commit_msg.txt
  ```

## Development Pipeline

All coding work follows this pipeline — do not skip steps:

```
User describes feature/fix
        ↓
[auto] codebase-planner skill
  → produces plan.md
        ↓
User says "go ahead" / "implement"
        ↓
[auto] codebase-developer skill
  → reads plan.md
  → makes changes with approval
  → writes changelog.md
        ↓
User says "verify" / "check"
        ↓
[auto] codebase-verifier skill
  → reads plan.md + changelog.md
  → build + test + code review
  → PASS / FAIL report
        ↓
User runs /project:commit-and-push
  → stages + commits + push (if whitelisted remote)
```
