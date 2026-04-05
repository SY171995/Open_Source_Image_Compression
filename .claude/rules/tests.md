---
description: Rules for working with tests
globs: ["test/**/*", "testimages/**/*"]
---

# Test Rules

- Tests are driven by CMake/ctest — run with `ctest --output-on-failure` from the `build/` directory
- Reference images are stored in `testimages/`
- When adding a new feature, check if a corresponding test exists in `test/`
- MD5 checksums are used to validate output images — see `src/md5/`
