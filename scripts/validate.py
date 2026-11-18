#!/usr/bin/env python3
"""Validate every plugin: plugin.json JSON + kebab name, Cowork description limits,
each SKILL.md frontmatter, and no duplicate slash commands across the marketplace."""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_DESC_MAX = 500
SKILL_DESC_MAX = 1024
ok, cmds = True, {}
mk = ROOT / ".claude-plugin/marketplace.json"


def skill_description(text):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 2:
        return None
    fm = parts[1]
    if re.search(r"^description:\s*>", fm, re.M):
        lines = []
        in_desc = False
        for line in fm.splitlines():
            if re.match(r"^description:\s*>", line):
                in_desc = True
                continue
            if in_desc:
                if line.startswith(" ") or line.startswith("\t"):
                    lines.append(line.strip())
                else:
                    break
        return " ".join(lines) if lines else ""
    m = re.search(r"^description:\s*(.+)$", fm, re.M)
    return m.group(1).strip() if m else None


try:
    json.loads(mk.read_text())
    print("[ok] marketplace.json valid")
except Exception as e:
    print(f"[FAIL] marketplace.json: {e}")
    ok = False

for pj in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
    plug = pj.parent.parent.name
    try:
        d = json.loads(pj.read_text())
        name = d.get("name", "")
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name), f"name not kebab: {name!r}"
        desc = d.get("description", "")
        if len(desc) > PLUGIN_DESC_MAX:
            raise AssertionError(
                f"description {len(desc)} chars > {PLUGIN_DESC_MAX} (Cowork limit)"
            )
        print(f"[ok] {plug}: plugin.json valid (v{d.get('version')})")
    except Exception as e:
        print(f"[FAIL] {plug}: {e}")
        ok = False
    for sk in sorted((pj.parent.parent / "skills").glob("*/SKILL.md")):
        t = sk.read_text()
        m = re.search(r"(?m)^name:\s*(\S+)\s*$", t)
        if not (t.startswith("---") and m):
            print(f"[FAIL] {plug}/{sk.parent.name}: missing frontmatter/name")
            ok = False
            continue
        c = m.group(1)
        cmds.setdefault(c, []).append(f"{plug}/{sk.parent.name}")
        desc = skill_description(t)
        if desc is not None and len(desc) > SKILL_DESC_MAX:
            print(
                f"[FAIL] {plug}/{sk.parent.name}: description {len(desc)} chars "
                f"> {SKILL_DESC_MAX} (Cowork limit)"
            )
            ok = False

for c, where in sorted(cmds.items()):
    if len(where) > 1:
        print(f"[FAIL] duplicate command /{c}: {where}")
        ok = False
print(f"\nCommands: {', '.join('/' + c for c in sorted(cmds))}")
print("VALIDATION:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)