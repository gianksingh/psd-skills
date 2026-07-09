#!/usr/bin/env python3
"""Validate every plugin: plugin.json JSON + kebab name, each SKILL.md frontmatter,
and no duplicate slash commands across the whole marketplace."""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
ok, cmds = True, {}
mk = ROOT/".claude-plugin/marketplace.json"
try:
    json.loads(mk.read_text()); print(f"[ok] marketplace.json valid")
except Exception as e:
    print(f"[FAIL] marketplace.json: {e}"); ok=False
for pj in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
    plug = pj.parent.parent.name
    try:
        d = json.loads(pj.read_text()); name=d.get("name","")
        assert re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name), f"name not kebab: {name!r}"
        print(f"[ok] {plug}: plugin.json valid (v{d.get('version')})")
    except Exception as e:
        print(f"[FAIL] {plug}: {e}"); ok=False
    for sk in sorted((pj.parent.parent/"skills").glob("*/SKILL.md")):
        t = sk.read_text()
        m = re.search(r'(?m)^name:\s*(\S+)\s*$', t)
        if not (t.startswith("---") and m):
            print(f"[FAIL] {plug}/{sk.parent.name}: missing frontmatter/name"); ok=False; continue
        c = m.group(1)
        cmds.setdefault(c, []).append(f"{plug}/{sk.parent.name}")
for c, where in sorted(cmds.items()):
    if len(where) > 1:
        print(f"[FAIL] duplicate command /{c}: {where}"); ok=False
print(f"\nCommands: {', '.join('/'+c for c in sorted(cmds))}")
print("VALIDATION:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
