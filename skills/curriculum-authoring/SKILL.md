---
name: curriculum-authoring
description: "강의 교안/회차 자료의 조사(Phase 3)와 생성(Phase 4) - 기존 자료 딥 탐색(explore 게이트)과 통째 이식, outline-first 개요 합의, 라이브/VOD 골격 선택, 수강생 수준별 콘텐츠 원칙, 미디어 게이트, 제작 직후 자기검수까지. Use when user asks for 교안 작성, 강의안, 회차 자료 제작, 실습 설계, VOD 클립 자료, 녹화 대본, 기존 강의자료 조사/이식, 라이브 강의 운영 팁. Do NOT use for 과정 설계나 학습목표 정의(curriculum-design), 이미 있는 자료의 단독 검수(curriculum-review), Notion 페이지 반영 실행(curriculum-notion-sync)."
---

# Curriculum Authoring - 자료조사 + 자료생성 (Phase 3~4)

기존 강의자료를 딥 탐색한 뒤 확정된 커리큘럼을 회차별 교안 `.md`로 만든다. 수강생 수준과 직무는 프로젝트 `AGENTS.md`와 context를 따른다.

## 시작 전 1회

`using-curriculum` 스킬의 `references/author-intent.md`(헌법)를 읽는다 - 기존 검증 자료 우선, 최소 개선, 원본 밀도가 상한선. 파일에 접근할 수 없으면 이 원칙만 지키고 진행한다.

게이트 스크립트 정본은 `using-curriculum` 스킬에 있다: `${CLAUDE_PLUGIN_ROOT}/skills/using-curriculum/scripts/curriculum_gate.py`(딥 탐색/미디어), 같은 폴더의 `format_scan.py`(2형태 lint). **게이트 통과는 응답에 (실행 명령, 통과 여부, 핵심 출력 라인) 인용으로만 인정.**

## 실행 순서

1. **자료조사(3-1절)** - 새 문장을 쓰기 전에 explore 게이트 산출물부터. 후보 원문 비교 -> `gate-candidates` 통과.
2. **개요 합의(3-2절)** - 2단계 개요를 사용자와 합의하기 전에 본문을 쓰지 않는다.
3. **골격 선택 후 작성(3-3~3-7절)** - 아래 골격 표.
4. **자기검수(3-8절)** - 초안 != 완료. `curriculum-review` 하네스를 제작의 필수 마무리로 돌린다.

## 골격 선택 (먼저 "라이브냐 VOD냐")

| 형태 | 골격 |
|---|---|
| **라이브**(실시간 빌드얼롱) | [`references/template.md`](references/template.md) - 복붙 프롬프트/단계 중심. 자료 많으면 [`references/notion-session-page-template.md`](references/notion-session-page-template.md)(child_page 분리 변형) |
| **VOD**(녹화 클립) | [`references/vod-clip-template.md`](references/vod-clip-template.md) - 매뉴얼형(학습목표/십진헤딩/이미지+표,코드/미션,요약) |
| **VOD 녹화 대본**(완성 클립 -> 강사 음성 원고) | [`references/vod-script-generation.md`](references/vod-script-generation.md) |

## 본문 라우팅

- 조사/이식, 개요, 골격 문법, 콘텐츠 원칙, 안전/도메인 매칭, 자기검수: [`references/authoring.md`](references/authoring.md)
- 라이브 운영(시간/환경/막힘 대처): [`references/live-lecture-operations-tips.md`](references/live-lecture-operations-tips.md), 입문자와 비개발자 대상 설명/전달: [`references/live-lecture-delivery-tips.md`](references/live-lecture-delivery-tips.md)
- Claude Code 실습형 원문 선택: [`templates/claude-code-practice-source-selection.md`](templates/claude-code-practice-source-selection.md)
- 비개발자 바이브코딩 용어 교안: [`references/nondev-vibe-coding-glossary.md`](references/nondev-vibe-coding-glossary.md)
- AI 티 표기/클리셰: `using-curriculum` 스킬의 `references/anti-patterns.md`
- 이미지 출처 우선순위, 생성 규칙, Notion 삽입: `curriculum-notion-sync` 스킬의 `references/image-generation-notion-assets.md`
- Notion 좌표 탐색(딥 탐색 입력 JSON): `curriculum-notion-sync` 스킬의 `references/notion-exploration.md`
