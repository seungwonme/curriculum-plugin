# ntn CLI 레퍼런스

## 멀티 워크스페이스

- 등록 목록: `~/.config/notion/workspaces.json`
- 기본 워크스페이스: `config.json`의 `defaultWorkspaceIds.prod`
- `ntn login`은 기본 워크스페이스를 덮어씀 — 로그인 후 `config.json` 확인
- 토큰: macOS 키체인 저장 (`NOTION_KEYRING=0`이면 `~/.config/notion/auth.json` 파일 방식)
- **AI 에이전트/백그라운드 실행은 keychain 대신 환경변수 토큰을 쓴다** — keychain은 화면 잠금·자동잠금에 막혀 헤드리스에서 `Failed to fetch token from keychain`이 난다(토큰은 등록돼 있어도 못 읽음). `agents-env`의 `NOTION_API_KEY`를 `NOTION_API_TOKEN`으로 주입: `agents-env run NOTION_API_KEY@<tag> -- sh -c 'NOTION_API_TOKEN={{NOTION_API_KEY}} ntn ...'`. integration 토큰이라 그 integration이 연결된 페이지·DB만 접근되니, 대상에 맞는 tag를 고른다(404면 다른 tag). 토큰별 워크스페이스 매핑은 auto-memory `reference_ntn_agent_auth` 참조.
- 워크스페이스 전환: `NOTION_WORKSPACE_ID=<uuid> ntn ...` 환경변수로 지정
- `ntn doctor`는 `NOTION_WORKSPACE_ID`를 무시함. 실제 전환 검증은 `ntn api /v1/users/me`의 `workspace_name`으로 확인
- `/v1/search`는 현재 활성 토큰의 워크스페이스 내 페이지만 반환 (토큰 스코프). api 호출에 403이 나면 해당 워크스페이스 토큰 재발급 필요. MCP가 특정 워크스페이스 DB에 404를 내면 `ntn` CLI + env override로 우회한다.

## 명령어 레퍼런스

아래 명령은 서브커맨드 레퍼런스다. 실제 실행 시에는 항상 `NOTION_WORKSPACE_ID=<workspace-id>`를 앞에 붙인다.

## 쓰기 안전선

Notion은 기본 read-only다. `search/get/query`는 읽기이고, `create/update/PATCH/trash/delete/archive/--allow-deleting-content`는 쓰기다.

쓰기 전에는 대상 워크스페이스, page/database/data-source id, 총 개수, 실행 명령을 사용자에게 보여주고 명시 승인을 받는다.

기존 페이지 쓰기는 직접 REST `GET /v1/pages/<id>`로 제목, 부모, `last_edited_by`, `last_edited_time`을 확인한 뒤 진행한다. 사용자 편집이나 diff 발산이 의심되면 멈추고 기준을 묻는다.

삭제/휴지통/아카이브는 별도 승인 대상이다. 후보 목록, 총 개수, 복구 가능성, 실행 명령을 보여주기 전에는 실행하지 않는다. 휴지통 판정은 `in_trash:true`이고 `archived`가 아니다.

TSV/list를 읽는 반복문 안에서 `ntn api`를 호출할 때는 `< /dev/null`을 붙인다. 그렇지 않으면 루프 입력을 JSON stdin으로 오인해 `Invalid JSON from stdin`이 날 수 있다.

