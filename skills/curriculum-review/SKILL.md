---
name: curriculum-review
description: "강의 자료 검수/개선 하네스(Phase 5) - 기계 린트(review-draft), 사용자 관점 페르소나 비평(curriculum-reviewer 서브에이전트), page-id 환각 차단(verify-pages), 실제 개선 실행(약점표 금지), iterate-until-pass, 반영 전 gate-review까지. 제작 직후 자기검수와 단독 검수 둘 다. Use when user asks for 교안 검수, 강의 자료 리뷰/비평/개선, 초안 다듬기, 사실 확인, 반영 전 점검. Do NOT use for 신규 교안 작성이나 자료 조사(curriculum-authoring), Notion 반영 실행(curriculum-notion-sync), 교육과 무관한 문서 리뷰."
---

# Curriculum Review - 검수/개선 하네스 (Phase 5)

검수는 선택이 아니라 제작의 필수 마무리다. **산출물은 약점 표가 아니라 실제로 고쳐진 자료 + 검수 리포트다.**

## 시작 전 1회

`using-curriculum` 스킬의 `references/author-intent.md`(헌법)를 읽는다 - 개선은 명시적 결함만 외과적으로, 멀쩡한 자료를 AI 미감으로 재작성하지 않는다. 파일에 접근할 수 없으면 이 원칙만 지키고 진행한다.

게이트 스크립트 정본은 `using-curriculum` 스킬에 있다: `${CLAUDE_PLUGIN_ROOT}/skills/using-curriculum/scripts/curriculum_gate.py`. **게이트 통과는 응답에 (실행 명령, 통과 여부, 핵심 출력 라인) 인용으로만 인정.**

## 하네스

전 단계가 [`references/review.md`](references/review.md)에 있다 - 그대로 따른다.

(단독 진입은 0절 딥 탐색 먼저) -> review-draft 린트 -> 페르소나 비평(인용 게이트, `curriculum-reviewer` 서브에이전트) -> verify-pages -> **실제 개선(텍스트+이미지)** -> before/after 재검 -> iterate(종료조건) -> 검수 리포트 -> `gate-review`.

- 제작(Phase 4) 직후 자기검수는 딥 탐색을 건너뛴다(`curriculum-authoring` 3-1에서 이미 함).
- 반영(Phase 6)은 `curriculum-notion-sync` 스킬로 - `gate-review` 통과가 전제다.
