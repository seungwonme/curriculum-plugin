#!/usr/bin/env python3
"""ntn-diff-viewer: 노션계 마크다운(ntn pages get 덤프) before/after를 렌더링 diff HTML로 만든다.

실행용 스크립트다 — 소스를 읽지 말고 실행하라. 사용법은 --help.

용도: `ntn pages update` 같은 대량 본문 교체 전에 사용자가 브라우저에서
"렌더링된 모습 그대로"의 변경(빨강=삭제/변경, 초록=추가/변경)을 검토할 때 쓴다.
소스 줄 단위 diff 탭도 함께 제공하며, 렌더링된 양쪽 문서는 공용 스크롤바 하나로 움직인다.

입력: OLD/NEW 각각 .md 파일 하나 또는 디렉토리(상대 경로가 같은 *.md끼리 짝짓기).
지원 문법: 헤딩/불렛/번호/체크박스/인용/파이프 표/HTML 표/코드펜스/이미지/frontmatter/
<callout>/<columns>/<column>/<video>/<mention-page>/[[bookmark:]]/<unknown>/<file>/<database>.
상대 경로 이미지는 각 파일이 있는 디렉토리 기준으로 찾는다(없으면 placeholder).
핸들러 없는 태그는 문단으로 노출되므로 실행 끝에 태그 이름을 경고로 알린다.
"""

import argparse, difflib, fnmatch, hashlib, html, json, pathlib, re, struct, sys


# inline()은 html.escape 뒤에 돌기도 해서 `\>`가 `\&gt;`로 도착한다. 엔티티도 같이 푼다.
ESCAPED = re.compile(r"\\(&(?:gt|lt|amp|quot|#\d+);|[\\`*_{}\[\]()#+\-.!~<>|])")
BR = re.compile(r"&lt;br\s*/?&gt;")


def inline(s):
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(
        r"(?<!\!)\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" target="_blank">\1</a>',
        s,
    )
    # 노션 덤프는 [ ] ~ > - 를 백슬래시로 이스케이프해 내보내고 줄바꿈을 <br>로 남긴다.
    # 그대로 두면 표와 콜아웃에 `\[10:00\] \~`, `<br>`이 노출돼 정작 볼 변경을 가린다.
    # <code> 안은 사용자가 실제로 칠 문자열이라 손대지 않는다.
    kept = []

    def stash(m):
        kept.append(m.group(0))
        return f"\x00{len(kept) - 1}\x00"

    s = re.sub(r"<code>.*?</code>", stash, s)
    s = BR.sub("<br>", ESCAPED.sub(r"\1", s))
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], s)


def image_size(path):
    try:
        data = path.read_bytes()
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            return struct.unpack(">II", data[16:24])
        if data.startswith(b"\xff\xd8"):
            index, starts = (
                2,
                {
                    0xC0,
                    0xC1,
                    0xC2,
                    0xC3,
                    0xC5,
                    0xC6,
                    0xC7,
                    0xC9,
                    0xCA,
                    0xCB,
                    0xCD,
                    0xCE,
                    0xCF,
                },
            )
            while index + 8 < len(data):
                if data[index] != 0xFF:
                    index += 1
                    continue
                marker = data[index + 1]
                index += 2
                if marker in (0xD8, 0xD9):
                    continue
                length = int.from_bytes(data[index : index + 2], "big")
                if marker in starts:
                    return (
                        int.from_bytes(data[index + 5 : index + 7], "big"),
                        int.from_bytes(data[index + 3 : index + 5], "big"),
                    )
                index += length
    except OSError:
        pass
    return None


def img_tag(cap, src, size=None):
    """노션 덤프의 S3 이미지는 서명 URL이라 몇 시간 뒤 만료된다. 만료되면 빈 상자가
    자리만 차지해 정작 변경된 텍스트가 화면 밖으로 밀리므로, 로드 실패를 alt와
    .broken 표시로 드러내고 높이는 CSS가 줄인다."""
    dimensions = f' width="{size[0]}" height="{size[1]}"' if size else ""
    alt = html.escape(cap or "이미지", quote=True)
    fig = (
        f'<figure><img loading="lazy"{dimensions} alt="{alt}" '
        f'src="{html.escape(src, quote=True)}" '
        f"onerror=\"this.classList.add('broken')\">"
    )
    if cap:
        fig += f"<figcaption>{inline(html.escape(cap))}</figcaption>"
    return fig + "</figure>"


SEP = re.compile(r":?-{2,}:?$")