```bash
# Pages
ntn pages get <page-id>                          # 페이지를 Markdown으로 출력
ntn pages get <page-id> --json                   # JSON 출력 (unknown_block_ids 등 진단용)
ntn pages create --content '# Title\n\nBody'     # 새 페이지 생성 (--parent 옵션으로 부모 지정)
ntn pages create --parent page:<id> < page.md    # stdin에서 마크다운 읽어 생성
ntn pages create --parent database:<id> < page.md
ntn pages create --parent data-source:<id> < page.md
ntn pages update <page-id> < page.md             # 페이지 내용 교체 (stdin)
ntn pages update <page-id> --content '...'       # 페이지 내용 교체 (인라인)
ntn pages update <page-id> --allow-deleting-content  # 자식 페이지/DB 삭제 허용
ntn pages trash <page-id>                        # 페이지 휴지통으로 이동 (별도 명시 승인 필수)

# Datasources (DB 쿼리)
ntn datasources resolve <db-id>      # Notion DB ID → data-source ID 변환
ntn datasources query <ds-id> --limit 100 --json # 데이터소스 페이지 목록 조회(기본 limit 25)
ntn datasources query <ds-id> --start-cursor <cursor> --json
ntn datasources query <ds-id> --filter-file filter.json

# Files
ntn files create --filename image.png --content-type image/png < image.png
ntn files create --external-url https://example.com/image.png
ntn files get <upload-id> --json

# Public API 직접 호출
ntn api --method GET /v1/pages/<id>
ntn api --method GET /v1/blocks/<id>/children
ntn api --method POST /v1/search -- 'query=검색어'
ntn api --method POST /v1/data_sources/<ds-id>/query
# inline input 형식: Header:Value, name==value, path=value, path:=json
ntn api --method POST /v1/pages -- 'parent:={"page_id":"..."}' 'properties:={...}'
ntn api --method PATCH /v1/pages/<id> -- 'properties:={"제목":{...}}'  # 지정 속성만 병합, 나머지 보존 (본문 안 건드리고 속성 1개만 외과적 수정)
ntn api --method POST /v1/pages/<id>/move -d '{"parent":{"type":"page_id","page_id":"<parent-page-id>"}}'
ntn api --method GET /v1/pages/<id>/properties/<property-id> page_size==100
ntn api --method GET /v1/data_sources/<ds-id>/templates page_size==100
ntn api --method GET /v1/comments block_id==<page-or-block-id>
ntn api --method POST /v1/comments -d '{"parent":{"page_id":"<page-id>"},"markdown":"검토 의견"}'

# 기타
ntn login / ntn logout
ntn doctor          # CLI 상태 확인 (NOTION_WORKSPACE_ID 무시)
ntn update          # CLI 업데이트
```

## 기존 페이지 update 안전선 — 발산 게이트 (덮어쓰기 방지)

`ntn pages update`는 본문 전체 교체다. 사용자가 노션에서 직접 편집한 내용이 오래된 로컬 .md에 덮여 유실된다 — 우선순위 **노션(사용자 편집) > 로컬 > AI 편집**. 더해 `ntn pages get` 읽기는 hang·0바이트·크로스 오염이 실측돼, 오염된 읽기 위에서 비교하면 거짓 통과한다(비교/검증은 직접 Notion REST API로).

기존 페이지를 파괴적으로 update할 때의 공통 절차는 직접 REST 읽기 → 베이스라인 재취득 → diff 확인 → 발산 시 멈추고 묻기 → 반영 후 round-trip 검증이다. 강의자료 이미지/GIF/북마크 보존처럼 도메인별 자산 규칙은 해당 workflow skill의 reference를 추가로 따른다.

## Markdown 읽기와 정밀 수정

`ntn pages get --json`이나 `GET /v1/pages/<id>/markdown`의 `truncated`, `unknown_block_ids`를 확인한다. unknown block 원인은 대개 페이지 크기 초과, 권한 부족, 미지원 블록(bookmark/embed/link preview 등)이다.

`unknown_block_ids`가 있으면 같은 markdown endpoint에 해당 block id를 넣어 subtree를 다시 읽는다. 권한 문제면 404가 날 수 있으니 누락이 아니라 접근 불가로 구분한다. 회의록 transcript가 필요할 때만 `include_transcript:=true`를 붙인다.

