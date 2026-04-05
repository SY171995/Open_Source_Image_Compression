# Run a single test

Run a specific test by name from the build directory. Pass the test name as $ARGUMENTS.

Usage: `/project:test-single <test-name>`

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo/build && ctest -R "$ARGUMENTS" --output-on-failure
```