def render(text, base_dir, changed=None, cls="", seen=None, unsupported=None):
    """base_dir: 상대 경로 이미지를 해석할 기준 디렉토리(그 md 파일의 부모).

    unsupported: 미지원 태그를 담을 set. 핸들러가 없는 `<tag>` 줄은 문단으로 떨어져
    화면에 raw 태그로 노출되므로, 여기 모아 실행 로그로 알린다(조용한 오렌더 방지)."""
    changed, seen = changed or {}, seen if seen is not None else set()
    unsupported = unsupported if unsupported is not None else set()
    out, lines, pending = [], text.splitlines(), []
    i, in_code, in_table, list_open = 0, False, False, None

    def unique(values):
        return list(dict.fromkeys(value for value in values if value))

    def line_ids(*indices):
        return unique(changed.get(index) for index in indices)

    def remember(ids):
        pending.extend(
            value for value in ids if value not in seen and value not in pending
        )

    def take(ids):
        values = unique([*pending, *ids])
        pending.clear()
        return values

    def ids_attr(ids):
        return html.escape(" ".join(ids), quote=True)

    def controls(ids):
        fresh = [value for value in ids if value not in seen]
        seen.update(fresh)
        return "".join(
            f'<label class="inline-revert-control" title="이 변경을 되돌리기 요청에 포함">'
            f'<input class="inline-revert-check" type="checkbox" data-change-id="{html.escape(value, quote=True)}" '
            f'aria-label="이 변경 되돌리기"><span>되돌림</span></label>'
            for value in fresh
        )

    def mk(s, ids):
        if not ids or not cls:
            return s
        return (
            f'<div class="mk {cls} review-change" data-change-ids="{ids_attr(ids)}">'
            f"{controls(ids)}{s}</div>"
        )

    def list_item(content, ids, extra=""):
        if not ids or not cls:
            return (
                f'<li class="{extra}">{content}</li>'
                if extra
                else f"<li>{content}</li>"
            )
        classes = " ".join(filter(None, (extra, cls, "review-change")))
        return (
            f'<li class="{classes}" data-change-ids="{ids_attr(ids)}">'
            f"{controls(ids)}{content}</li>"
        )

    def close_list():
        nonlocal list_open
        if list_open:
            out.append(f"</{list_open}>")
            list_open = None

    # `ntn pages get` 덤프는 page 속성을 frontmatter로 얹는다. 본문 문단으로 흘리면
    # 첫 화면이 `title: ...`로 시작해 실제 본문처럼 보이므로 메타 상자로 접어 둔다.
    if lines and lines[0].strip() == "---":
        end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
        if end is not None:
            meta_ids = take(line_ids(*range(0, end + 1)))
            body = "<br>".join(
                html.escape(line.strip()) for line in lines[1:end] if line.strip()
            )
            out.append(mk(f'<div class="fm">{body}</div>', meta_ids))
            i = end + 1

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        ids = line_ids(i)
        if s.startswith("```"):
            close_list()
            remember(ids)
            out.append('<pre class="code">' if not in_code else "</pre>")
            in_code = not in_code
            i += 1
            continue
        if in_code:
            out.append(mk(html.escape(raw), take(ids)))
            i += 1
            continue
        # HTML 표 통과 (colgroup 고정폭 버림, 셀 단위 diff 색)
        if s.startswith("<table") or in_table:
            if s.startswith("<table"):
                close_list()
                in_table = True
            if s.startswith("</table>"):
                in_table = False
            if not s.startswith(("<colgroup", "<col ", "</colgroup")):
                line = inline(s)
                if ids and cls and re.match(r"<t[dh][ >]", s):
                    visible_ids = take(ids)
                    line = re.sub(
                        r"^<(t[dh])([^>]*)>",
                        lambda m: (
                            f'<{m.group(1)} class="{cls} review-change"{m.group(2)} '
                            f'data-change-ids="{ids_attr(visible_ids)}">{controls(visible_ids)}'
                        ),
                        line,
                        count=1,
                    )
                elif ids:
                    remember(ids)
                out.append(line)
            i += 1
            continue
        # 마크다운 파이프 표 (블록 단위로 모아 표 안 어느 줄이든 변경이면 통째 하이라이트)
        if s.startswith("|") and s.count("|") >= 2:
            close_list()
            start = i
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            block_ids = take(line_ids(*range(start, i)))
            rows, has_sep = [], False
            for ln in block:
                cells = [c.strip() for c in ln.strip("|").split("|")]
                if cells and all(SEP.fullmatch(c) for c in cells):
                    has_sep = True
                    continue
                rows.append(cells)
            t = ['<table class="md">']
            for ri, r in enumerate(rows):
                tg = "th" if has_sep and ri == 0 else "td"
                t.append(
                    "<tr>"
                    + "".join(f"<{tg}>{inline(html.escape(c))}</{tg}>" for c in r)
                    + "</tr>"
                )
            t.append("</table>")
            out.append(mk("".join(t), block_ids))
            continue
        if s.startswith(("<details", "</details", "<summary", "</summary")):
            remember(ids)
            out.append(raw)
            i += 1
            continue
        # 노션 다단 컬럼. 핸들러가 없으면 태그가 문단으로 노출돼 변경보다 눈에 띈다.
        if s.startswith("<columns"):
            close_list()
            remember(ids)
            out.append('<div class="ncols">')
            i += 1
            continue
        if s == "</columns>":
            close_list()
            remember(ids)
            out.append("</div>")
            i += 1
            continue
        m = re.match(r'<column(?:\s+ratio="([\d.]+)")?\s*/?>', s)
        if m:
            close_list()
            remember(ids)
            out.append(f'<div class="ncol" style="flex:{m.group(1) or "50"}">')
            i += 1
            continue
        if s == "</column>":
            close_list()
            remember(ids)
            out.append("</div>")
            i += 1
            continue
        if s.startswith(("<colgroup", "<col ", "</colgroup")):
            remember(ids)
            i += 1
            continue
        m = re.match(r'<callout icon="([^"]*)" color="([^"]*)">', s)
        if m:
            close_list()
            visible_ids = take(ids)
            attrs = (
                f' review-change" data-change-ids="{ids_attr(visible_ids)}'
                if visible_ids
                else ""
            )
            out.append(
                f'<div class="co co-{m.group(2)}{attrs}">{controls(visible_ids)}<span class="ic">{m.group(1)}</span><div>'
            )
            i += 1
            continue
        if s == "</callout>":
            remember(ids)
            close_list()
            out.append("</div></div>")
            i += 1
            continue
        if s in ("<empty-block/>", "<empty-block />"):
            remember(ids)
            i += 1
            continue
        m = re.match(r'<video src="([^"]+)"', s)
        if m:
            close_list()
            out.append(
                mk(
                    f'<div class="bm">▶️ <a href="{m.group(1)}" target="_blank">{m.group(1)}</a></div>',
                    take(ids),
                )
            )
            i += 1
            continue
        m = re.match(r'<mention-page url="([^"]+)"', s)
        if m:
            close_list()
            out.append(
                mk(
                    f'<div class="bm">📄 <a href="{m.group(1)}" target="_blank">{m.group(1)}</a></div>',
                    take(ids),
                )
            )
            i += 1
            continue
        # 하위 페이지 링크. 제목이 태그 안에 있으므로 제목을 링크 텍스트로 쓴다.
        m = re.match(r'<page url="([^"]+)"\s*>(.*?)</page>', s)
        if m:
            close_list()
            title = html.escape(m.group(2)) or m.group(1)
            out.append(
                mk(
                    f'<div class="bm">📄 <a href="{m.group(1)}" target="_blank">{title}</a></div>',
                    take(ids),
                )
            )
            i += 1
            continue
        m = re.match(r"\[\[bookmark:\s*([^\]]+)\]\]", s)
        if m:
            close_list()
            u = m.group(1).strip()
            out.append(
                mk(
                    f'<div class="bm">🔖 <a href="{u}" target="_blank">{u}</a></div>',
                    take(ids),
                )
            )
            i += 1
            continue
        # ntn이 못 푼 블록은 alt에 원래 종류가 담겨 나온다(bookmark, external_object_instance 등).
        # 종류를 가리지 않고 링크 한 줄로 접어야 태그가 본문에 노출되지 않는다.
        m = re.search(r'<unknown url="([^"]+)"[^>]*alt="([^"]*)"', s)
        if m:
            close_list()
            u, kind = m.group(1), m.group(2)
            label = (
                ""
                if kind == "bookmark"
                else f' <span class="r">{html.escape(kind)}</span>'
            )
            out.append(
                mk(
                    f'<div class="bm">🔖 <a href="{u}" target="_blank">{u}</a>{label}</div>',
                    take(ids),
                )
            )
            i += 1
            continue
        if s.startswith(("<file ", "<embed ")):
            close_list()
            out.append(mk('<div class="bm">📎 첨부 파일(원본 보존)</div>', take(ids)))
            i += 1
            continue
        if s.startswith("<database"):
            close_list()
            out.append(
                mk('<div class="bm">🗄️ 인라인 데이터베이스(원본 보존)</div>', take(ids))
            )
            i += 1
            continue
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            close_list()
            cap, src, visible_ids = m.group(1), m.group(2), take(ids)
            if src.startswith(("http://", "https://", "data:", "file://")):
                out.append(mk(img_tag(cap, src), visible_ids))
            else:
                p = (base_dir / src).resolve() if base_dir else None
                if p and p.exists():
                    out.append(
                        mk(img_tag(cap, f"file://{p}", image_size(p)), visible_ids)
                    )
                else:
                    out.append(
                        mk(
                            f'<div class="bm">🖼️ {inline(html.escape(cap)) or "이미지"} ({html.escape(src)} 없음)</div>',
                            visible_ids,
                        )
                    )
            i += 1
            continue
        if s == "---":
            close_list()
            out.append(mk("<hr>", take(ids)))
            i += 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", s)
        if m:
            close_list()
            lv = min(len(m.group(1)) + 2, 6)
            out.append(
                mk(f"<h{lv}>{inline(html.escape(m.group(2)))}</h{lv}>", take(ids))
            )
            i += 1
            continue
        if s.startswith("> "):
            close_list()
            out.append(
                mk(f"<blockquote>{inline(html.escape(s[2:]))}</blockquote>", take(ids))
            )
            i += 1
            continue
        m = re.match(r"- \[( |x)\]\s*(.*)", s)
        if m:
            if list_open != "ul":
                close_list()
                out.append("<ul>")
                list_open = "ul"
            box = "☑" if m.group(1) == "x" else "☐"
            out.append(
                list_item(f"{box} {inline(html.escape(m.group(2)))}", take(ids), "task")
            )
            i += 1
            continue
        if s.startswith("- "):
            if list_open != "ul":
                close_list()
                out.append("<ul>")
                list_open = "ul"
            out.append(list_item(inline(html.escape(s[2:])), take(ids)))
            i += 1
            continue
        m = re.match(r"(\d+)\.\s+(.*)", s)
        if m:
            if list_open != "ol":
                close_list()
                out.append("<ol>")
                list_open = "ol"
            out.append(list_item(inline(html.escape(m.group(2))), take(ids)))
            i += 1
            continue
        if not s:
            close_list()
            remember(ids)
            i += 1
            continue
        close_list()
        tag = re.match(r"</?([a-zA-Z][\w-]*)[\s/>]", s)
        if tag:
            unsupported.add(tag.group(1))
        out.append(mk(f"<p>{inline(html.escape(s))}</p>", take(ids)))
        i += 1
    close_list()
    if pending:
        out.append(mk("<span>구조 변경</span>", take([])))
    return "\n".join(out)


