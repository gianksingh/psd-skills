#!/usr/bin/env python3
"""Build the clean PSD template deck: every layout once, numbers masked, text slots labeled."""
import json, re, sys, copy
src = json.load(open(sys.argv[1]))
t = copy.deepcopy(src)
WEEK = "M/D–M/D/YY"
NUMERIC_KEYS = {"value", "cmp", "w", "dir", "share", "clicks", "card_rows"}
def mask(v, k=None):
    if isinstance(v, str):
        if k == "img": return None
        if k in ("num", "sec", "kicker"): return v.replace(src["meta"]["week"], WEEK)
        v = v.replace(src["meta"]["week"], WEEK)
        v = re.sub(r"\b\d{1,2}/\d{1,2}(/\d{2})?\b", "M/D", v)
        return re.sub(r"(?<![A-Za-z_/])\d[\d,\.]*", "#", v)
    if isinstance(v, list): return [mask(x) for x in v]
    if isinstance(v, dict): return {kk: (x if kk in NUMERIC_KEYS and not isinstance(x, str) else mask(x, kk)) for kk, x in v.items()}
    return v
t["meta"]["week"] = WEEK
skip = {"appx_log_2", "appx_log_3", "appx_log_4", "appx_log_5", "appx_bible_2"}
out = []
for s in t["slides"]:
    if s["id"] in skip: continue
    s = mask(s)
    if s["type"] in ("finding", "summary", "cover"):
        s["headline"] = "[Headline: the one takeaway, with its number]"
    if s["type"] == "finding":
        s.pop("_obs", None)
    if s["type"] == "cover":
        s["headline"] = "[Optional: one line on the week]"
    out.append(s)
# The new-drop slide only runs when a drop launched in the last 14 days, so the template carries a stub of it.
if not any(x["id"] == "drop" for x in out):
    ref = next(x for x in out if x["id"] == "products")
    stub = {"id": "drop", "type": "finding", "kicker": "New drop · [Drop name]", "sec": "02", "pill": "LAUNCHED M/D",
        "headline": "[Headline: the one takeaway, with its number]",
        "body": {"layout": "two_cards", "split": 0.58,
                 "left": {"kind": "table", "title": "LAUNCH TO DATE VS PAST DROPS AT THE SAME DAY COUNT (# DAYS)",
                          "columns": [{"h": h, "w": w, **({"a": "r"} if i > 1 else {})} for i, (h, w) in enumerate([("Drop", 1.9), ("Launched", 0.9), ("Days", 0.6), ("Units", 0.8), ("Net sales", 0.95), ("Sessions", 0.95), ("ATC rate", 0.85), ("CVR", 0.75)])],
                          "rows": [[{"t": n, "b": True}, "M/D", "#", "#", "$#K", "#", "#%", "#%"] for n in ("[This drop]", "[Past drop 1]", "[Past drop 2]")]},
                 "right": {"kind": "table", "title": "TOP PRODUCTS IN THE DROP BY UNITS",
                           "columns": [{"h": "Product", "w": 2.2}, {"h": "Style", "w": 1.6}, {"h": "Units", "w": 0.7, "a": "r"}, {"h": "CVR", "w": 0.7, "a": "r"}],
                           "rows": [[{"t": "[Product]", "b": True}, "[Style]", "#", "#%"] for _ in range(5)]}},
        "jamie": True,
        "footer": ref["footer"].split(" · Week")[0].replace("Online Store", "drop collection") + " · Week M/D–M/D/YY"}
    i = next(k for k, x in enumerate(out) if x["id"] == "lp_modules") + 1
    out.insert(i, stub)
t["slides"] = out
json.dump(t, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
print("template spec:", len(out), "slides")
