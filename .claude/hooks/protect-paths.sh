#!/bin/bash
# Hook: protect-paths.sh
# Blocks Edit and Write tool calls to folders listed in protected-paths.txt

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROTECTED_PATHS_FILE="$SCRIPT_DIR/protected-paths.txt"
[ ! -f "$PROTECTED_PATHS_FILE" ] && exit 0

PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty')

# Make file path absolute if relative
[[ "$FILE_PATH" != /* ]] && FILE_PATH="$PROJECT_DIR/$FILE_PATH"

while IFS= read -r line || [ -n "$line" ]; do
  # Skip comments and empty lines
  [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
  # Resolve protected path to absolute
  PROTECTED="$PROJECT_DIR/$line"
  if [[ "$FILE_PATH" == "$PROTECTED"* ]]; then
    echo "Modification blocked: '$line' is a protected folder. Remove it from .claude/hooks/protected-paths.txt to allow changes." >&2
    exit 2
  fi
done < "$PROTECTED_PATHS_FILE"

exit 0
