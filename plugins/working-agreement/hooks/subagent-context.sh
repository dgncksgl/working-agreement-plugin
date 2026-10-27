#!/bin/sh
# SubagentStart injects context only through JSON, so wrap the rules file in the
# hookSpecificOutput envelope. awk keeps the hook free of runtime dependencies.
rules="${CLAUDE_PLUGIN_ROOT}/rules/working-agreement.md"
# Without the file, awk would still print the opening of the envelope. Fail the way
# `cat` does for SessionStart: no stdout, a message on stderr, a non-blocking exit 1.
if [ ! -r "$rules" ]; then
  echo "working-agreement: cannot read $rules" >&2
  exit 1
fi
awk '
BEGIN { printf "{\"hookSpecificOutput\":{\"hookEventName\":\"SubagentStart\",\"additionalContext\":\"" }
{
  gsub(/\\/, "\\\\")
  gsub(/"/, "\\\"")
  gsub(/\t/, "\\t")
  gsub(/\r/, "\\r")
  printf "%s\\n", $0
}
END { printf "\"}}\n" }
' "$rules"
