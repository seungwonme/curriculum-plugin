# 마크다운 → Notion 블록 변환 규칙

- 본문 마크다운으로 주면 Notion 블록으로 네이티브 변환
- front-matter 없이 본문만 주면 페이지 속성은 보존되고 본문 블록만 교체
- **콜아웃은 `<callout icon="이모지" color="gray_bg"> … </callout>` 문법만 가능.** `<aside>`, `> [!NOTE]`는 콜아웃이 아니라 paragraph/quote로 평탄화됨 (2026-05-29 실증)
- 토글: `<details><summary>제목</summary> … </details>`
- **인용구는 마지막 내용 줄로 끝내고 빈 줄로 닫는다 — 끝에 단독 `>` 줄을 두지 않는다.** 빈 인용 연속 줄이 뒤따르는 문단·콜아웃을 인용 블록으로 흡수해, 같은 문장이 인용구와 원래 위치 두 곳에 렌더된다. 업로드 전 검증: `grep -cE '^[[:space:]]*>[[:space:]]*$' <file>` 이 0.
- 변환 검증: **`ntn pages get <page-id>`로 round-trip** 해서 `<callout>`·`<table>`·`<details>` 개수·균형이 맞는지 본다. (블록 조회 `ntn api …/children`는 **`timeout` 명령으로 감싸면 빈 응답**이 된다 — `timeout` 래핑이 hang의 실제 원인. `| head -c N`으로 SIGPIPE 종료시켜 받는다.)

## 직접 블록 API surgical (전체교체 아닌 블록 단위 편집)

위는 `ntn pages update`의 마크다운 네이티브 변환(본문 전체교체)이다. 이미지 보존이 필요한 부분 편집은 공식 Markdown `update_content`나 블록 API를 사용한다. 발산 게이트, 블록 재귀 조회, 위치 지정과 API 제한은 [`ntn-cli.md`](ntn-cli.md)의 "Markdown 읽기와 정밀 수정", "블록, 이동, 파일, 댓글" 절을 따른다.
