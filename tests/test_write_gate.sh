#!/bin/bash
# curriculum-write-gate 회귀: notion_reflect.py 실행 형태는 차단(rc 2), 언급만은 통과(rc 0).
# 본문 .md가 없어 사이드카 검사에서 막히는 것으로 "게이트에 걸렸다"를 판정한다.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="$HERE/../hooks/curriculum-write-gate.sh"
fail=0
ck() { # ck <expected_rc> <command>
  local in rc
  in=$(jq -cn --arg c "$2" '{tool_name:"Bash",tool_input:{command:$c},cwd:"/tmp"}')
  printf '%s' "$in" | bash "$GATE" >/dev/null 2>&1; rc=$?
  if [ "$rc" = "$1" ]; then printf '  ok   rc=%s  %s\n' "$rc" "$(printf '%s' "$2" | tr '\n' ' ')"
  else printf '  FAIL want=%s got=%s  %s\n' "$1" "$rc" "$(printf '%s' "$2" | tr '\n' ' ')"; fail=$((fail + 1)); fi
}
echo "[통과해야 함: 언급만]"
ck 0 'cd /tmp && grep -n foo notion_reflect.py'
ck 0 'echo notion_reflect.py'
ck 0 'rg -l notion_reflect.py . | head'
echo "[차단해야 함: 실행]"
ck 2 'python3 scripts/notion_reflect.py lecture.md --page x'
ck 2 $'cd /tmp\npython3 ~/x/notion_reflect.py PAGE nothere.md'
ck 2 $'NOTION_WORKSPACE_ID="abc" \\\n  python3 ~/x/notion_reflect.py \\\n  --report r.md \\\n  PAGE nothere.md'
ck 2 'uv run ~/x/notion_reflect.py PAGE nothere.md'
ck 2 'python3 -u ~/x/notion_reflect.py PAGE nothere.md'
ck 2 '  /usr/bin/env python3 ~/x/notion_reflect.py PAGE nothere.md'
ck 2 'cd ~/proj && python3 ~/x/notion_reflect.py PAGE nothere.md; echo done'
echo "실패 ${fail}건"
exit "$fail"
