# New Feature

Scaffold a new feature. Pass a short description as $ARGUMENTS.

Usage: `/project:new-feature <description>`

Based on `$ARGUMENTS`:
1. Ask clarifying questions if the scope is unclear
2. Identify which existing files will need modification
3. Follow the coding style rules in `.claude/rules/cpp-style.md`
4. Propose the implementation plan before writing any code
5. Wait for user approval before making changes
