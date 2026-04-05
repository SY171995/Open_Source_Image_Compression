# Run tests

Run tests from the `build/` directory. Behavior depends on `$ARGUMENTS`:

## If `$ARGUMENTS` is "all" (or contains "all")

Run the full test suite:

```bash
cd /home/chander/CODE_BASE/libjpeg-turbo/build && ctest --output-on-failure
```

## Otherwise — smart test selection

1. Run `git diff --name-only HEAD` to find changed files.
2. Map changed files to ctest patterns using this table:

   | Changed path pattern          | ctest `-R` pattern |
   |-------------------------------|--------------------|
   | `src/turbojpeg*`              | `tjunittest`       |
   | `src/turbojpeg-mapfile`       | `tjunittest`       |
   | `src/tjbench*`                | `tjbench`          |
   | `src/jc*.c`                   | `cjpeg`            |
   | `src/jd*.c`                   | `djpeg`            |
   | `src/jpegtran*`               | `jpegtran`         |
   | `src/transupp*`               | `jpegtran`         |
   | `src/rdbmp*`, `src/wrbmp*`    | `bmpsizetest`      |
   | `src/example*`                | `example`          |
   | `simd/`                       | *(run all tests)*  |

3. Build the command:
   - If one match: `ctest -R "^<pattern>" --output-on-failure`
   - If multiple matches: OR them: `ctest -R "^(pattern1|pattern2)" --output-on-failure`
   - If `simd/` changed or no match found: fall back to full suite with a note explaining why.

4. Print which tests are being run and why before executing.
