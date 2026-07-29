# Curriculum Plugin

강의/교육과정 전 주기(설계 -> 맥락수집 -> 자료조사 -> 자료생성 -> 검수/개선 -> Notion 반영)를 다루는 Claude Code·Codex 스킬 패밀리 플러그인.

## 구성

| 구성요소 | 무엇 |
|---|---|
| `skills/using-curriculum` | 진입점: 라이프사이클 라우팅 + 불변 원칙(헌법) + 게이트 스크립트 정본(`scripts/`) |
| `skills/curriculum-design` | Phase 1~2: Backward Design 설계 + 고객/수강생 맥락수집 |
| `skills/curriculum-authoring` | Phase 3~4: 기존 자료 딥 탐색/이식 + 회차 페이지 작성(라이브/VOD 골격) |
| `skills/curriculum-review` | Phase 5: 검수/개선 하네스(기계 린트 + 페르소나 비평 + 실제 개선) |
| `skills/curriculum-notion-sync` | Phase 6(선택): Notion 반영(발산 게이트, surgical, round-trip) |
| `skills/notion` | Notion transport: 워크스페이스 검색/조회/수정, Markdown round-trip, 변경 선택 리뷰 |
| `agents/` | `curriculum-reviewer`(fresh-context 검수 리포트), `notion-explorer`(읽기 전용 좌표 탐색) |
| `hooks/` | Claude Code의 `notion_reflect.py` 쓰기 직전 충실도 게이트(PreToolUse) |

## 설치

### Claude Code

```bash
claude plugin marketplace add seungwonme/curriculum-plugin
claude plugin install curriculum@curriculum-marketplace
```

### Codex

```bash
codex plugin marketplace add seungwonme/curriculum-plugin
codex plugin add curriculum@curriculum
```

## 선택 의존성

- `notion` 스킬은 플러그인에 포함된다. Notion 조회/반영에는 별도로 `ntn` CLI와 워크스페이스 등록이 필요하며, 준비되지 않았으면 Phase 1~5만 진행한다.
- 맥락수집은 `project-collect`/`voice-memos` 스킬이 있으면 위임하고, 없으면 수동으로 진행한다.

## Maintainer

- source of truth는 `~/.agents/skills/shared/`의 6개 스킬 폴더다. 이 repo의 `skills/`는 배포 사본이므로 직접 편집하지 않는다.
- 반영 절차: shared에서 수정/검증(skill-manager 린트) -> `scripts/sync.sh` 실행 -> Claude/Codex manifest 검증 -> 커밋/푸시 + manifest 버전 동기화.
- `agents/`와 `hooks/`는 플러그인에서 관리한다. `skills/`만 shared 정본에서 생성한다.
- 계보: 단일 `curriculum` 스킬(2026-07 분리 전)에서 갈라져 나왔다. 분리 구조는 obra/superpowers의 bootstrap+소형 스킬 패턴을 따랐다.
