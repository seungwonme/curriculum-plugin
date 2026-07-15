#!/usr/bin/env bash
# PreToolUse(Bash) 빠른 선별기: 명령에 notion_reflect.py가 없으면 즉시 통과(python 미기동).
# 있을 때만 충실도 게이트 python으로 stdin을 넘긴다(exit code 그대로 전파 -> exit 2면 쓰기 차단).
DIR="$(cd "$(dirname "$0")" && pwd)"
input=$(cat)
case "$input" in
  *notion_reflect.py*) printf '%s' "$input" | python3 "$DIR/curriculum-write-gate.py" ;;
  *) exit 0 ;;
esac