def diff_data(bt, dt, prefix):
    a, b = bt.splitlines(), dt.splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    rows, adds, dels, changes = [], 0, 0, []
    del_map, ins_map = {}, {}

    def row(ln1, t1, c1, ln2, t2, c2):
        rows.append(
            f'<tr><td class="ln">{ln1}</td><td class="tx {c1}">{html.escape(t1)}</td>'
            f'<td class="ln">{ln2}</td><td class="tx {c2}">{html.escape(t2)}</td></tr>'
        )

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            change_id = f"{prefix}:h{len(changes) + 1:02d}"
            old_text, new_text = "\n".join(a[i1:i2]), "\n".join(b[j1:j2])
            changes.append(
                {
                    "change_id": change_id,
                    "kind": tag,
                    "before": {
                        "line_start": i1 + 1 if i2 > i1 else None,
                        "line_end": i2 if i2 > i1 else None,
                        "text": old_text,
                        "sha256": hashlib.sha256(old_text.encode()).hexdigest(),
                    },
                    "after": {
                        "line_start": j1 + 1 if j2 > j1 else None,
                        "line_end": j2 if j2 > j1 else None,
                        "text": new_text,
                        "sha256": hashlib.sha256(new_text.encode()).hexdigest(),
                    },
                    "context_before": a[i1 - 1] if i1 else "",
                    "context_after": a[i2] if i2 < len(a) else "",
                }
            )
            del_map.update({index: change_id for index in range(i1, i2)})
            ins_map.update({index: change_id for index in range(j1, j2)})
        if tag == "equal":
            n = i2 - i1
            # 동일 구간이 길면 앞뒤 3줄만 남기고 접는다(diff 가독성 관례)
            ks = (
                list(range(n))
                if n <= 8
                else list(range(3)) + [None] + list(range(n - 3, n))
            )
            for k in ks:
                if k is None:
                    rows.append(
                        f'<tr class="skip"><td colspan="4">동일 {n - 6}줄 생략</td></tr>'
                    )
                else:
                    row(i1 + k + 1, a[i1 + k], "", j1 + k + 1, b[j1 + k], "")
        elif tag == "delete":
            dels += i2 - i1
            for k in range(i1, i2):
                row(k + 1, a[k], "del", "", "", "")
        elif tag == "insert":
            adds += j2 - j1
            for k in range(j1, j2):
                row("", "", "", k + 1, b[k], "ins")
        else:
            dels += i2 - i1
            adds += j2 - j1
            for k in range(max(i2 - i1, j2 - j1)):
                l = (i1 + k + 1, a[i1 + k], "del") if i1 + k < i2 else ("", "", "")
                r = (j1 + k + 1, b[j1 + k], "ins") if j1 + k < j2 else ("", "", "")
                row(*l, *r)
    return (
        f'<table class="diff">{"".join(rows)}</table>',
        adds,
        dels,
        del_map,
        ins_map,
        changes,
    )


