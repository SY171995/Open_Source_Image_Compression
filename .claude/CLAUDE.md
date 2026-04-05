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
