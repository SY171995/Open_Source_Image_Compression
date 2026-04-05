# Rebuild (clean)

Wipe the build directory and do a full clean rebuild from scratch.

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo && rm -rf build && mkdir build && cd build && cmake .. -G"Unix Makefiles" && make -j 1
```
