# 페이지 간 자료 이식 (이미지·링크·설명) - 같은 워크스페이스

다른 노션 페이지의 이미지·링크·설명을 대상 페이지에 병합하는 절차.

- **이미지**: `pages get`의 파일 URL은 만료되는 pre-signed URL이므로 장기 참조로 재사용하지 않는다. 원본을 즉시 내려받고 `ntn files create`로 다시 업로드한 뒤 `ntn api`로 이미지 블록을 삽입한다. 앵커 위치와 block ID는 [`ntn-cli.md`](ntn-cli.md)의 "블록, 이동, 파일, 댓글" 절을 따른다.
- **텍스트·설명**: 마크다운으로 병합 후 `ntn pages edit <dst> < merged.md`로 전체 교체한다. 먼저 `ntn pages get <dst> > /tmp/orig-dst.md`로 대상을 백업한다.
- **북마크 카드**(`<unknown url=… alt="bookmark"/>`)는 enhanced Markdown 미지원 블록이다. 인라인 `[라벨](url)`로 변환하거나 그 자리만 Notion UI에서 추가한다.
- **이미지가 있는 페이지**: `pages edit`로 본문 전체를 교체하면 기존 이미지를 유실할 수 있다. 텍스트만 고칠 때는 Markdown `update_content`를 우선하고, 필요한 이미지는 `ntn api`로 재삽입한다.
