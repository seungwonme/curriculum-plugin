#!/usr/bin/env bash
# shared 정본(~/.agents/skills/shared)의 커리큘럼 5개 스킬을 이 플러그인의 배포 사본으로 sync한다.
# 정본은 shared다 - 이 플러그인의 skills/를 직접 편집하지 말 것.
# 경로 rewrite: ~/.agents/skills/shared/ -> ${CLAUDE_PLUGIN_ROOT}/skills/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HOME/.agents/skills/shared"
SKILLS=(using-curriculum curriculum-design curriculum-authoring curriculum-review curriculum-notion-sync)
for s in "${SKILLS[@]}"; do
  rsync -a --delete --exclude '__pycache__' "$SRC/$s/" "$ROOT/skills/$s/"
  find "$ROOT/skills/$s" -name '*.md' -print0 \
    | xargs -0 sed -i '' 's|~/.agents/skills/shared/|${CLAUDE_PLUGIN_ROOT}/skills/|g'
done
echo "synced: ${SKILLS[*]}"
