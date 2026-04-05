#!/bin/bash
# Hook: prompt-network-check.sh
# UserPromptSubmit hook - detects download/transfer intent and injects context warning

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' | tr '[:upper:]' '[:lower:]')

[ -z "$PROMPT" ] && exit 0

DOWNLOAD_PATTERN='download|wget|curl|git clone|pip install|pip3 install|npm install|npm ci|yarn install|yarn add|apt install|apt-get install|brew install|cargo install|go get|go install|docker pull|fetch.*http|install.*package'
TRANSFER_PATTERN='upload|transfer|scp |rsync |sftp |ftp |send.*file|push.*file'

if echo "$PROMPT" | grep -qE "$DOWNLOAD_PATTERN"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: "NOTICE: The user request involves downloading or installing something from the internet. You CANNOT do this yourself — it is blocked. Tell the user exactly what command to run or what to download, where to place it, and ask them to notify you once it is done before you proceed."
    }
  }'
  exit 0
fi

if echo "$PROMPT" | grep -qE "$TRANSFER_PATTERN"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "UserPromptSubmit",
      additionalContext: "NOTICE: The user request involves transferring a file over the internet. You CANNOT do this yourself — it is blocked. Tell the user exactly what transfer to perform, and ask them to notify you once it is done before you proceed."
    }
  }'
  exit 0
fi

exit 0
