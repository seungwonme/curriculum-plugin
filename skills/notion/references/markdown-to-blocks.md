# 마크다운 -> Notion 블록 변환 규칙

- 본문 마크다운으로 주면 Notion 블록으로 네이티브 변환
- front-matter 없이 본문만 주면 페이지 속성은 보존되고 본문 블록만 교체
- 콜아웃은 `<callout>...</callout>`을 사용한다. 새로 쓸 때는 `<callout icon="이모지" color="gray_bg">...</callout>`처럼 속성을 명시하고, 읽기 도구는 `color`가 생략된 덤프도 허용한다. `<aside>`와 `> [!NOTE]`는 콜아웃으로 취급하지 않는다.
- 토글: `<details><summary>제목</summary> … </details>`
- **인용구는 마지막 내용 줄로 끝내고 빈 줄로 닫는다 — 끝에 단독 `>` 줄을 두지 않는다.** 빈 인용 연속 줄이 뒤따르는 문단·콜아웃을 인용 블록으로 흡수해, 같은 문장이 인용구와 원래 위치 두 곳에 렌더된다. 업로드 전 `rg -n '^[[:space:]]*>[[:space:]]*$' <file>` 결과가 없는지 확인한다.
- 변환 검증: **`ntn pages get <page-id>`로 round-trip** 해서 `<callout>`·`<table>`·`<details>` 개수·균형이 맞는지 본다. (블록 조회 `ntn api …/children`는 **`timeout` 명령으로 감싸면 빈 응답**이 된다 — `timeout` 래핑이 hang의 실제 원인. `| head -c N`으로 SIGPIPE 종료시켜 받는다.)

## 직접 블록 API surgical (전체교체 아닌 블록 단위 편집)

위는 `ntn pages edit`의 마크다운 네이티브 변환(본문 전체교체)이다. 이미지 보존이 필요한 부분 편집은 공식 Markdown `update_content`나 블록 API를 사용한다. 발산 게이트, 블록 재귀 조회, 위치 지정과 API 제한은 [`ntn-cli.md`](ntn-cli.md)의 "Markdown 읽기와 정밀 수정", "블록, 이동, 파일, 댓글" 절을 따른다.
