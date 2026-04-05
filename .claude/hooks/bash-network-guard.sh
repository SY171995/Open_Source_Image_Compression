#!/bin/bash
# Hook: bash-network-guard.sh
# PreToolUse hook - blocks download and file transfer commands in Bash

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$COMMAND" ] && exit 0

# Check for download commands
if echo "$COMMAND" | grep -qE '^\s*(wget|curl\s.*(--output|-O\b|-o\s|--remote-name)|git\s+clone|git\s+submodule\s+update|pip3?\s+(install|download)|npm\s+(install|ci|add)|yarn\s+(install|add)|apt(-get)?\s+install|brew\s+install|cargo\s+(install|add)|go\s+(get|install)|docker\s+pull)'; then
  echo "BLOCKED: Download attempt detected." >&2
  echo "Command: $COMMAND" >&2
  echo "You cannot download files or install packages from the internet." >&2
  echo "Tell the user to run this command manually and notify you once it is done." >&2
  exit 2
fi

# Check for file transfer commands
if echo "$COMMAND" | grep -qE '^\s*(scp\s|rsync\s|sftp\s|ftp\s|curl\s.*(-T\s|--upload-file|--data\s*@|--data-binary\s*@|-d\s*@)|ncat?\s.*<)'; then
  echo "BLOCKED: File transfer attempt detected." >&2
  echo "Command: $COMMAND" >&2
  echo "You cannot transfer files over the internet." >&2
  echo "Tell the user to perform this transfer manually and notify you once it is done." >&2
  exit 2
fi

exit 0
