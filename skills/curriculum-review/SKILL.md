---
name: curriculum-review
description: "강의 자료 검수·개선과 실제 수업 전달 회고를 수행한다. 교안은 기계 린트, 사용자 관점 비평, page-id 검증, 실제 개선, iterate-until-pass, 반영 전 gate-review까지 닫고, 진행된 수업은 녹화·전사 타임스탬프로 계획 대비 시간·실습·질문·이월을 분석한다. Use for 교안 검수, 강의 자료 리뷰/개선, 실제 수업 회고, 강의 녹화 분석, 수업 시간 배분, 다음 회차 개선. Do NOT use for 신규 교안 작성이나 자료 조사(curriculum-authoring), Notion 반영 실행(curriculum-notion-sync), 교육과 무관한 문서 리뷰."
---

# Curriculum Review - 검수/개선 하네스 (Phase 5)

교안 검수는 제작의 필수 마무리다. 교안 검수 산출물은 약점 표가 아니라 실제로 고쳐진 자료와 검수 리포트다. 실제 수업 회고는 이미 진행된 수업을 소급해 재작성하지 않고, 근거가 연결된 전달 회고와 다음 회차 변경안을 남긴다.

## 시작 전 1회

`using-curriculum` 스킬의 `references/author-intent.md`(헌법)를 읽는다 - 개선은 명시적 결함만 외과적으로, 멀쩡한 자료를 AI 미감으로 재작성하지 않는다. 파일에 접근할 수 없으면 이 원칙만 지키고 진행한다.

## 모드

| 요청 | 읽고 따를 것 | 산출물 |
|---|---|---|
| 교안·초안·Notion 반영 전 자료 검수 | [`references/review.md`](references/review.md) | 고쳐진 자료 + 검수 리포트 |
| 녹화·녹음·전사 기반 실제 수업 회고 | [`references/delivery-review.md`](references/delivery-review.md) | 타임스탬프 근거 회고 + 다음 회차 변경안 |

## 교안 검수 하네스

게이트 스크립트 정본은 `using-curriculum` 스킬에 있다: `${CLAUDE_PLUGIN_ROOT}/skills/using-curriculum/scripts/curriculum_gate.py`. **게이트 통과는 응답에 (실행 명령, 통과 여부, 핵심 출력 라인) 인용으로만 인정.**

(단독 진입은 0절 딥 탐색 먼저) -> review-draft 린트 -> 페르소나 비평(인용 게이트, `curriculum-reviewer` 서브에이전트) -> verify-pages -> **실제 개선(텍스트+이미지)** -> before/after 재검 -> 변경 승인 diff -> iterate(종료조건) -> 검수 리포트 -> `gate-review`.

- 제작(Phase 4) 직후 자기검수는 딥 탐색을 건너뛴다(`curriculum-authoring` 3-1에서 이미 함).
- 이미 수강생이나 고객사가 보는 자료는 개선본을 바로 쓰지 않는다. 리뷰 HTML로 항목별 승인을 받고 승인분만 반영한다(review.md 4-5절).
- 반영(Phase 6)은 `curriculum-notion-sync` 스킬로 - `gate-review` 통과가 전제다.