def chars(t):
    """본문 글자수(공백/태그/코드펜스 제외) - 분량 변화 표시용."""
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>|\[\[bookmark:[^\]]*\]\]|!\[[^\]]*\]\([^)]*\)", "", t)
    return len(re.sub(r"\s", "", t))


def collect_pairs(old, new, excludes):
    """(key, old_path|None, new_path|None) 목록. 디렉토리면 상대 경로가 같은 *.md끼리 짝."""
    if old.is_file() and new.is_file():
        return [(new.stem, old, new)]
    if not (old.is_dir() and new.is_dir()):
        sys.exit(
            f"오류: OLD와 NEW는 둘 다 파일이거나 둘 다 디렉토리여야 한다. OLD={old} NEW={new}"
        )

    def index(d):
        m = {}
        for p in sorted(d.rglob("*.md")):
            rel = str(p.relative_to(d))
            if any(fnmatch.fnmatch(rel, pat) for pat in excludes):
                continue
            m[rel] = p
        return m

    om, nm = index(old), index(new)
    keys = sorted(set(om) | set(nm))
    if not keys:
        sys.exit(f"오류: 비교할 *.md가 없다. OLD={old} NEW={new} (--exclude 패턴 확인)")
    return [(k[:-3], om.get(k), nm.get(k)) for k in keys]


