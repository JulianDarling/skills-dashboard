#!/bin/bash
INPUT=$(cat)
SKILL=$(echo "$INPUT" | python -c "
import sys,json
data=json.load(sys.stdin)
print(data.get('tool_input',{}).get('skill',''))
" 2>/dev/null)
[ -z "$SKILL" ] && exit 0
LOG_DIR="F:/04_利安工坊/output"
echo "{\"skill\":\"$SKILL\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$LOG_DIR/usage.jsonl"
exit 0
