#!/bin/bash
# PostToolUse hook for Bash — triggers dashboard regeneration on skill install/remove
INPUT=$(cat)
CMD=$(echo "$INPUT" | python -c "
import sys,json
data=json.load(sys.stdin)
print(data.get('tool_input',{}).get('command',''))
" 2>/dev/null)

if echo "$CMD" | grep -qE "skills (install|remove|uninstall)"; then
  python "F:/04_利安工坊/repos/skills-dashboard/generate.py" &
fi
exit 0
