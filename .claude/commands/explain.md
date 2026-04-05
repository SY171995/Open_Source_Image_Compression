# Explain

Explain a file or function in detail.

Usage: `/project:explain <file-or-function-name>`

Search for and read `$ARGUMENTS` — it could be a file path or a function/symbol name.
If it's a symbol, find it first using grep across src/, simd/, and sharedlib/.

Then explain:
1. What it does and its purpose in the codebase
2. Key parameters or fields
3. How it fits into the broader architecture
4. Any non-obvious logic or gotchas
