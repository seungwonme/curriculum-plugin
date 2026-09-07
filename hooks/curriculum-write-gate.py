#!/usr/bin/env python3
"""PreToolUse 게이트: curriculum 노션 쓰기(notion_reflect.py) 직전에 충실도 린트를 강제한다.

왜: AI가 강의 본문을 '창작'(소스에 없는 섹션/표/산문 발명)해서 노션에 박는 사고가 반복됨.
    스킬 문서/지침은 무시되니, 쓰기 도구 자체를 훅으로 막는다.
동작: Bash 명령에 notion_reflect.py가 있으면
    1) 본문 .md를 찾고
    2) 소스 선언 사이드카 <본문>.fidelity.json 을 요구(없으면 차단)
    3) canonical curriculum fidelity_lint.py로 net-new 발명 검사(실패면 차단)
    통과(또는 비curriculum 명령)면 exit 0으로 그냥 흘려보낸다.
차단은 exit 2 + stderr 사유(Claude에게 피드백되어 쓰기가 막힌다).

사이드카 형식: {"sources": ["기존자료1.md", "기존자료2.md"]}
  sources 경로는 사이드카 파일 기준 상대경로. 임계값 재정의는 허용하지 않는다.
  {"native": true} 면 충실도 강제 없이 통과(빌드 소스가 없는 네이티브/골드 클립용).

ceiling(spartan): notion_reflect.py만 가로챈다. `ntn pages update` 직접 호출 우회는 v1 미커버
  (그 경로는 이미지/북마크를 잃어 실제 이식엔 안 쓰임). 필요해지면 matcher에 추가.
"""

import json
import os
import re
import subprocess
import sys

# 플러그인 내장 스크립트 우선, 없으면 로컬 shared 정본으로 fallback.
_here = os.path.dirname(os.path.abspath(__file__))
_candidates = [
    os.path.normpath(
        os.path.join(_here, "..", "skills", "using-curriculum", "scripts", "fidelity_lint.py")
    ),
    os.path.expanduser("~/.agents/skills/shared/using-curriculum/scripts/fidelity_lint.py"),
]
LINT = next((p for p in _candidates if os.path.exists(p)), _candidates[0])


def block(msg):
    sys.stderr.write("[curriculum 충실도 게이트] 쓰기 차단\n" + msg + "\n")
    sys.exit(2)


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        sys.exit(0)  # 입력 파싱 실패는 fail-open (훅 버그로 전체 쓰기를 막지 않음)

    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command", "")
    if "notion_reflect.py" not in cmd:
        sys.exit(0)  # 비curriculum 쓰기는 관여 안 함

    # notion_reflect.py가 '실행'되는 세그먼트만 게이트한다. grep/echo 등에서 파일명을
    # 언급만 한 복합 명령(cd X && grep ...)은 명령 위치 매칭에 걸리지 않아 통과한다.
    # 실행 형태: [ENV=v ...] [python*|uv run|env|time|nohup [-opt ...]]* <경로/>notion_reflect.py <인자...>
    # 정본 호출은 여러 줄이라 백슬래시 줄연결을 먼저 접고 개행도 명령 구분자로 본다.
    cmd_flat = re.sub(r"\\\n\s*", " ", cmd)
    exec_m = re.search(
        r"(?:^\s*|[;&|(\n]\s*)"
        r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
        r"(?:(?:\S*python[\d.]*|uv\s+run|\S*env|time|nohup)\s+(?:-\S+\s+)*)*"
        r"\S*notion_reflect\.py\b([^;&|)\n]*)",
        cmd_flat,
    )
    if not exec_m:
        sys.exit(0)  # 언급뿐, 실행 아님 (bash -c/xargs 래핑, heredoc 안 실행은 v1 미커버 ceiling)
    seg = exec_m.group(1)

    cwd = data.get("cwd") or os.getcwd()

    # 실행 세그먼트의 인자에서만 .md 토큰 추출 (--report 값은 검수 리포트라 본문에서 제외)
    md_tokens = [t.strip("'\"") for t in re.findall(r"[^\s'\"]+\.md", seg)]
    report = re.search(r"--report[=\s]+['\"]?([^\s'\"]+\.md)", seg)
    report_md = report.group(1) if report else None
    bodies = [m for m in md_tokens if m != report_md]
    if not bodies:
        # reflect 실행은 항상 본문 .md 인자를 받는다. .md가 없으면 실행이 아니라
        # 단순 언급(grep/find/sed 등)이므로 통과(과탐지 방지, fail-open).
        sys.exit(0)

    target = bodies[-1]  # canonical CLI의 마지막 .md positional이 LOCAL_MD
    target_abs = target if os.path.isabs(target) else os.path.join(cwd, target)
    if not os.path.exists(target_abs):
        block(f"본문 경로를 찾지 못했습니다: {target_abs}")

    sidecar = target_abs + ".fidelity.json"
    if not os.path.exists(sidecar):
        block(
            f"소스 미선언. 이 클립이 어떤 기존 검증 자료를 이식한 건지 선언해야 씁니다.\n"
            f"  {os.path.basename(sidecar)} 를 만들고 sources에 기존 자료 .md 경로를 넣으세요:\n"
            f'  {{"sources": ["기존_1일1바_원본.md"]}}\n'
            f"  네이티브/골드(기존 1일1바에 대응 빌드 소스가 없거나 강사가 직접 다듬은 클립)면 "
            f'{{"native": true}} 로 선언하면 충실도 강제 없이 통과합니다(옛 소스로 골드를 덮지 마세요).'
        )

    try:
        spec = json.load(open(sidecar, encoding="utf-8"))
    except Exception as e:
        block(f"{os.path.basename(sidecar)} 파싱 실패: {e}")

    # 네이티브/골드 클립({"native": true})은 충실도 강제 대상이 아니다.
    # 기존 1일1바에 대응 빌드 소스가 없거나, 강사가 직접 다듬은 골드는 옛 소스 충실도가
    # 오히려 해롭다(골드 덮어쓰기/과탐지 사고 방지). 명시 선언만 통과시킨다.
    if not isinstance(spec, dict):
        block(f"{os.path.basename(sidecar)} 는 JSON 객체여야 합니다.")
    if "cov" in spec or "ratio" in spec:
        block(
            f"{os.path.basename(sidecar)} 에서 cov/ratio 임계값을 재정의할 수 없습니다."
        )
    if spec.get("native") is True:
        if spec.get("sources"):
            block("native=true와 sources를 함께 선언할 수 없습니다.")
        sys.exit(0)

    sources = spec.get("sources") or []
    if (
        not isinstance(sources, list)
        or not sources
        or not all(isinstance(s, str) and s for s in sources)
    ):
        block(
            f"{os.path.basename(sidecar)} 의 sources가 비었습니다. 이식 원본 .md를 선언하세요."
        )

    sc_dir = os.path.dirname(sidecar)
    src_args = []
    for s in sources:
        sp = s if os.path.isabs(s) else os.path.join(sc_dir, s)
        if not os.path.exists(sp):
            block(f"선언한 소스가 없습니다: {s} (해석: {sp})")
        src_args += ["--source", sp]

    argv = [sys.executable, LINT, "--target", target_abs] + src_args
    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        block(
            "기존 자료에 없는 net-new 블록(발명)이 한도를 넘었습니다. 소스 흐름/구조 그대로 이식하세요:\n"
            + r.stdout
            + ("\n" + r.stderr if r.stderr.strip() else "")
        )
    sys.exit(0)  # 통과


if __name__ == "__main__":
    main()
