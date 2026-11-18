#!/usr/bin/env python3
"""mix-match-report · HTML builder. Injects data.json into assets/template.html.
Never edit the template during a run. usage: build_html.py data.json out.html"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "assets", "template.html")
REQ = ["meta", "kits", "summary", "division", "order_mix", "kit_division", "daily", "traffic", "top_picks"]


def die(m):
    print(f"build_html.py: STOP · {m}", file=sys.stderr); sys.exit(1)


if len(sys.argv) != 3:
    die("usage: build_html.py data.json out.html")
d = json.load(open(sys.argv[1]))
miss = [k for k in REQ if k not in d]
if miss:
    die(f"data.json is missing {miss}; run compute.py first")
for k in ("period", "compare"):
    if not d["meta"].get(k, {}).get("label"):
        die(f"meta.{k}.label missing")
t = open(TPL).read()
if t.count("/*DATA*/null") != 1:
    die("template placeholder /*DATA*/null not found exactly once; the template was edited")
d = {k: v for k, v in d.items() if k != "issues"}  # issues go to chat, never into the report
out = t.replace("/*DATA*/null", json.dumps(d, separators=(",", ":")))
open(sys.argv[2], "w").write(out)
print(f"build_html.py: OK → {sys.argv[2]}" + (" (FILLER)" if d["meta"].get("filler") else ""))