JS = """document.addEventListener('click', function(event) {
  var img = event.target;
  if (img.tagName === 'IMG' && img.closest('.doc')) img.classList.toggle('expanded');
});

// 변경 없는 블록(주로 스크린샷 연속)이 길면 실제 변경이 스크롤 밖으로 밀린다.
// 훑을 때는 변경을 품은 최상위 블록만 남긴다.
document.addEventListener('change', function(event) {
  var box = event.target;
  if (!box.classList.contains('only-changes-check')) return;
  box.closest('section').querySelectorAll('.doc').forEach(function(doc) {
    Array.prototype.forEach.call(doc.children, function(node) {
      var keep = node.classList.contains('review-change') || node.querySelector('.review-change');
      node.classList.toggle('hidden-unchanged', box.checked && !keep);
    });
  });
});

function tab(btn, which) {
  var sec = btn.closest('section');
  sec.querySelectorAll('.tabs button').forEach(function(b){ var on = b === btn; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
  sec.querySelectorAll('.view').forEach(function(v){ v.hidden = !v.classList.contains(which); });
}

(function() {
  var dataNode = document.getElementById('revert-request-data');
  if (!dataNode) return;
  var meta = JSON.parse(dataNode.textContent);
  var changes = meta.changes;
  var selected = new Set();
  var bar = document.getElementById('revert-actions');
  var count = document.getElementById('revert-count');
  var position = document.getElementById('change-position');
  var prevButton = document.getElementById('change-prev');
  var nextButton = document.getElementById('change-next');
  var blocks = Array.from(document.querySelectorAll('.review-change'));
  var inputs = Array.from(document.querySelectorAll('.inline-revert-check'));
  var navLinks = Array.from(document.querySelectorAll('nav a[data-section-id]'));
  var changeById = Object.create(null);
  var targetById = Object.create(null);
  var currentIndex = -1;
  var statusTimer;

  changes.forEach(function(change, index) {
    changeById[change.change_id] = change;
    change._index = index;
  });
  blocks.forEach(function(block) {
    (block.dataset.changeIds || '').split(' ').filter(Boolean).forEach(function(id) {
      if (!targetById[id]) targetById[id] = block;
    });
  });

  function blockIds(block) {
    return (block.dataset.changeIds || '').split(' ').filter(Boolean);
  }

  function updateBlocks() {
    blocks.forEach(function(block) {
      var ids = blockIds(block);
      block.classList.toggle('revert-selected', ids.some(function(id) { return selected.has(id); }));
    });
  }

  function setActiveSection(sectionId) {
    navLinks.forEach(function(link) {
      var active = link.dataset.sectionId === sectionId;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    var activeLink = navLinks.find(function(link) { return link.dataset.sectionId === sectionId; });
    if (activeLink) activeLink.scrollIntoView({block:'nearest', inline:'nearest'});
  }

  function syncCurrentToSection(sectionId) {
    setActiveSection(sectionId);
    if (currentIndex >= 0 && changes[currentIndex].section_id === sectionId) return;
    var index = changes.findIndex(function(change) { return change.section_id === sectionId; });
    if (index >= 0) setCurrent(index, false);
  }

  function updateNavBadges() {
    var counts = Object.create(null);
    selected.forEach(function(id) {
      var change = changeById[id];
      if (change) counts[change.section_id] = (counts[change.section_id] || 0) + 1;
    });
    navLinks.forEach(function(link) {
      var value = counts[link.dataset.sectionId] || 0;
      var badge = link.querySelector('.selection-badge');
      badge.hidden = value === 0;
      badge.textContent = '선택 ' + value;
      link.classList.toggle('has-selection', value > 0);
    });
  }

  function setCurrent(index, shouldScroll) {
    if (!changes.length) {
      position.textContent = '변경 없음';
      prevButton.disabled = true;
      nextButton.disabled = true;
      return;
    }
    currentIndex = (index + changes.length) % changes.length;
    var change = changes[currentIndex];
    blocks.forEach(function(block) {
      block.classList.toggle('review-current', blockIds(block).includes(change.change_id));
    });
    position.textContent = '변경 ' + (currentIndex + 1) + '/' + changes.length + ' · ' + change.clip;
    setActiveSection(change.section_id);
    if (!shouldScroll) return;
    var target = targetById[change.change_id];
    if (target) {
      var section = target.closest('section');
      var rendered = section && section.querySelector('.v-prev');
      if (rendered && rendered.hidden) tab(section.querySelector('.tabs button'), 'v-prev');
      target.scrollIntoView({block:'center', inline:'nearest'});
    }
    history.replaceState(null, '', '#' + change.section_id);
  }

  function updateBar() {
    count.textContent = '선택 ' + selected.size + '개';
    bar.classList.toggle('show', selected.size > 0);
  }

  function select(changeId, checked) {
    checked ? selected.add(changeId) : selected.delete(changeId);
    inputs.forEach(function(input) {
      if (input.dataset.changeId === changeId) input.checked = checked;
    });
    updateBlocks();
    updateNavBadges();
    updateBar();
  }

  function payload() {
    var selections = meta.changes.filter(function(change) { return selected.has(change.change_id); });
    return {
      schema: 'notion-revert-request/v1',
      generated_at: new Date().toISOString(),
      intent: 'restore_before',
      source: meta.source,
      selection_count: selections.length,
      selections: selections
    };
  }

  function requestJson() { return JSON.stringify(payload(), null, 2); }
  function showStatus(message) {
    count.textContent = message;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(updateBar, 1600);
  }

  inputs.forEach(function(input) {
    input.addEventListener('change', function() { select(input.dataset.changeId, input.checked); });
  });

  prevButton.addEventListener('click', function() { setCurrent(currentIndex - 1, true); });
  nextButton.addEventListener('click', function() { setCurrent(currentIndex + 1, true); });
  document.addEventListener('keydown', function(event) {
    if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return;
    var target = event.target;
    var typing = target && (target.isContentEditable || target.tagName === 'TEXTAREA'
      || target.tagName === 'SELECT' || (target.tagName === 'INPUT' && target.type !== 'checkbox'));
    if (typing) return;
    var key = event.key.toLowerCase();
    if (key === 'n') { event.preventDefault(); setCurrent(currentIndex + (event.shiftKey ? -1 : 1), true); }
    if (key === 'p') { event.preventDefault(); setCurrent(currentIndex - 1, true); }
  });
  navLinks.forEach(function(link) {
    link.addEventListener('click', function() {
      var index = changes.findIndex(function(change) { return change.section_id === link.dataset.sectionId; });
      if (index >= 0) setCurrent(index, false);
    });
  });

  if ('IntersectionObserver' in window) {
    var visibleSections = new Set();
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) visibleSections.add(entry.target);
        else visibleSections.delete(entry.target);
      });
      var nearest = Array.from(visibleSections).sort(function(a, b) {
        return Math.abs(a.getBoundingClientRect().top) - Math.abs(b.getBoundingClientRect().top);
      })[0];
      if (nearest) syncCurrentToSection(nearest.id);
    }, {rootMargin:'-96px 0px -65% 0px', threshold:[0, 0.01]});
    document.querySelectorAll('main > section').forEach(function(section) { observer.observe(section); });
  }

  document.getElementById('revert-clear').addEventListener('click', function() {
    Array.from(selected).forEach(function(changeId) { select(changeId, false); });
  });

  document.getElementById('revert-download').addEventListener('click', function() {
    var blob = new Blob([requestJson()], {type:'application/json'});
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = 'part3-revert-request-' + new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19) + '.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function() { URL.revokeObjectURL(url); }, 0);
    showStatus('파일 생성 완료');
  });

  document.getElementById('revert-copy').addEventListener('click', async function() {
    var value = requestJson();
    try {
      await navigator.clipboard.writeText(value);
    } catch (_) {
      var area = document.createElement('textarea');
      area.value = value;
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      area.remove();
    }
    showStatus('클립보드 복사 완료');
  });

  var hashSection = decodeURIComponent(location.hash.slice(1));
  var initialIndex = changes.findIndex(function(change) { return change.section_id === hashSection; });
  setCurrent(initialIndex >= 0 ? initialIndex : 0, false);
  updateNavBadges();

  window.__inlineRevert = {
    payload: payload,
    selected: selected,
    select: select,
    navigate: setCurrent,
    current: function() { return changes[currentIndex] || null; }
  };
})();"""

