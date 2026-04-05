#!/bin/bash
# Hook: webfetch-guard.sh
# PreToolUse hook - blocks WebFetch to non-whitelisted domains

INPUT=$(cat)
URL=$(echo "$INPUT" | jq -r '.tool_input.url // empty')

[ -z "$URL" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WHITELIST_FILE="$SCRIPT_DIR/allowed-domains.txt"

# If no whitelist file, block everything
if [ ! -f "$WHITELIST_FILE" ]; then
  echo "BLOCKED: WebFetch to '$URL' is not allowed." >&2
  echo "No allowed-domains.txt found. Add the domain to .claude/hooks/allowed-domains.txt to allow it." >&2
  exit 2
fi

# Extract domain from URL (strip protocol and path)
DOMAIN=$(echo "$URL" | sed -E 's|https?://([^/]+).*|\1|')

while IFS= read -r line || [ -n "$line" ]; do
  [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
  if [[ "$DOMAIN" == "$line" || "$DOMAIN" == *".$line" ]]; then
    exit 0
  fi
done < "$WHITELIST_FILE"

echo "BLOCKED: WebFetch to '$DOMAIN' is not whitelisted." >&2
echo "Tell the user the URL you need to access. They can:" >&2
echo "  1. Add '$DOMAIN' to .claude/hooks/allowed-domains.txt to allow it" >&2
echo "  2. Fetch the content themselves and paste it into the conversation" >&2
exit 2
