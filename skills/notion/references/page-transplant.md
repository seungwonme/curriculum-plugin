# 페이지 간 자료 이식 (이미지·링크·설명) — 같은 워크스페이스

다른 노션 페이지의 이미지·링크·설명을 대상 페이지에 병합하는 절차.

- **이미지: 0.16.0에선 `pages get`이 이미지를 만료 S3 URL로 내보내, 옛 `file://` ref 복사 재연결이 죽었다** (S3·로컬·옛 `file://` 어느 것도 본문 .md에 넣어 `update`하면 빈 이미지 `![]()`로 깨짐). 이미지 이식은 원본을 내려받아 `ntn files create` 업로드 → `ntn api`로 이미지 블록 삽입한다. 앵커 위치 지정·block id 확보는 `curriculum-notion-sync` 스킬의 image-generation-notion-assets reference.
- **텍스트·설명**: 마크다운으로 병합 후 `ntn pages update <dst> < merged.md` (stdin, frontmatter 없이, 전체교체). 먼저 대상 백업 `ntn pages get <dst> > /tmp/orig-dst.md`.
- **북마크 카드**(`<unknown url=… alt="bookmark"/>`)는 `update`로 생성 불가(400) → 인라인 `[라벨](url)`로 변환하거나 그 자리만 노션 UI 수동 추가.
- **⚠️ 이미지 있는 페이지를 `update`(본문 전체 교체)하면 기존 이미지도 유실** → 텍스트만 고칠 땐 이미지를 `ntn api`로 재삽입한다.