CSS = """
:root { color-scheme:light; --bg:#f5f7fa; --surface:#fff; --fg:#1f2937; --mut:#667085; --line:#dfe3ea; --pane:#f8fafc; --code:#f2f4f7; --acc:#2563eb; --current:#d97706; --del:#b42318; --del-soft:#fff1f0; --ins:#067647; --ins-soft:#ecfdf3; --shadow:0 1px 3px rgba(16,24,40,.08); --gray:#f1f1ef; --blue:#e7f0fd; --red:#fdebec; }
@media (prefers-color-scheme: dark) { :root { color-scheme:dark; --bg:#101114; --surface:#181a1f; --fg:#eceef2; --mut:#a0a7b4; --line:#30343c; --pane:#202329; --code:#252932; --acc:#8ab4ff; --current:#fbbf24; --del:#ff9292; --del-soft:#351d22; --ins:#79dba5; --ins-soft:#173427; --shadow:0 1px 3px rgba(0,0,0,.4); --gray:#252525; --blue:#1b2a41; --red:#3a2224; } }
* { box-sizing:border-box } body { margin:0; font:15px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",Pretendard,sans-serif; background:var(--bg); color:var(--fg) }
header { position:sticky; top:0; background:var(--surface); border-bottom:1px solid var(--line); padding:12px clamp(16px,3vw,40px); box-shadow:var(--shadow); z-index:9 }
.header-row { display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px }
header h1 { font-size:17px; line-height:1.35; margin:0 }
.change-nav { display:flex; align-items:center; gap:6px; flex:none }
.change-nav button { min-height:32px; padding:4px 10px; border:1px solid var(--line); border-radius:8px; background:var(--pane); color:var(--fg); cursor:pointer }
.change-nav button:hover { color:var(--acc); border-color:var(--acc) }
.change-nav button:disabled { cursor:not-allowed; opacity:.45 }
.change-nav kbd { display:inline-flex; align-items:center; justify-content:center; min-width:20px; height:20px; margin:0 2px; border:1px solid var(--line); border-bottom-width:2px; border-radius:5px; background:var(--surface); color:var(--mut); font:11px/1 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif }
.change-position { min-width:145px; color:var(--mut); text-align:center; font-size:12px; font-variant-numeric:tabular-nums }
nav { display:flex; flex-wrap:nowrap; gap:6px; overflow-x:auto; padding-bottom:4px; scrollbar-width:thin }
nav a { flex:none; display:inline-flex; align-items:center; gap:4px; min-height:32px; font-size:12px; text-decoration:none; color:var(--fg); background:var(--pane); border:1px solid var(--line); border-radius:999px; padding:3px 10px }
nav a:hover { color:var(--acc); border-color:var(--acc) }
nav a.active { color:var(--acc); border-color:var(--acc); background:var(--blue); box-shadow:0 0 0 2px color-mix(in srgb,var(--acc) 10%,transparent) }
nav a.has-selection:not(.active) { border-color:color-mix(in srgb,var(--acc) 45%,var(--line)) }
nav a .r { color:var(--mut) }
.selection-badge { margin-left:2px; padding:1px 6px; border-radius:999px; background:var(--acc); color:#fff; font-size:10px; font-weight:700; font-variant-numeric:tabular-nums }
main { padding:24px clamp(16px,3vw,40px); max-width:1920px; margin:0 auto }
section { scroll-margin-top:90px; margin-bottom:28px; border:1px solid var(--line); border-radius:16px; padding:18px; background:var(--surface); box-shadow:var(--shadow) }
h2 { display:flex; flex-wrap:wrap; align-items:baseline; gap:8px; font-size:20px; margin:0 } h2 small { color:var(--mut); background:var(--code); border-radius:999px; padding:2px 8px; font-weight:400; font-size:13px }
.tabs { display:inline-flex; gap:3px; margin:12px 0; padding:3px; border:1px solid var(--line); border-radius:10px; background:var(--pane) }
.tabs button { min-height:34px; font:13px inherit; padding:5px 12px; border:0; background:transparent; color:var(--mut); border-radius:7px; cursor:pointer }
.tabs button:hover { color:var(--fg) }
.tabs button.on { background:var(--surface); box-shadow:var(--shadow); font-weight:700; color:var(--acc) }
.tabs button:focus-visible, nav a:focus-visible, .change-nav button:focus-visible { outline:2px solid var(--acc); outline-offset:2px }
.tabs .st { font-size:11px; color:var(--mut) }
.dwrap { border:1px solid var(--line); border-radius:12px; max-height:82vh; overflow:auto }
table.diff { width:100%; border-collapse:collapse; font:12px/1.55 "SF Mono",Menlo,monospace; table-layout:fixed }
table.diff td { vertical-align:top; padding:0 6px; border:none }
table.diff td.tx { white-space:pre-wrap; word-break:break-all }
table.diff td.ln { width:40px; color:var(--mut); text-align:right; user-select:none; background:var(--pane); font-size:11px }
table.diff td.del { background:rgba(225,60,60,.13) }
table.diff td.ins { background:rgba(60,175,90,.14) }
table.diff tr.skip td { color:var(--mut); text-align:center; background:var(--pane); padding:3px; font-size:11px }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:0; max-height:82vh; overflow:auto; background:var(--surface); border:1px solid var(--line); border-radius:12px; scrollbar-color:var(--mut) transparent }
.pane { min-width:0; background:var(--surface) }
.pane + .pane { border-left:1px solid var(--line) }
.pane > h3 { position:sticky; top:0; z-index:2; display:flex; align-items:center; gap:7px; font-size:13px; margin:0; padding:10px 16px; border-bottom:1px solid var(--line); background:var(--pane) }
.pane > h3::before { content:""; width:8px; height:8px; flex:none; border-radius:50%; background:currentColor }
.pane > h3 small { color:var(--mut); font-size:11px; font-weight:500 }
.pane:first-child > h3 { color:var(--del); background:var(--del-soft) }
.pane:last-child > h3 { color:var(--ins); background:var(--ins-soft) }
.doc { background:var(--surface); padding:18px 20px 28px }
@media (max-width:1100px) { .cols { grid-template-columns:1fr } .pane + .pane { border-left:0; border-top:1px solid var(--line) } .pane > h3 { position:static } }
@media (max-width:700px) { header { padding:10px 12px } .header-row { align-items:flex-start; flex-direction:column } .change-nav { width:100% } .change-nav button { flex:1 } .change-position { min-width:0 } main { padding:12px } section { padding:14px 12px; border-radius:12px } .doc { padding:14px } }
@media (pointer:coarse) { nav a, .tabs button, .change-nav button { min-height:44px } }
.doc h3 { font-size:17px; margin:18px 0 6px } .doc h4 { font-size:15px; margin:14px 0 4px } .doc h5,.doc h6 { font-size:14px; margin:12px 0 4px }
.doc p { margin:6px 0 } .doc ul,.doc ol { margin:6px 0; padding-left:22px } .doc li { margin:3px 0 }
.doc li.task { list-style:none; margin-left:-18px }
.doc hr { border:none; border-top:1px solid var(--line); margin:16px 0 }
.doc blockquote { border-left:3px solid var(--acc); margin:8px 0; padding:2px 12px }
.doc code { background:var(--code); border-radius:4px; padding:1px 5px; font:12.5px "SF Mono",Menlo,monospace }
.doc pre.code { background:var(--code); border-radius:8px; padding:12px; overflow:auto; font:12.5px/1.6 "SF Mono",Menlo,monospace; white-space:pre-wrap; word-break:break-all }
.doc pre.code .mk { display:block }
.doc table { border-collapse:collapse; margin:8px 0; width:100%; font-size:13.5px }
.doc td, .doc th { border:1px solid var(--line); padding:5px 9px; vertical-align:top; text-align:left }
.doc th { background:var(--code); font-weight:600 }
.doc figure { margin:10px 0 }
/* 노션 덤프는 이미지가 많아 원본 크기로 두면 변경된 텍스트가 스크롤 밖으로 밀린다.
   기본은 한 화면에 앞뒤 텍스트가 같이 보이는 높이로 줄이고, 클릭하면 원본으로 편다. */
.doc img { max-width:100%; max-height:240px; width:auto; height:auto; object-fit:contain; object-position:left top; border-radius:8px; border:1px solid var(--line); cursor:zoom-in }
.doc img.expanded { max-height:none; cursor:zoom-out }
.doc img.broken { min-height:32px; max-height:32px; width:100%; object-fit:none; border-style:dashed; background:var(--code); font-size:12px; color:var(--mut) }
.doc figcaption { font-size:12px; color:var(--mut); margin-top:3px }
.fm { margin:0 0 10px; padding:6px 10px; border:1px dashed var(--line); border-radius:8px; background:var(--pane); color:var(--mut); font-size:12px; line-height:1.5 }
.only-changes-toggle { display:inline-flex; align-items:center; gap:6px; margin-left:10px; color:var(--mut); font-size:12px; cursor:pointer; user-select:none }
.only-changes-toggle:hover { color:var(--acc) }
.only-changes-toggle input { width:15px; height:15px; margin:0; accent-color:var(--acc) }
.hidden-unchanged { display:none }
/* 노션 다단 컬럼. 좁은 폭에서는 세로로 떨어뜨려 좌우 패널 안에서도 읽히게 한다. */
.ncols { display:flex; flex-wrap:wrap; gap:14px; margin:10px 0 }
.ncol { flex:1; min-width:min(240px,100%) }
.co { display:flex; gap:10px; border-radius:8px; padding:10px 14px; margin:10px 0 }
.co-gray_bg { background:var(--gray) } .co-blue_bg { background:var(--blue) } .co-red_bg { background:var(--red) }
.co .ic { flex:none } .co ul { margin:2px 0 }
.bm { font-size:12.5px; background:var(--code); border:1px solid var(--line); border-radius:6px; padding:4px 10px; margin:5px 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
.bm a { color:var(--acc); text-decoration:none }
.doc .mk.del { background:rgba(225,60,60,.15); border-radius:3px }
.doc .mk.ins { background:rgba(60,175,90,.16); border-radius:3px }
.doc li.del { background:rgba(225,60,60,.15); border-radius:3px }
.doc li.ins { background:rgba(60,175,90,.16); border-radius:3px }
.doc td.del, .doc th.del { background:rgba(225,60,60,.2) }
.doc td.ins, .doc th.ins { background:rgba(60,175,90,.2) }
.review-change { position:relative }
.inline-revert-control { float:right; display:inline-flex; align-items:center; gap:4px; min-height:26px; margin:1px 1px 4px 8px; padding:2px 7px; border:1px solid var(--line); border-radius:999px; background:var(--surface); color:var(--mut); box-shadow:var(--shadow); font:11px/1.2 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif; cursor:pointer; user-select:none }
.inline-revert-control:hover { color:var(--acc); border-color:var(--acc) }
.inline-revert-control input { width:15px; height:15px; margin:0; accent-color:var(--acc) }
.inline-revert-control:has(input:focus-visible) { outline:2px solid var(--acc); outline-offset:2px }
.review-change.revert-selected { outline:2px solid var(--acc); outline-offset:2px; box-shadow:0 0 0 4px color-mix(in srgb,var(--acc) 12%,transparent) }
.review-change.review-current { outline:2px solid var(--current); outline-offset:3px; box-shadow:0 0 0 5px color-mix(in srgb,var(--current) 14%,transparent) }
.review-change.revert-selected.review-current { box-shadow:0 0 0 4px color-mix(in srgb,var(--acc) 16%,transparent),0 0 0 7px color-mix(in srgb,var(--current) 18%,transparent) }
.structural-review { margin:0 0 10px; padding:8px 10px; border:1px dashed var(--line); border-radius:9px; background:var(--pane); color:var(--mut); font-size:12px }
.revert-actions { position:fixed; left:50%; bottom:20px; z-index:20; display:none; align-items:center; gap:8px; transform:translateX(-50%); padding:9px 10px 9px 14px; border:1px solid var(--line); border-radius:14px; background:var(--surface); box-shadow:0 8px 30px rgba(0,0,0,.22) }
.revert-actions.show { display:flex }
.revert-count { min-width:72px; font-size:13px; font-weight:700 }
.revert-actions button { min-height:34px; padding:5px 11px; border:1px solid var(--line); border-radius:8px; background:var(--pane); color:var(--fg); cursor:pointer }
.revert-actions button.primary { border-color:var(--acc); background:var(--acc); color:#fff; font-weight:700 }
.revert-actions button:focus-visible { outline:2px solid var(--acc); outline-offset:2px }
@media (max-width:700px) { .inline-revert-control span { display:none } .revert-actions { right:10px; bottom:10px; left:10px; flex-wrap:wrap; transform:none } .revert-count { flex:1 } }
"""


