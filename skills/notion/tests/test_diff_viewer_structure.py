#!/usr/bin/env python3
"""Structural regression test for the inline Notion diff review HTML.

Renders a tiny before/after pair through scripts/ntn-diff-viewer.py and asserts the
review contract the apply step depends on: every change carries a checkbox, change
ids are unique, and navigation plus the JSON export hook are present.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ntn-diff-viewer.py"

OLD = """# 제목
<callout icon="💡" color="gray_bg">
	**바뀌지 않는 콜아웃**
</callout>
- 첫 항목
- 둘째 항목
"""

NEW = """# 제목
<callout icon="💡" color="gray_bg">
	**바뀌지 않는 콜아웃**
</callout>
- 첫 항목 수정
- 둘째 항목
- 새로 추가된 항목
"""


STRUCT_OLD = """---
title: 페이지
---
<columns>
	<column ratio="50">
		- 이름 A
	</column>
	<column ratio="50">
		- 설명
	</column>
</columns>
<unknown url="https://example.com/x" alt="external_object_instance"/>
"""

STRUCT_NEW = STRUCT_OLD.replace("이름 A", "이름 B")


INLINE_OLD = """<table header-row="true">
<tr><td>**\\[10:00\\] \\~ \\[10:50\\]**</td><td>실습</td></tr>
</table>
<callout icon="💡" color="gray_bg">
	**오늘의 산출물<br>**스펙 -\\> 테스트 -\\> 구현
</callout>
<page url="https://example.com/child">하위 페이지</page>
"""

INLINE_NEW = INLINE_OLD.replace("<td>실습</td>", "<td>실습 2</td>")


def render(tmp_path, old_text=OLD, new_text=NEW):
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    out = tmp_path / "review.html"
    old.write_text(old_text, encoding="utf-8")
    new.write_text(new_text, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(old), str(new), "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"viewer failed: {proc.stderr}"
    return out.read_text(encoding="utf-8")


def test_every_change_has_a_checkbox(tmp_path):
    body = render(tmp_path)
    match = re.search(
        r'<script id="revert-request-data" type="application/json">(.*?)</script>',
        body,
        re.S,
    )
    assert match, "missing revert-request-data"
    change_ids = [
        change["change_id"] for change in json.loads(match.group(1))["changes"]
    ]
    assert change_ids, "no changes detected in a pair that differs"
    assert len(change_ids) == len(set(change_ids)), "duplicate change ids"
    control_ids = set(re.findall(r'data-change-id="([^"]+)"', body))
    assert set(change_ids) <= control_ids, "change without checkbox"


def test_navigation_and_export_present(tmp_path):
    body = render(tmp_path)
    for marker in (
        'id="change-prev"',
        'id="change-next"',
        "notion-revert-request/v1",
        "addEventListener('keydown'",
        # N은 다음, Shift+N은 이전. 손을 옮기지 않고 앞뒤로 오갈 수 있어야 한다.
        "event.shiftKey ? -1 : 1",
        'aria-keyshortcuts="p shift+n"',
    ):
        assert marker in body, f"missing {marker}"


def test_notion_structure_tags_render_instead_of_leaking(tmp_path):
    """구조 태그가 문단으로 새면 화면에서 변경보다 눈에 띄어 리뷰를 방해한다.

    소스 diff 탭은 원문 줄을 그대로 보여주는 게 맞으므로 렌더링 패널(.doc)만 본다."""
    body = render(tmp_path, STRUCT_OLD, STRUCT_NEW)
    panels = re.findall(r'<div class="doc">(.*?)</div></div>', body, re.S)
    assert panels, "no rendered panel found"
    for panel in panels:
        for leaked in ("&lt;column", "&lt;unknown", "<p>title:"):
            assert leaked not in panel, f"raw tag leaked into the panel: {leaked}"
    for rendered in ('class="ncols"', 'class="ncol"', 'class="fm"', 'class="bm"'):
        assert rendered in body, f"missing rendered structure: {rendered}"


def test_notion_escapes_resolve_in_rendered_panels(tmp_path):
    """ntn 덤프는 [ ] ~ > 를 백슬래시로 이스케이프하고 줄바꿈을 <br>로 남긴다.

    그대로 두면 표와 콜아웃이 `\\[10:00\\]`, `<br>`로 덮여 정작 볼 변경이 묻힌다."""
    body = render(tmp_path, INLINE_OLD, INLINE_NEW)
    panels = re.findall(r'<div class="doc">(.*?)</div></div>', body, re.S)
    assert panels, "no rendered panel found"
    for panel in panels:
        for leaked in ("\\[", "\\~", "-\\&gt;", "&lt;br&gt;", "&lt;page"):
            assert leaked not in panel, f"raw escape leaked into the panel: {leaked}"
    assert "[10:00] ~ [10:50]" in body, "escaped brackets were not restored"
    assert "하위 페이지" in body, "child page title was not rendered"
