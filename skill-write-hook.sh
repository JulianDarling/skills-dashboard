#!/bin/bash
# PostToolUse hook for Write/Edit — triggers dashboard regeneration when skill files change
INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | python -c "
import sys,json
data=json.load(sys.stdin)
print(data.get('tool_input',{}).get('file_path',''))
" 2>/dev/null)

if echo "$FILEPATH" | grep -qiE "(commands/|\.claude/skills/)"; then
  python "F:/04_利安工坊/repos/skills-dashboard/generate.py" &
fi
exit 0