def main():
    ap = argparse.ArgumentParser(
        description="노션계 마크다운 before/after를 공용 스크롤 렌더링 diff + 소스 diff 탭이 있는 단일 HTML로 만든다.",
        epilog="예: ntn-diff-viewer.py baseline/ drafts/ --exclude '*.changes.md' -o /tmp/review.html && open /tmp/review.html",
    )
    ap.add_argument(
        "old",
        type=pathlib.Path,
        help="현행본(.md 파일 또는 디렉토리, 예: ntn pages get 덤프)",
    )
    ap.add_argument("new", type=pathlib.Path, help="개선본(.md 파일 또는 디렉토리)")
    ap.add_argument(
        "-o",
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("/tmp/ntn-diff.html"),
        help="출력 HTML 경로 (기본 /tmp/ntn-diff.html)",
    )
    ap.add_argument("--title", default="Notion Markdown Diff", help="페이지 제목")
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="디렉토리 비교 시 제외할 상대 경로 패턴(반복 가능, 예: '*.changes.md')",
    )
    args = ap.parse_args()
    for p, name in ((args.old, "OLD"), (args.new, "NEW")):
        if not p.exists():
            sys.exit(f"오류: {name} 경로 없음: {p}")

    nav, sections, all_changes = [], [], []
    bundle_hash, unrendered_total, unsupported = hashlib.sha256(), 0, set()
    for key, op, np in collect_pairs(args.old, args.new, args.exclude):
        bt = op.read_text() if op else ""
        dt = np.read_text() if np else ""
        db, dd = chars(bt), chars(dt)
        ratio = round(100 * dd / db) if db else (100 if dd else 0)
        sid = re.sub(r"[^\w-]+", "-", key)
        dhtml, adds, dels, del_map, ins_map, changes = diff_data(bt, dt, sid)
        bundle_hash.update(f"{key}\0{bt}\0{dt}\0".encode())
        for change in changes:
            change.update(
                {
                    "clip": re.sub(r"^\d+-", "", sid),
                    "section_id": sid,
                    "order": len(all_changes),
                }
            )
            all_changes.append(change)
        old_seen, new_seen = set(), set()
        old_html = render(
            bt, op.parent if op else None, del_map, "del", old_seen, unsupported
        )
        new_html = render(
            dt, np.parent if np else None, ins_map, "ins", new_seen, unsupported
        )
        missing = [
            change["change_id"]
            for change in changes
            if change["change_id"] not in old_seen | new_seen
        ]
        unrendered_total += len(missing)
        fallback = ""
        if missing:
            controls = "".join(
                f'<label class="inline-revert-control"><input class="inline-revert-check" type="checkbox" '
                f'data-change-id="{html.escape(change_id, quote=True)}"><span>구조 변경 되돌림</span></label>'
                for change_id in missing
            )
            fallback = f'<div class="structural-review">렌더링 밖 구조 변경 {len(missing)}개 {controls}</div>'
        note = (
            ""
            if (op and np)
            else (" - NEW에만 존재" if np else " - OLD에만 존재(삭제됨)")
        )
        nav.append(
            f'<a href="#{sid}" data-section-id="{sid}">{html.escape(key)} '
            f'<span class="r">{ratio}%</span><span class="selection-badge" hidden>선택 0</span></a>'
        )
        sections.append(f'''
<section id="{sid}"><h2>{html.escape(key)} <small>본문 {db:,}자에서 {dd:,}자로 ({ratio}%){note}</small></h2>
<div class="tabs"><button type="button" onclick="tab(this,'v-prev')" class="on" aria-pressed="true">렌더링 diff</button><button type="button" onclick="tab(this,'v-diff')" aria-pressed="false">소스 diff <span class="st">+{adds}/-{dels}</span></button></div>
<label class="only-changes-toggle"><input type="checkbox" class="only-changes-check"><span>변경만 보기</span></label>
{fallback}
<div class="view v-prev"><div class="cols">
<div class="pane"><h3>현행본 <small>삭제·변경</small></h3><div class="doc">{old_html}</div></div>
<div class="pane"><h3>개선본 <small>추가·변경</small></h3><div class="doc">{new_html}</div></div>
</div></div>
<div class="view v-diff dwrap" hidden>{dhtml}</div></section>''')

    request_data = json.dumps(
        {
            "source": {"title": args.title, "diff_id": bundle_hash.hexdigest()},
            "changes": all_changes,
        },
        ensure_ascii=False,
    ).replace("<", "\\u003c")
    actions = """<div id="revert-actions" class="revert-actions" role="status" aria-live="polite">
<span id="revert-count" class="revert-count">선택 0개</span><button id="revert-clear" type="button">초기화</button>
<button id="revert-copy" type="button">선택 내용 복사</button><button id="revert-download" class="primary" type="button">요청 파일 만들기</button></div>"""
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(args.title)}</title>
<style>{CSS}</style></head><body>
<header><div class="header-row"><h1>{html.escape(args.title)}</h1>
<div class="change-nav" role="group" aria-label="변경 탐색">
<button id="change-prev" type="button" aria-label="이전 변경" aria-keyshortcuts="p shift+n">← 이전 <kbd>P</kbd><kbd>⇧N</kbd></button>
<span id="change-position" class="change-position" aria-live="polite">변경 준비 중</span>
<button id="change-next" type="button" aria-label="다음 변경" aria-keyshortcuts="n"><kbd>N</kbd> 다음 →</button></div></div>
<nav aria-label="클립 바로가기">{"".join(nav)}</nav></header>
<main>{"".join(sections)}</main>{actions}<script id="revert-request-data" type="application/json">{request_data}</script><script>{JS}</script></body></html>"""
    args.out.write_text(page)
    print(
        f"{args.out} ({args.out.stat().st_size // 1024}KB, {len(sections)}개 섹션, "
        f"변경 {len(all_changes)}개, 구조 fallback {unrendered_total}개) - open {args.out}"
    )
    if unsupported:
        # 핸들러 없는 태그는 화면에 raw로 남아 변경을 가린다. 조용히 넘기지 않고
        # 이름을 알려 render()에 핸들러를 더할지 판단하게 한다.
        print(
            f"경고: 렌더링 못 한 태그가 문단으로 노출됨 - {', '.join(sorted(unsupported))}. "
            f"이 태그가 화면에 그대로 보이면 render()에 핸들러를 추가한다."
        )


if __name__ == "__main__":
    main()
