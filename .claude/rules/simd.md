---
description: Rules for working with SIMD code
globs: ["simd/**/*"]
---

# SIMD Code Rules

- SIMD routines live in `simd/` and are organized by architecture (x86, arm, loongarch, mips, etc.)
- x86-64 SIMD uses NASM assembly (`.asm` files)
- Arm SIMD uses intrinsics in C (`.c` files)
- When modifying SIMD code, always verify the corresponding non-SIMD fallback path in `src/` still works
- SIMD functions are performance-critical — avoid unnecessary abstraction or branching
