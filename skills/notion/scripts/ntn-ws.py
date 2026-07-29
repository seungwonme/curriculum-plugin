#!/usr/bin/env python3
"""Resolve a Notion workspace by name/alias and run ntn with NOTION_WORKSPACE_ID set.

Values live in ntn's own config (~/.config/notion/workspaces.json) plus an optional
user-managed alias file (~/.config/notion/aliases.json), so raw UUIDs stay out of
skill docs and command lines (= conversation logs).

Usage:
  ntn-ws.py --list                        registered workspaces (+ aliases)
  ntn-ws.py --alias <alias> <target>      save alias (target = name fragment or full UUID)
  ntn-ws.py <name-or-alias> <ntn args...> run ntn scoped to that workspace
  ntn-ws.py jax pages get <page-id>

Run it; do not read the source.
"""
import json
import os
import sys
from pathlib import Path

CONFIG = Path.home() / ".config/notion/workspaces.json"
ALIASES = Path.home() / ".config/notion/aliases.json"


def die(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(2)


def workspaces() -> dict:
    """{uuid: name} from ntn's own registration file."""
    if not CONFIG.exists():
        die(f"ntn 설정이 없습니다: {CONFIG}\n"
            "ntn 대화형 로그인(사람 몫)이 이 파일을 만듭니다 - 로그인 후 다시 실행하세요.")
    envs = json.loads(CONFIG.read_text()).get("environments", {})
    out = {}
    for env in envs.values():
        for uuid, meta in env.items():
            out[uuid] = (meta or {}).get("name", uuid)
    if not out:
        die(f"{CONFIG}에 등록된 워크스페이스가 없습니다 - ntn 로그인으로 등록하세요.")
    return out


def aliases() -> dict:
    if not ALIASES.exists():
        return {}
    try:
        data = json.loads(ALIASES.read_text())
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
        return data
    except Exception as e:
        die(f'{ALIASES} 파싱 실패({e}) - {{"별칭": "이름조각 또는 UUID"}} 형식이어야 합니다.')


def resolve(query: str, ws: dict, al: dict) -> str:
    al_l = {k.lower(): v for k, v in al.items()}
    if query.lower() in al_l:
        query = al_l[query.lower()]
    if query in ws:
        return query
    hits = [u for u, name in ws.items() if query.lower() in name.lower()]
    if len(hits) == 1:
        return hits[0]
    names = ", ".join(sorted(ws.values()))
    if not hits:
        die(f"'{query}'와 일치하는 워크스페이스가 없습니다. 등록된 이름: {names}\n"
            "별칭 추가: ntn-ws.py --alias <별칭> <이름조각>")
    die(f"'{query}'가 여러 워크스페이스와 일치합니다: "
        f"{', '.join(ws[h] for h in hits)} - 더 구체적인 이름이나 별칭을 쓰세요.")


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    ws = workspaces()
    al = aliases()

    if args[0] == "--list":
        for uuid, name in ws.items():
            tags = sorted(a for a, t in al.items()
                          if t == uuid or t.lower() in name.lower())
            print(name + (f"  (alias: {', '.join(tags)})" if tags else ""))
        return 0

    if args[0] == "--alias":
        if len(args) != 3:
            die("사용법: ntn-ws.py --alias <별칭> <이름조각 또는 UUID>")
        _, alias, target = args
        resolve(target, ws, {})  # target이 실제 워크스페이스로 풀리는지 선검증
        data = aliases()
        data[alias] = target
        ALIASES.parent.mkdir(parents=True, exist_ok=True)
        ALIASES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"alias 저장: {alias} -> {target} ({ALIASES})")
        return 0

    query, rest = args[0], args[1:]
    if rest and rest[0] == "--":
        rest = rest[1:]
    if not rest:
        die("실행할 ntn 인자가 없습니다. 예: ntn-ws.py jax pages get <page-id>")
    uuid = resolve(query, ws, al)
    env = dict(os.environ, NOTION_WORKSPACE_ID=uuid)
    os.execvpe("ntn", ["ntn", *rest], env)


if __name__ == "__main__":
    sys.exit(main())
