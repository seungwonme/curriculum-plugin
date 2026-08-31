---
argument-hint: "[설계|맥락수집|자료조사|자료생성|검수개선|노션반영]"
name: using-curriculum
description: "강의/교육과정 전 주기의 진입점이자 커리큘럼 스킬 패밀리의 헌법 - 설계/맥락수집은 curriculum-design, 자료조사/생성은 curriculum-authoring, 검수/개선은 curriculum-review, 노션 반영은 curriculum-notion-sync로 라우팅하고, 모든 Phase 공통 불변 원칙(검증 자료 우선, 신호 우선, 게이트 증거 인용)과 게이트 스크립트 정본을 제공. Use when user asks for 커리큘럼, 강의, 교안, 교육과정 작업을 시작하거나 전 주기로 진행할 때, 여러 Phase에 걸친 작업, 어느 커리큘럼 스킬을 쓸지 애매할 때. Do NOT use for 교육과 무관한 문서 작성, 일반 Notion 검색/CRUD, 단일 Phase만 필요한 작업(해당 하위 스킬을 직접 쓴다)."
---

# Using Curriculum - 강의/교육과정 전 주기 진입점 (설계 -> 맥락수집 -> 자료조사 -> 자료생성 -> 검수/개선 -> 노션반영)

Backward Design + ADDIE 하이브리드. 맥락 수집부터 검수, 선택적 발행까지 한 흐름이고, 단계 실행은 하위 스킬이 맡는다. 이 스킬은 라우팅, 불변 원칙(헌법), 게이트 스크립트 정본(`scripts/`)을 제공한다.

## 라이프사이클 (6 Phase - 어느 단계부터든 진입 가능, 해당 스킬을 호출한다)

| Phase | 무엇 | 스킬 |
|---|---|---|
| 1. **설계** | 무엇을/왜 가르치나 - 목표, 차시 분해, 평가, 버전관리, B2B/B2C | `curriculum-design` (design.md 1절) |
| 2. **맥락수집** | 고객/수강생/요구 context 수집 - `project-collect`에 위임 | `curriculum-design` (design.md 2절) |
| 3. **자료조사** | 프로젝트가 선언한 소스 딥 탐색 -> 후보 원문 비교 -> `gate-candidates` 통과 | `curriculum-authoring` (authoring.md 3-1절) |
| 4. **자료생성** | 개요 합의(outline-first) 후 회차 페이지 작성 + 자기검수(초안 != 완료) | `curriculum-authoring` (3-2~3-8절) |
| 5. **검수/개선** | 사용자 관점으로 비평하고 **실제로 고친다**(약점표 금지). 진행된 수업의 전달 회고(녹화/전사 분석)도 여기 | `curriculum-review` |
| 6. **노션반영** | 프로젝트가 Notion 발행을 선언한 경우만 - 안전선, surgical, round-trip | `curriculum-notion-sync` |

## 불변 원칙 (모든 Phase 공통 - 하위 스킬도 준수)

