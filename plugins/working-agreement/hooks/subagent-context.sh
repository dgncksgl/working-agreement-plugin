#!/bin/sh
# SubagentStart injects context only through JSON, so wrap the rules file in the
# hookSpecificOutput envelope. awk keeps the hook free of runtime dependencies.
rules="${CLAUDE_PLUGIN_ROOT}/rules/working-agreement.md"
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