**북마크 자기참조 앵커 함정 (덤프-수정-재반영 루프)**: `ntn pages get`이 북마크 블록을 실제 목적지 URL 대신 자기참조 앵커 `[[bookmark: https://app.notion.com/p/<자기 page-id>#<block-id>]]`로 내보낼 수 있다. `ntn pages update`는 `[[bookmark:]]` 값을 그대로 새 블록으로 만들기 때문에, 이 덤프를 그대로 재반영하면 정상 북마크가 깨진 자기참조 링크로 전량 덮인다(실측: 19페이지 105건 전부 앵커형). 덤프 후 `GET /v1/blocks/<page-id>/children`의 `bookmark.url` 인벤토리로 실제 URL로 치환하고, 반영 전 `rg 'bookmark: *https://app\.notion\.com/p/' <본문.md>` 0건을 확인한다.

기존 페이지 일부만 고칠 때는 전체교체 전에 공식 markdown PATCH의 `update_content`를 우선 검토한다. `old_str`이 0개 또는 여러 곳에 매칭되면 validation error가 나므로, 발산 게이트와 잘 맞는다.

```bash
ntn api --method PATCH /v1/pages/<id>/markdown -d '{"type":"update_content","update_content":{"content_updates":[{"old_str":"기존 문장","new_str":"새 문장"}]}}'
ntn api --method PATCH /v1/pages/<id>/markdown -d '{"type":"replace_content","replace_content":{"new_str":"# 전체 교체 본문"}}'
```

큰 markdown 쓰기는 `allow_async:true`를 넣고, 반환된 task id를 `GET /v1/async_tasks/<task-id>`로 polling한다. `insert_content`, `replace_content_range`는 legacy 경로라 새 작업 기본값으로 삼지 않는다.

## 데이터소스와 속성 조회

`ntn datasources query`는 data-source id를 받는다. database id를 받지 않으므로 먼저 `ntn datasources resolve <db-id>`로 data-source id를 확인한다.

query 기본 limit은 25다. 전수 판단이나 중복 검사는 `--limit 100`과 `--start-cursor` pagination을 같이 쓴다. 복잡한 필터는 shell quoting보다 `--filter-file`이 덜 깨진다. 정렬은 `-s "<property> asc|desc"`를 반복할 수 있고, 순서가 의미 있다.

페이지의 `title`, `rich_text`, `relation`, `people` 같은 긴 속성은 `GET /v1/pages/<id>/properties/<property-id>`가 paginated list를 반환할 수 있다. `GET /v1/pages/<id>`만 보고 25개 초과 relation/people이 전부라고 단정하지 않는다.

데이터소스 템플릿은 `GET /v1/data_sources/<ds-id>/templates`로 확인한다. 템플릿도 페이지라서 template id로 페이지 본문을 읽을 수 있다.

## 블록, 이동, 파일, 댓글

`GET /v1/blocks/<id>/children`은 1단계 children만 반환한다. 중첩 토글, 콜아웃, synced block 내부까지 보려면 `has_children`을 따라 재귀 조회한다.

`PATCH /v1/blocks/<parent>/children`은 한 요청에 children 최대 100개, nesting 최대 2단계다. 위치 지정은 deprecated `after` 대신 `position`을 쓴다.

```bash
ntn api --method PATCH /v1/blocks/<parent-id>/children -d '{"children":[{"type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"추가 문장"}}]}}],"position":{"type":"after_block","after_block":{"id":"<block-id>"}}}'
```

페이지 이동은 wrapper가 아니라 `POST /v1/pages/<id>/move`를 쓴다. 새 부모는 일반 페이지면 `page_id`, DB면 database id가 아니라 `data_source_id`다.

파일 업로드는 `ntn files create`로 staging한 뒤, 필요한 block/page/comment API에서 file upload id를 참조한다. `ntn files list`는 현재 첫 페이지만 반환하므로 전수 목록으로 믿지 않는다. 공개 URL은 `--external-url`로 등록할 수 있다.

댓글 API는 connection의 read/insert comment capability가 꺼져 있으면 403이 난다. 댓글 markdown은 inline formatting만 구조화된다. heading, list, table, fenced code block이 필요한 내용은 댓글이 아니라 페이지 본문에 쓴다.