- **AI 창작이 아니라 사람의 검증 자료가 기본값, 약간의 개선만** - 모든 Phase의 헌법. 기존 검증 자료를 베이스로 최소 개선하고, AI 자율 미감으로 새로 짓거나(특히 이미지) 멀쩡한 걸 방치 판단하지 않는다. 왜, 3대 실패패턴, 판단원칙은 [`references/author-intent.md`](references/author-intent.md)(제작/검수 시작 전 1회 읽기 - 하위 스킬 직접 호출 시에도).
- **핵심만, 신호 우선** - 모든 블록은 수강생이 *뭘 보고/칠지*(명령어, 출처, 실제 화면)만 담는다. 빼도 할 일이 안 줄면 삭제.
- **개념은 명료하게** - 한 줄 정의 -> 직관적 단계 -> 복붙 프롬프트. 잡설 제거와 개념 흐리기는 다르다.
- **산출물 중심 이론-실습 조율** - 비율보다 순서와 완주를 우선한다: `완성 화면 -> 필요한 이론 -> 시연 -> 수강생 실습 -> 결과 확인`. 이론은 직후 실습에 필요한 만큼만 두고, 일정이 밀리면 다음 이론/보너스를 줄여 실습/검증/제출 시간을 보존한다.
- **산출물 형식** - 회차 교안과 검수 리포트는 Markdown, 고객 제출용 제안서와 보고서는 DOCX가 기본이다. 프로젝트나 계약에서 형식을 지정했다면 그 형식을 우선한다.
- **산문 최소, 불렛/넘버링/표 우선** - 세 문장 넘는 줄글은 쪼갠다. 컴팩트 판단은 전체 줄 수가 아니라 문단 밀도로. 상세는 `curriculum-authoring`의 authoring.md 3-5절, 표기는 [`references/anti-patterns.md`](references/anti-patterns.md).
- **논리 구조는 항상 고객, 수강생 중심** - 사고 사슬은 1. 수강생 피드백/설문 -> 2. 만들고 싶다고 한 주제 -> 3. 그래서 이번 회차에 만드는 것 -> 4. 만들기 위해 가르칠 개념(기존 자료 이식). 개념->실습 순으로 정리하지 않는다.
- **수강생 수준은 프로젝트 맥락을 따른다** - 프로젝트 `AGENTS.md`와 context의 직무, 기술 수준에 맞춰 용어, 실습, 설명 밀도를 조절한다. 입문자와 비개발자는 일상어와 첫 등장 1줄 풀이를 쓰고, 개발자는 실제 repo, 테스트, 운영 맥락을 보존한다.
- **딥 탐색 -> 최선 선택 -> 비판적 검토 후 이식** (무비판 복붙 금지) - 통째 이식하되 도메인(고객사, 팀, 예시)만 치환하고, 구체를 일반 라벨로 희석하지 않는다. 원본 밀도가 상한선. 강제는 딥 탐색 게이트(authoring 3-1절 / review 0절).
- **안전선**: 위험/보안 우회 명령(인증서 검증 끄기 등)은 학습자 본문, 강사 메모 어디에도 금지. 내부 모순 금지(저장 안 되면 "시제품", 되면 "도구"). 시간 현실성(한 블록에 풀코스 금지).

## 게이트 인프라 (스크립트 정본)

깨지기 쉬운 단계는 산문이 아니라 게이트 스크립트가 산출물/exit-code로 강제한다. 정본은 이 스킬의 `scripts/`이며 하위 스킬이 아래 경로로 호출한다. **게이트 통과는 응답에 (실행 명령, 통과 여부, 핵심 출력 라인)을 인용해야 인정**한다.

```text
python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-curriculum/scripts/curriculum_gate.py --help
```

| 게이트 | 스크립트 | 쓰는 스킬 |
|---|---|---|
| 딥 탐색(`explore`, `gate-candidates`) | `curriculum_gate.py` | curriculum-authoring, curriculum-review |
| 미디어(`verify-media`) | `curriculum_gate.py` | curriculum-authoring, curriculum-review |
| 환각 차단(`verify-pages`) | `curriculum_gate.py` | curriculum-review |
| 검수(`review-draft`, `gate-review`) | `curriculum_gate.py` | curriculum-review |
| 2형태 원칙 lint | `format_scan.py` | curriculum-authoring, curriculum-review |
| 충실도(sidecar) | `fidelity_lint.py` | curriculum-notion-sync |
| 반영(fail-closed) | `notion_reflect.py` | curriculum-notion-sync |
| 단계 현황(`status`) | `curriculum_gate.py` | 전 주기 가시성(통과 판정 아님) |

## 실행 순서 (전 주기)

설계(curriculum-design) -> 맥락수집(curriculum-design) -> 고객 리뷰(피드백 -> `curriculum-v{N}` 변경이력 헤더) -> 자료조사/개요 합의/자료생성(curriculum-authoring) -> 검수/개선(curriculum-review) -> 표기 점검 -> 프로젝트가 Notion 발행을 쓰면 반영(curriculum-notion-sync).

## 관련 지식

- `project-collect` - 다중 소스 context 수집(Phase 2 위임), `voice-memos` - 음성 메모 전사(Phase 2)
- `humanize-korean` - AI 티/번역투 탐지/윤문(톤 게이트)
- `notion` 스킬의 ntn-cli reference 문서 - Notion 공통 쓰기 안전선, ntn CLI, 워크스페이스 전환
- `notion-explorer`(에이전트) - Notion 좌표 읽기 전용 탐색, `curriculum-reviewer`(에이전트) - fresh-context 검수 리포트
- 프로젝트별 동기화 로그, page id 매핑은 각 프로젝트 `AGENTS.md`에(결정 원장)
