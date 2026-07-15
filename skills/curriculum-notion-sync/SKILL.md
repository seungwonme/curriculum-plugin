---
name: curriculum-notion-sync
description: "검수 통과한 강의 교안의 Notion 반영(Phase 6) - 베이스 선택 라우터, 발산 게이트, surgical/전체교체, notion_reflect.py fail-closed 반영, round-trip 검증, 이미지/자산 보존, 읽기 전용 좌표 탐색, 이미지 소싱/생성 규칙. 프로젝트가 발행 채널로 Notion을 선언한 경우만. Use when user asks for 교안 노션 반영, 강의 자료 노션 업로드/동기화, 회차 페이지 반영, 강의 이미지 노션 삽입, 반영 전 페이지 좌표/정체성 확인. Do NOT use for 일반 Notion 검색/CRUD(notion 스킬), 교안 내용 자체의 검수/수정(curriculum-review), 교안 작성(curriculum-authoring)."
---

# Curriculum Notion Sync - 노션반영 (Phase 6 - 선택적)

프로젝트가 발행 채널로 Notion을 선언했을 때만 실행한다. 공통 CLI, 인증, 승인, 삭제 규칙은 `notion` 스킬의 `references/ntn-cli.md`가 정본이다 - 반영 전에 먼저 읽는다. 해당 스킬이나 `ntn`이 없으면 실행하지 않는다.

## 시작 전 1회

`using-curriculum` 스킬의 `references/author-intent.md`(헌법)를 읽는다 - 사용자 편집 보존, 자산 보존, fail-closed. 파일에 접근할 수 없으면 이 원칙만 지키고 진행한다.

반영 전제: `curriculum-review`의 `gate-review` 통과(검수 리포트 + 후보 binding). 통과 없이 반영하지 않는다.

## 라우팅

| 작업 | 읽을 것 |
|---|---|
| 반영 절차(베이스 선택, 발산 게이트, 전체교체/surgical, round-trip) | [`references/notion-sync.md`](references/notion-sync.md) |
| 반영 전 좌표/정체성 확인(읽기 전용, `notion-explorer` 에이전트 위임 가능) | [`references/notion-exploration.md`](references/notion-exploration.md) |
| 이미지 출처 우선순위, 생성 규칙, Notion 삽입/검증 | [`references/image-generation-notion-assets.md`](references/image-generation-notion-assets.md) |

반영 스크립트 정본은 `using-curriculum` 스킬에 있다: `${CLAUDE_PLUGIN_ROOT}/skills/using-curriculum/scripts/notion_reflect.py`(fail-closed 반영), 같은 폴더의 `fidelity_lint.py`(충실도 sidecar 검사). 실행 명령과 필수 인자는 notion-sync.md 4-2절이 정본이다.

프로젝트별 page-id 매핑, 승인된 변경, round-trip 결과는 프로젝트 `AGENTS.md`에 기록한다.
