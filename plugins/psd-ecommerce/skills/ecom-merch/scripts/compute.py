#!/usr/bin/env python3
"""Ecom Merch Weekly: compute layer (v2).

data/raw_<week>.json + data/observations_<week>.json  ->  data/deck_<week>.json

Every number in the deck is formatted here, with one rule set. Fail-closed: a missing key raises.
"""
import csv, json, sys, datetime as dt
from pathlib import Path

import os
ROOT = Path(__file__).resolve().parent  # skill scripts dir: config.json lives here
WORK = Path(os.environ.get("MERCH_WORK") or os.getcwd())  # run folder: data/, inputs/, assets/products/
cfg = json.loads((ROOT / "config.json").read_text())

# --------------------------------------------------------------- format rules (bible §0)
def rate(n, d):
    return None if not d else n / d

def f_int(x):
    return "—" if x is None else f"{x:,.0f}"

def f_k(x):
    return "—" if x is None else (f"{x/1000:,.1f}K" if abs(x) >= 10000 else f"{x:,.0f}")

def f_money(x, k=False):
    if x is None:
        return "—"
    if k and abs(x) >= 1000:
        return f"${x/1000:,.1f}K"
    return f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"

def f_rate(r, dp=1):
    return "—" if r is None else f"{r*100:.{dp}f}%"

def d_pct(cur, prev):
    if prev in (None, 0) or cur is None:
        return {"t": "n/a", "dir": 0}
    v = (cur - prev) / prev
    t = f"{v*100:+.1f}%"
    return {"t": "0.0%", "dir": 0} if t in ("+0.0%", "-0.0%") else {"t": t, "dir": (v > 0) - (v < 0)}

def d_pts(cur, prev, dp=1):
    if cur is None or prev is None:
        return {"t": "n/a", "dir": 0}
    v = (cur - prev) * 100
    t = f"{v:+.{dp}f} pts"
    return {"t": f"{0:.{dp}f} pts", "dir": 0} if float(t.split()[0]) == 0 else {"t": t, "dir": (v > 0) - (v < 0)}

def low(den, num=None):
    return (den is not None and den < 100) or (num is not None and num < 30)

def flag(text, is_low):
    return text + " †" if is_low else text

def sd(s):
    d = dt.date.fromisoformat(s); return f"{d.month}/{d.day}"

def dow(s):
    return dt.date.fromisoformat(s).strftime("%a")

TITLES = {}

def page_name(path):
    """Site title when known (Shopify), else a readable version of the handle."""
    if path in TITLES:
        return TITLES[path]
    if path == "/":
        return "Homepage"
    h = path.replace("/collections/", "").replace("/pages/", "")
    return " · ".join(seg.replace("-", " ").title().replace("Mens", "Men's").replace("Womens", "Women's") for seg in h.split("/"))

def parse_clarity(path, labels):
    rows = list(csv.reader(open(WORK / path, encoding="utf-8-sig")))
    meta, clicks, hdr = {}, [], False
    for r in rows:
        if not r:
            continue
        if r[0] in ("Date range", "Page views", "Visited URL matches regex", "Visited URL contains"):
            meta[r[0]] = r[1]
        if r[0] == "Area" and len(r) > 2:
            hdr = True; continue
        if hdr and len(r) >= 3:
            clicks.append(int(r[1]))
    if len(clicks) != len(labels):
        raise SystemExit(f"Clarity label count mismatch for {path}: {len(clicks)} areas vs {len(labels)} labels")
    tot = sum(clicks)
    return meta, tot, [{"label": l, "clicks": c, "share": c / tot} for l, c in zip(labels, clicks)]

def top_modules(items, n=8):
    srt = sorted(items, key=lambda i: -i["clicks"])
    top, rest = srt[:n], srt[n:]
    out = [{"label": i["label"], "value": i["share"], "display": f"{f_rate(i['share'])}  ·  {f_int(i['clicks'])}"} for i in top]
    if rest:
        rc = sum(i["clicks"] for i in rest); rs = sum(i["share"] for i in rest)
        out.append({"label": f"All other areas ({len(rest)})", "value": rs, "display": f"{f_rate(rs)}  ·  {f_int(rc)}", "muted": True})
    return out

# --------------------------------------------------------------- build
def camp_name_upper(inp):
    return inp["campaign"]["name"].upper()

def build(week):
    raw = json.loads((WORK / "data" / f"raw_{week}.json").read_text())
    op = WORK / "data" / f"observations_{week}.json"
    obs = json.loads(op.read_text()) if op.exists() else {}
    m, inp = raw["meta"], raw["inputs"]
    TITLES.update(raw.get("titles", {}))
    D = lambda s: dt.date.fromisoformat(s)
    WEEK = f"{D(m['week_start']).strftime('%-m/%-d')}–{D(m['week_end']).strftime('%-m/%-d/%y')}"
    WOW = f"vs {D(m['wow_start']).strftime('%-m/%-d')}–{D(m['wow_end']).strftime('%-m/%-d')}"
    YOY = f"YoY {D(m['yoy_start']).strftime('%-m/%-d')}–{D(m['yoy_end']).strftime('%-m/%-d/%y')}"
    runlog, slides = [], []

    def foot(src, extra=None):
        return " · ".join(x for x in [src, f"Week {WEEK}", extra] if x)

    import re as _re
    def _pd(t):
        return _re.sub(r"(\d{4})-(\d{2})-(\d{2})\.\.(\d{4})-(\d{2})-(\d{2})", lambda g: f"{int(g[2])}/{int(g[3])}–{int(g[5])}/{int(g[6])}/{g[4][2:]}", t)
    def log(sl, num, src, filt, dates=None):
        runlog.append([sl, num, src, filt, _pd(dates or f"{m['week_start']}..{m['week_end']} vs {m['wow_start']}..{m['wow_end']}")])

    def H(k, fb):
        return obs.get(k, {}).get("headline", fb)

    def OB(k):
        return obs.get(k, {}).get("observations", [])

    def stat(value, label, sub, d=None, dl=None, invert=False, accent=False):
        return {"value": value, "label": label, "sub": sub, "d": d, "dl": dl, "invert": invert, "accent": accent}

    # core numbers
    sw, sw0 = raw["pixel"]["sitewide"]["cy"], raw["pixel"]["sitewide"]["wow"]
    cvr, cvr0 = rate(sw["cc"], sw["sessions"]), rate(sw0["cc"], sw0["sessions"])
    atc, atc0 = rate(sw["atc"], sw["sessions"]), rate(sw0["atc"], sw0["sessions"])
    g, gl = raw["ga4"]["sitewide"]["cy"], raw["ga4"]["sitewide"]["ly"]
    gcvr, gcvr0 = rate(g["purchases"], g["sessions"]), rate(gl["purchases"], gl["sessions"])
    s, s0, sy = raw["sales"]["cy"], raw["sales"]["wow"], raw["sales"]["yoy"]
    for n in ("Sessions", "Conversion rate", "Add-to-cart rate"):
        log("Cover / summary / site", n, "Polar pixel", "PSD Web view; all sessions (bots included)")
    log("Cover / summary", "Net sales, orders, AOV", "Shopify via Polar (custom_60202 etc.)", "PSD Web view")
    log("Summary / site", "YoY sessions and CVR", "GA4 via Polar (ga_main)", "PSD Web view", f"{m['week_start']}..{m['week_end']} vs {m['yoy_start']}..{m['yoy_end']}")

    # missing inputs
    missing = [f"What's live: {x}" for x in inp.get("whats_live_missing", [])]
    if not inp["campaign"].get("launch_date"):
        missing.append("Campaign launch date and last year's equivalent (launch-to-date view)")
    missing += [f"AfterSell: {x}" for x in inp.get("aftersell_missing", [])]
    missing += [f"Looking ahead: {x}" for x in inp.get("ahead_missing", [])]
    missing += [f"Searchspring: {x}" for x in raw.get("search", {}).get("searchspring", {}).get("missing", [])]
    if inp.get("drop") and not raw.get("drop"):
        missing.append(f"New drop data for {inp['drop'].get('name', 'the drop')}")

    # ===================== COVER
    slides.append({"id": "cover", "type": "cover",
        "kicker": f"WEEK OF {WEEK} · MON–SUN", "pill": "PSD WEB", "title": "Ecom Merch Weekly",
        "headline": H("cover", ""),
        "stats": [stat(f_k(sw["sessions"]), "Sessions", f"{d_pct(sw['sessions'], sw0['sessions'])['t']} WoW", accent=True),
                  stat(f_rate(cvr, 2), "Conversion rate", f"{d_pts(cvr, cvr0, 2)['t']} WoW"),
                  stat(f_money(s["net"], k=True), "Net sales (context)", f"{d_pct(s['net'], s0['net'])['t']} WoW · {d_pct(s['net'], sy['net'])['t']} YoY")],
        "foot_left": "Prepared for the Monday merch meeting",
        "foot_right": f"{len(missing)} manual inputs missing · see run notes" if missing else "All manual inputs received",
    })

    # ===================== SUMMARY
    fu = inp.get("followups", [])
    ap = raw.get("app")
    if ap: log("Summary", "App orders, net sales, AOV", "Shopify via Polar", "PSD Web view; custom_5794 = Mobile App (Tapcart)")
    slides.append({"id": "summary", "type": "summary", "kicker": "The week at a glance", "pill": f"WEEK {WEEK}",
        "headline": H("summary", "Week at a glance"),
        "stats": [stat(f_int(sw["sessions"]), "Sessions", f"{d_pct(sw['sessions'], sw0['sessions'])['t']} WoW · {d_pct(g['sessions'], gl['sessions'])['t']} YoY (GA4)", accent=True),
                  stat(f_rate(cvr, 2), "Conversion rate", f"{d_pts(cvr, cvr0, 2)['t']} WoW · {d_pts(gcvr, gcvr0, 2)['t']} YoY (GA4)"),
                  stat(f_money(s["net"], k=True), "Net sales (context)", f"{d_pct(s['net'], s0['net'])['t']} WoW · {d_pct(s['net'], sy['net'])['t']} YoY · AOV {f_money(s['aov'])}")]
                 + ([stat(f"{f_int(ap['cy']['orders'])} orders", "App (Tapcart)", f"{f_rate(rate(ap['cy']['orders'], s['orders']))} of orders · {f_money(ap['cy']['net'], k=True)} ({d_pct(ap['cy']['net'], ap['wow']['net'])['t']}) · AOV {f_money(ap['cy']['aov'])} ({d_pct(ap['cy']['aov'], ap['wow']['aov'])['t']})")] if ap else []),
        "card_title": "FOR LEADERSHIP",
        "card_rows": 5,
        "card_note": "Last week's follow-ups: none were open." if not fu else f"Last week's follow-ups: {len(fu)}",
        "footer": foot("Polar pixel (all sessions) · Shopify via Polar · YoY = GA4 on both sides", f"{WOW}; {YOY}"),
    })

    # ===================== WHAT CHANGED (site + sends)
    ws, we = D(m["week_start"]), D(m["week_end"])
    days = [(ws + dt.timedelta(days=i)).isoformat() for i in range(7)]
    site_by = {d: [] for d in days}; em_by = {d: [] for d in days}; sms_by = {d: [] for d in days}
    for w in inp["whats_live"]:
        site_by[w["date"]].append(w.get("short", w["change"]))
    for e in raw["sends"]["email"]:
        em_by[e["date"]].append(e["name"])
    for x in raw["sends"]["sms"]:
        sms_by[x["date"]].append(f"{x['name']} ({f_k(x['sessions'])} sessions)")
    crows = [[{"t": f"{dow(d)} {sd(d)}", "b": True}, {"t": "\n".join(site_by[d]) or "—", "c": None if site_by[d] else "muted"},
              {"t": "\n".join(em_by[d]) or "—", "c": None if em_by[d] else "muted"}, {"t": "\n".join(sms_by[d]) or "—", "c": None if sms_by[d] else "muted"}] for d in days]
    log("What changed", "SMS sessions per send", "Polar pixel (custom_5984 = SMS, utm_campaign)", "send names dated in the week; all segments")
    log("What changed", "Email sends", "Klaviyo get_campaigns", "status Sent, send time in week (PT)", f"{m['week_start']}..{m['week_end']}")
    slides.append({"id": "changes", "type": "finding", "kicker": "What changed this week", "pill": "SITE · EMAIL · SMS",
        "missing": [f"What's live: {x}" for x in inp.get("whats_live_missing", [])],
        "headline": H("changes", "What changed this week"),
        "body": {"layout": "table_images",
                 "card": {"kind": "table", "columns": [{"h": "Day", "w": 0.85}, {"h": "Site", "w": 2.6}, {"h": "Email", "w": 1.6}, {"h": "SMS", "w": 2.35}], "rows": crows, "dense": True},
                 "images": [f"Homepage {sd(w['date'])} (mobile)" for w in inp["whats_live"] if w["surface"] == "Homepage"][:2]},
        "_obs": OB("changes"), "jamie": ["WHAT CHANGED", "WHY", "NEXT STEPS"],
        "footer": foot("Jamie's what's-live input · Klaviyo · Polar (Postscript utm_campaign)"),
    })

    # ===================== DIVIDER 1
    slides.append({"id": "div_site", "type": "divider", "num": "01", "kicker": "SECTION 1", "title": "Site and page performance",
                   "sub": "Sitewide traffic, PLPs and collections, top products, the homepage and search."})

    # ===================== SITEWIDE
    daily, daily0 = raw["pixel"]["sitewide"]["daily_cy"], raw["pixel"]["sitewide"]["daily_wow"]
    slides.append({"id": "site", "type": "finding", "kicker": "Sitewide traffic and conversion", "sec": "01", "pill": WOW.upper(),
        "headline": H("site", "Sitewide"),
        "body": {"layout": "stats_card",
                 "stats": [stat(f_int(sw["sessions"]), "Sessions", f"{d_pct(sw['sessions'], sw0['sessions'])['t']} WoW", accent=True),
                           stat(f_rate(atc), "Add-to-cart rate", f"{d_pts(atc, atc0)['t']} WoW"),
                           stat(f_rate(cvr, 2), "Conversion rate", f"{d_pts(cvr, cvr0, 2)['t']} WoW")],
                 "card": {"kind": "vbars", "title": "SESSIONS BY DAY · THIS WEEK VS SAME DAY LAST WEEK",
                          "items": [{"label": f"{dow(a['date'])} {sd(a['date'])}", "value": a["sessions"], "cmp": b["sessions"],
                                     "sub": f"CVR {f_rate(rate(a['cc'], a['sessions']), 2)}"} for a, b in zip(daily, daily0)]}},
        "_obs": OB("site"), "jamie": True,
        "footer": foot("Polar pixel, PSD Web view, all sessions", WOW),
    })

    # ===================== TOP PLPs
    P = raw["plps"]
    prior = {p["path"]: p["sessions"] for p in P["top_prior"]}; prior.update(P.get("prior_lookup", {}))
    prior_paths = [p["path"] for p in P["top_prior"]]
    rows, new_n = [], 0
    for i, p in enumerate(P["top_cy"], 1):
        isnew = p["path"] not in prior_paths; new_n += isnew
        pv = prior.get(p["path"])
        lc = P["landing_cy"].get(p["path"])
        rows.append([str(i), {"t": page_name(p["path"]), "b": True}, f_int(p["sessions"]),
                     (d_pct(p["sessions"], pv)["t"] if pv and pv >= 100 else "new") if pv is not None else "n/a",
                     f_int(lc["sessions"]) if lc else "—",
                     flag(f_rate(rate(lc["bounced"], lc["sessions"]), 0), low(lc["sessions"])) if lc else "—",
                     {"t": "NEW", "c": "accent", "b": True} if isnew else ""])
    dropped = [page_name(x) for x in prior_paths if x not in [p["path"] for p in P["top_cy"]]]
    log("Top PLPs", "Visited sessions by PLP", "Polar pixel (page_path)", "page_path CONTAINS /collections/, NOTCONTAINS /products/")
    log("Top PLPs", "Landed sessions and bounce by PLP", "Polar pixel (landing_page_path)", "landing_page_path IS <path>")
    crow = []
    for f in inp["featured"]:
        c = raw["collections"][f["path"]]; cy, c0 = c["cy"], c["wow"]
        lc, lc0 = P["landing_cy"].get(f["path"]), P["landing_wow"].get(f["path"])
        newc = c0["sessions"] < 100
        top = c.get("top_channel")
        crow.append([{"t": f["name"], "b": True},
                     f"{f_int(cy['sessions'])}  ({'new' if newc else d_pct(cy['sessions'], c0['sessions'])['t']})",
                     flag(f_rate(rate(lc["bounced"], lc["sessions"]), 0), low(lc["sessions"])) if lc else "—",
                     flag(f_rate(rate(cy["atc"], cy["sessions"])), low(cy["sessions"])),
                     flag(f_rate(rate(cy["cc"], cy["sessions"]), 2), low(cy["sessions"], cy["cc"])),
                     f_money(c["sales_cy"], k=True)])
        log("Collections", f"{f['name']} visited funnel", "Polar pixel", f"page_paths_in_session exact match {f['path']}")
        log("Collections", f"{f['name']} landed", "Polar pixel", f"landing_page_path IS {f['path']}")
        log("Collections", f"{f['name']} net sales", "Shopify via Polar (custom_60202)", f"collection_handle IS {f['handle']}")
    slides.append({"id": "plps", "type": "finding", "kicker": "Top PLPs and featured collections", "sec": "01", "pill": "VISITED · LANDED",
        "headline": H("plps", "Top PLPs and featured collections"),
        "body": {"layout": "two_cards", "split": 0.53,
                 "left": {"kind": "table", "title": "TOP 10 PLPS BY VISITED SESSIONS · NEW = NOT IN LAST WEEK'S TOP 10",
                          "columns": [{"h": "#", "w": 0.35}, {"h": "PLP", "w": 2.4}, {"h": "Visited", "w": 0.95, "a": "r"}, {"h": "WoW", "w": 0.85, "a": "r"},
                                      {"h": "Landed", "w": 0.9, "a": "r"}, {"h": "Bounce", "w": 0.8, "a": "r"}, {"h": "", "w": 0.6}], "rows": rows},
                 "right": {"kind": "table", "title": ("FEATURED COLLECTIONS · PICKED FROM THIS WEEK'S TRAFFIC" if inp.get("featured_collections_status") == "inferred_from_traffic" else "FEATURED COLLECTIONS · JAMIE'S LIST"),
                           "columns": [{"h": "Collection", "w": 1.75}, {"h": "Visited (WoW)", "w": 1.5, "a": "r"}, {"h": "Landed bounce", "w": 0.95, "a": "r"},
                                       {"h": "ATC", "w": 0.75, "a": "r"}, {"h": "CVR", "w": 0.75, "a": "r"}, {"h": "Net sales", "w": 0.95, "a": "r"}],
                           "rows": crow, "note": "ATC and CVR use visited sessions. Net sales = products in the collection (collections overlap). † low confidence."}},
        "_obs": OB("plps") + OB("collections"), "jamie": True,
        "footer": foot("Polar pixel + Shopify via Polar · visited = viewed the page at any point · landed = first page of the session", WOW),
    })

    # ===================== TOP PRODUCTS (units, web) + PRODUCT SIGNALS
    PR = raw.get("products")
    if PR:
        import re as _r2, statistics as _st
        def pslug(t, ty): return _r2.sub(r"[^a-z0-9]+", "-", f"{t} {ty}".lower()).strip("-")
        def thumb(t, ty):
            f = WORK / "assets" / "products" / f"{pslug(t, ty)}.jpg"
            return str(f) if f.exists() else None
        coll_name = {f["handle"]: f["name"] for f in inp["featured"]}
        coll_name[inp["campaign"]["shop_all"]["handle"]] = inp["campaign"]["name"]
        pool = [x for x in PR.get("pool", {}).get("rows", []) if x["units"] > 0]
        med_cvr = _st.median([rate(x["orders"], x["sessions"]) for x in pool]) if pool else None
        med_atc = _st.median([rate(x["atc"], x["pdp_views"]) for x in pool]) if pool else None
        med_views = _st.median([x["pdp_views"] for x in pool]) if pool else None
        R_ = cfg["product_signals"]
        def tone(v, med):  # highlight cells far from the pool median
            if med is None or v is None: return None
            return "good" if v >= R_["high_x_median"] * med else "bad" if v <= R_["low_x_median"] * med else None
        def signals(x):
            out = []
            atc_r, cvr_r = rate(x["atc"], x["pdp_views"]), rate(x["orders"], x["sessions"])
            if x["pdp_views"] >= R_["low_atc_min_views"] and atc_r < R_["low_atc_rate"]: out.append("HIGH VIEWS · LOW ATC")
            if med_views and x["pdp_views"] >= R_["traffic_x_median"] * med_views and cvr_r <= R_["low_x_median"] * med_cvr: out.append("HIGH VIEWS · LOW CVR")
            if x["units_wow"] >= R_["mover_min_prior"] and x["units"] >= R_["riser_min_units"] and x["units"] >= R_["riser_x"] * x["units_wow"]: out.append("RISER")
            if x["units_wow"] >= R_["faller_min_prior"] and x["units"] <= R_["faller_x"] * x["units_wow"]: out.append("FALLER")
            return out
        items = []
        for i, x in enumerate(PR["top"][:cfg.get("top_products", 10)], 1):
            atc_r, cvr_r = rate(x["atc"], x["pdp_views"]), rate(x["orders"], x["sessions"])
            dw = None if x["units_wow"] < 10 else d_pct(x["units"], x["units_wow"])
            items.append({"rank": i, "title": x["title"], "type": x["type"], "img": thumb(x["title"], x["type"]),
                          "coll": coll_name.get(x["collection"], ""),
                          "cells": [{"t": f_int(x["units"]), "b": True},
                                    {"t": "new" if dw is None else dw["t"], "c": None if dw is None else ("good" if dw["dir"] > 0 else "bad" if dw["dir"] < 0 else None)},
                                    {"t": f_money(x["net"], k=True)}, {"t": f_int(x["pdp_views"])},
                                    {"t": flag(f_rate(atc_r, 0), low(x["pdp_views"])), "c": tone(atc_r, med_atc)},
                                    {"t": flag(f_rate(cvr_r), low(x["sessions"], x["orders"])), "c": tone(cvr_r, med_cvr)}],
                          "signals": signals(x)})
        cu, wu = PR["campaign_units"], PR["web_units"]
        log("Top products", "Units, net sales, orders by product × style", "Shopify via Polar", "PSD Web view; custom_5794 = Online Store; Mystery excluded")
        log("Top products", "PDP views, add-to-cart events, sessions by product × style", "Polar pixel", "product_title × product_type")
        slides.append({"id": "products", "type": "finding", "kicker": "Top products by units (web)", "sec": "01", "pill": WOW.upper(),
            "headline": H("products", "Top products"),
            "body": {"layout": "card_full", "card": {"kind": "product_grid", "cols": 2,
                     "title": f"TOP {len(items)} BY UNITS · ONLINE STORE · {camp_name_upper(inp)} PRODUCTS = {f_rate(rate(cu['cy'], wu['cy']), 0)} OF WEB UNITS",
                     "heads": ["Units", "WoW", "Sales", "PDP views", "ATC", "CVR"], "items": items,
                     "note": f"Green / red = at least {R_['high_x_median']:g}× / at most {R_['low_x_median']:g}× the median of the top {len(pool)} products by PDP views (ATC {f_rate(med_atc, 0)}, CVR {f_rate(med_cvr)}). ATC = add-to-cart events ÷ PDP views. CVR = orders ÷ sessions with the product. App orders and Mystery styles excluded."}},
            "jamie": True,
            "footer": foot("Shopify via Polar (Online Store) + Polar pixel · one row per product and style", WOW),
        })
        # product signals: rule-based flags across the PDP-view pool
        order = ["HIGH VIEWS · LOW CVR", "HIGH VIEWS · LOW ATC", "RISER", "FALLER"]
        flagged = []
        for x in pool:
            sg = signals(x)
            if sg: flagged.append((min(order.index(g) for g in sg), -x["pdp_views"], x, sg))
        flagged.sort(key=lambda z: (z[0], z[1]))
        cards = []
        for _, _, x, sg in flagged[:R_["max_cards"]]:
            atc_r, cvr_r = rate(x["atc"], x["pdp_views"]), rate(x["orders"], x["sessions"])
            dw = None if x["units_wow"] < 10 else d_pct(x["units"], x["units_wow"])
            prank = [t.lower() for t in raw.get("search", {}).get("searchspring", {}).get("popular_rank", [])]
            hit = next((k for k, t in enumerate(prank) if t not in R_["generic_search_terms"] and _r2.search(r"\b" + _r2.escape(t) + r"\b", x["title"].lower())), None)
            l2 = f"{f_int(x['units'])} units" + (f" ({dw['t']})" if dw else "")
            if x.get("inventory_today") is not None and "HIGH VIEWS · LOW ATC" in sg: l2 += f" · {f_int(x['inventory_today'])} in stock today"
            elif hit is not None: l2 += f" · #{hit + 1} search term"
            else: l2 += f" · {f_money(x['net'], k=True)}"
            lines = [f"{f_int(x['pdp_views'])} views · ATC {f_rate(atc_r)} · CVR {f_rate(cvr_r)}", l2]
            en = PR.get("entry", {}).get("rows", {}).get(f"{x['title']}|{x['type']}")
            if en:
                def ename(pth):
                    return "this PDP" if pth.rstrip("/").endswith("/products/" + en["handle"]) else "Homepage" if pth == "/" else ("other PDP" if "/products/" in pth else page_name(pth))
                lines.append("Entry: " + ", ".join(f"{ename(pth)} {f_rate(rate(n, en['sessions']), 0)}" for pth, n in en["entry"][:2]))
                lines.append(f"Source: {en['source'][0]} {f_rate(rate(en['source'][1], x['pdp_views']), 0)} of views")
            cards.append({"tag": sg[0], "title": x["title"], "type": x["type"], "img": thumb(x["title"], x["type"]), "lines": lines})
        if cards:
            log("Product signals", "Rule-based flags across the top products by PDP views", "Polar pixel + Shopify via Polar", "rules in config.json product_signals")
            log("Product signals", "Inventory on hand", "Shopify via Polar (inventory_quantity snapshot)", "today, all locations", "snapshot")
            slides.append({"id": "product_signals", "type": "finding", "kicker": "Product signals: oddities worth a look", "sec": "01", "pill": f"{len(cards)} OF {len(flagged)} FLAGS SHOWN" if len(flagged) > len(cards) else f"{len(flagged)} FLAGGED",
                "headline": H("product_signals", "Product signals"),
                "body": {"layout": "card_full", "card": {"kind": "signal_cards", "cards": cards, "cols": 4,
                         "title": f"FLAGS ACROSS THE TOP {len(pool)} PRODUCTS BY PDP VIEWS (WEB)"}},
                "jamie": True,
                "footer": foot(f"Rules: low ATC < {f_rate(R_['low_atc_rate'], 0)} on {f_int(R_['low_atc_min_views'])}+ views; low CVR ≤ {R_['low_x_median']:g}× median on {R_['traffic_x_median']:g}× median views; riser ≥ {R_['riser_x']:g}×, faller ≤ {R_['faller_x']:g}× last week's units · inventory = today", WOW),
            })

    # ===================== HOMEPAGE
    hl, hl0 = raw["homepage"]["landing"]["cy"], raw["homepage"]["landing"]["wow"]
    hv, hv0 = raw["homepage"]["viewed"]["cy"], raw["homepage"]["viewed"]["wow"]
    def lv_rows(L, L0, V, V0):
        def cell(r, r0, dp=1):
            return f"{f_rate(r, dp)}  ({d_pts(r, r0, dp)['t']})"
        return [
            [{"t": "Sessions", "b": True}, f"{f_int(L['sessions'])}  ({d_pct(L['sessions'], L0['sessions'])['t']})", f"{f_int(V['sessions'])}  ({d_pct(V['sessions'], V0['sessions'])['t']})"],
            [{"t": "Bounce", "b": True}, cell(rate(L["bounced"], L["sessions"]), rate(L0["bounced"], L0["sessions"])), {"t": "landing only", "c": "muted"}],
            [{"t": "Viewed a product", "b": True}, cell(rate(L["pdp"], L["sessions"]), rate(L0["pdp"], L0["sessions"])), cell(rate(V["pdp"], V["sessions"]), rate(V0["pdp"], V0["sessions"]))],
            [{"t": "Add-to-cart rate", "b": True}, cell(rate(L["atc"], L["sessions"]), rate(L0["atc"], L0["sessions"])), cell(rate(V["atc"], V["sessions"]), rate(V0["atc"], V0["sessions"]))],
            [{"t": "Conversion rate", "b": True}, cell(rate(L["cc"], L["sessions"]), rate(L0["cc"], L0["sessions"]), 2), cell(rate(V["cc"], V["sessions"]), rate(V0["cc"], V0["sessions"]), 2)],
        ]
    ld = {d["date"]: d for d in raw["homepage"]["landing_daily"]}
    changes = sorted(w["date"] for w in inp["whats_live"] if w["surface"] == "Homepage")
    ba = []
    for i, c in enumerate(changes):
        cd = D(c)
        end = D(changes[i + 1]) - dt.timedelta(days=1) if i + 1 < len(changes) else we
        n = min((end - cd).days + 1, (cd - D(changes[i - 1])).days if i else 7, 7)
        def agg(start):
            ds = [(start + dt.timedelta(days=j)).isoformat() for j in range(n)]
            if not all(x in ld for x in ds):
                raise SystemExit(f"before/after needs daily homepage landing data for {ds}")
            return {k: sum(ld[x][k] for x in ds) for k in ("sessions", "bounced", "atc", "cc")}, ds
        a_, ads = agg(cd); b_, bds = agg(cd - dt.timedelta(days=n))
        ba.append([{"t": f"{sd(c)} refresh", "b": True}, f"{n} days each side ({dow(bds[0])}–{dow(bds[-1])} vs {dow(ads[0])}–{dow(ads[-1])})",
                   f"{f_rate(rate(b_['cc'], b_['sessions']), 2)} → {f_rate(rate(a_['cc'], a_['sessions']), 2)}",
                   f"{f_rate(rate(b_['bounced'], b_['sessions']))} → {f_rate(rate(a_['bounced'], a_['sessions']))}"])
        log("Homepage", f"Before/after {c}", "Polar pixel", "landing_page_path IS /", f"{bds[0]}..{bds[-1]} vs {ads[0]}..{ads[-1]}")
    log("Homepage", "Landed vs visited", "Polar pixel", "landing_page_path IS / ; custom_6843 = Viewed Homepage")
    slides.append({"id": "homepage", "type": "finding", "kicker": "Homepage performance", "sec": "01", "pill": "LANDED · VISITED",
        "headline": H("homepage", "Homepage"),
        "body": {"layout": "two_cards",
                 "left": {"kind": "table", "title": "LANDED ON THE HOMEPAGE VS VISITED IT AT ANY POINT (WoW)",
                          "columns": [{"h": "", "w": 1.6}, {"h": "Landed here", "w": 2.0, "a": "r"}, {"h": "Visited at any point", "w": 2.0, "a": "r"}], "rows": lv_rows(hl, hl0, hv, hv0), "big": True},
                 "right": {"kind": "table", "title": "BEFORE / AFTER EACH REFRESH (LANDED SESSIONS)",
                           "columns": [{"h": "Change", "w": 1.15}, {"h": "Window", "w": 2.0}, {"h": "CVR", "w": 1.35}, {"h": "Bounce", "w": 1.25}], "rows": ba,
                           "note": "Equal days each side; the day-of-week mix differs. Source split for each window is in the run log."}},
        "_obs": OB("homepage"), "jamie": True,
        "footer": foot("Polar pixel · landed = first page; visited = any page in the session", WOW),
    })

    # ===================== HOMEPAGE MODULES
    hm, htot, hitems = parse_clarity(inp["clarity_files"]["homepage"], inp["clarity_labels"]["homepage"])
    log("Homepage modules", "Module click share", "Microsoft Clarity area export (manual)", "homepage URL; mobile", hm.get("Date range"))
    slides.append({"id": "hp_modules", "type": "finding", "kicker": "Homepage · where shoppers click", "sec": "01", "pill": "CLARITY · MOBILE",
        "headline": H("hp_modules", "Homepage modules"),
        "body": {"layout": "image_card", "image": "Clarity click map: homepage (mobile)",
                 "card": {"kind": "hbars", "title": f"SHARE OF ALL HOMEPAGE CLICKS · {f_int(htot)} CLICKS, {hm.get('Page views')} PAGE VIEWS", "items": top_modules(hitems)}},
        "_obs": OB("hp_modules"), "jamie": True,
        "footer": foot("Microsoft Clarity area export (mobile) · click share = area clicks ÷ all page clicks"),
    })

    # ===================== ONSITE SEARCH
    SR = raw.get("search")
    if SR:
        q, q0 = SR["pixel"]["cy"], SR["pixel"]["wow"]
        scvr, scvr0 = rate(q["cc"], q["sessions"]), rate(q0["cc"], q0["sessions"])
        ncvr = rate(sw["cc"] - q["cc"], sw["sessions"] - q["sessions"])
        ss = SR.get("searchspring", {})
        zr = ss.get("zero_result_searches")
        pr_, rr_ = ss.get("popular_rank", []), ss.get("refined_rank", [])
        zt = ss.get("zero_result_terms", [])
        srows = [[str(i + 1), pr_[i] if i < len(pr_) else "—", rr_[i] if i < len(rr_) else "—",
                  {"t": zt[i][0], "b": True} if i < len(zt) else "—", f_int(zt[i][1]) if i < len(zt) else ""] for i in range(max(len(pr_), len(rr_), len(zt)))]
        log("Search", "Sessions that searched, searcher funnel", "Polar pixel", SR["pixel"]["filter"])
        log("Search", "Zero-result searches, top and most-refined terms", "Searchspring dashboard (manual)", "screenshots", zr["range"] if zr else None)
        slides.append({"id": "search", "type": "finding", "kicker": "Onsite search (Searchspring)", "sec": "01", "pill": WOW.upper(),
            "missing": [f"Searchspring: {x}" for x in ss.get("missing", [])],
            "headline": H("search", "Onsite search"),
            "body": {"layout": "stats_card",
                     "stats": [stat(f_int(q["sessions"]), "Sessions that searched", f"{d_pct(q['sessions'], q0['sessions'])['t']} WoW · {f_rate(rate(q['sessions'], sw['sessions']))} of sessions", accent=True),
                               stat(f_rate(scvr, 2), "Searcher conversion", f"{d_pts(scvr, scvr0, 2)['t']} WoW · non-searchers {f_rate(ncvr, 2)}"),
                               stat(zr["value"] if zr else "—", "Zero-result searches", f"{f_int(zr['per_day'])} a day (Searchspring)" if zr else "not provided")],
                     "card": {"kind": "table", "title": "TOP SEARCHES · MOST REFINED (RANK) · NO RESULTS (SEARCHES)",
                              "columns": [{"h": "#", "w": 0.35}, {"h": "Top searches", "w": 2.0}, {"h": "Most refined", "w": 2.0}, {"h": "No results", "w": 1.7}, {"h": "", "w": 0.6, "a": "r"}], "rows": srows,
                              "note": ss.get("popular_range_note", "")}},
            "_obs": OB("search"), "jamie": True,
            "footer": foot("Polar pixel (sessions that viewed /search) · Searchspring dashboard (manual)", WOW),
        })

    # ===================== DIVIDER 3
    camp = inp["campaign"]
    slides.append({"id": "div_camp", "type": "divider", "num": "02", "kicker": "SECTION 2", "title": f"Current campaign: {camp['name']}",
                   "sub": f"Landing page {camp['lp_path']}, category pages and this week's sends."})

    # ===================== CAMPAIGN LP
    cl, cl0 = raw["campaign"]["lp_landing"]["cy"], raw["campaign"]["lp_landing"]["wow"]
    cp, cp0 = raw["campaign"]["lp_page"]["cy"], raw["campaign"]["lp_page"]["wow"]
    steps = [("Landed", "sessions"), ("Viewed a product", "pdp"), ("Added to cart", "atc"), ("Started checkout", "cs"), ("Ordered", "cc")]
    fun = []
    for i, (lab, k) in enumerate(steps):
        st = {"label": lab, "value": cl[k], "display": f_int(cl[k])}
        if i:
            pk = steps[i - 1][1]
            st["rate"] = flag(f"{f_rate(rate(cl[k], cl[pk]))} of prior step", low(cl[pk], cl[k] if k == "cc" else None))
        fun.append(st)
    gcl, gcll = raw["ga4"]["campaign_lp_landing"]["cy"], raw["ga4"]["campaign_lp_landing"]["ly"]
    lvc = [
        [{"t": "Sessions", "b": True}, f"{f_int(cl['sessions'])}  ({d_pct(cl['sessions'], cl0['sessions'])['t']})", f"{f_int(cp['sessions'])}  ({d_pct(cp['sessions'], cp0['sessions'])['t']})"],
        [{"t": "Bounce", "b": True}, f"{f_rate(rate(cl['bounced'], cl['sessions']))}  ({d_pts(rate(cl['bounced'], cl['sessions']), rate(cl0['bounced'], cl0['sessions']))['t']})", {"t": "landing only", "c": "muted"}],
        [{"t": "Add-to-cart rate", "b": True}, f"{f_rate(rate(cl['atc'], cl['sessions']))}  ({d_pts(rate(cl['atc'], cl['sessions']), rate(cl0['atc'], cl0['sessions']))['t']})", f"{f_rate(rate(cp['atc'], cp['sessions']))}  ({d_pts(rate(cp['atc'], cp['sessions']), rate(cp0['atc'], cp0['sessions']))['t']})"],
        [{"t": "Conversion rate", "b": True}, flag(f"{f_rate(rate(cl['cc'], cl['sessions']), 2)}  ({d_pts(rate(cl['cc'], cl['sessions']), rate(cl0['cc'], cl0['sessions']), 2)['t']})", low(None, cl["cc"])), f"{f_rate(rate(cp['cc'], cp['sessions']), 2)}  ({d_pts(rate(cp['cc'], cp['sessions']), rate(cp0['cc'], cp0['sessions']), 2)['t']})"],
        [{"t": "YoY landed (GA4)", "b": True}, f"{f_int(gcl['sessions'])} vs {f_int(gcll['sessions'])} ({d_pct(gcl['sessions'], gcll['sessions'])['t']})", {"t": "page structure changed", "c": "muted"}],
    ]
    log("Campaign", "Landing funnel", "Polar pixel", f"landing_page_path IS {camp['lp_path']}")
    log("Campaign", "Visited", "Polar pixel", f"page_paths_in_session contains {camp['lp_path']} (no longer paths share the prefix)")
    log("Campaign", "YoY landings", "GA4 Data API via Polar", f"landingPage = {camp['lp_path']}", f"{m['week_start']}..{m['week_end']} vs {m['yoy_start']}..{m['yoy_end']}")
    slides.append({"id": "campaign", "type": "finding", "kicker": f"{camp['name']} · landing page", "sec": "02", "pill": "LANDED · VISITED",
        "missing": ["Launch date and last year's equivalent campaign (launch-to-date view)"] if not camp.get("launch_date") else [],
        "headline": H("campaign", "Campaign landing page"),
        "body": {"layout": "two_cards",
                 "left": {"kind": "funnel", "title": "LANDING-SESSION FUNNEL", "steps": fun},
                 "right": {"kind": "table", "title": "LANDED VS VISITED (WoW)", "columns": [{"h": "", "w": 1.5}, {"h": "Landed here", "w": 1.9, "a": "r"}, {"h": "Visited at any point", "w": 1.9, "a": "r"}], "rows": lvc,
                           "note": "Last year: separate category collections; this year: one landing page with category tag pages."}},
        "_obs": OB("campaign"), "jamie": True,
        "footer": foot("Polar pixel; YoY from GA4 on both sides (property on America/Juneau time)", f"{WOW}; {YOY}"),
    })

    # ===================== CAMPAIGN ENGAGEMENT
    cat = raw["campaign"]["categories"]
    items = [{"label": f"Shop all ({camp['shop_all']['name']})", "value": cat["shop_all"]["cy"], "cmp": cat["shop_all"]["wow"],
              "display": f"{f_int(cat['shop_all']['cy'])}  ({d_pct(cat['shop_all']['cy'], cat['shop_all']['wow'])['t']})", "hl": True}]
    items += [{"label": r["name"], "value": r["cy"], "cmp": r["wow"], "display": f"{f_int(r['cy'])}  ({d_pct(r['cy'], r['wow'])['t']})"} for r in cat["rows"]]
    src = {r["ch"]: r for r in raw["campaign"]["lp_by_channel"]["cy"]}; src0 = {r["ch"]: r for r in raw["campaign"]["lp_by_channel"]["wow"]}
    srows = [[r["ch"], f_int(r["sessions"]), d_pct(r["sessions"], src0.get(r["ch"], {}).get("sessions"))["t"]] for r in list(src.values())[:3]]
    sends = [[f"{dow(x['date'])} {sd(x['date'])}", x["name"], f_int(x["sessions"])] for x in raw["sends"]["sms"] if camp["shop_all"]["handle"] in x["landing"]][:3]
    log("Campaign", "Category engagement", "Polar pixel", f"page_path IS {camp['shop_all']['path']}/<tag>")
    log("Campaign", "Landing page by source", "Polar pixel (custom_5984)", f"page_paths_in_session contains {camp['lp_path']}")
    slides.append({"id": "campaign_engagement", "type": "finding", "kicker": f"{camp['name']} · category engagement", "sec": "02", "pill": WOW.upper(),
        "headline": H("campaign_engagement", "Category engagement"),
        "body": {"layout": "card_side",
                 "left": {"kind": "hbars", "title": "SESSIONS ON EACH CATEGORY PAGE VS SHOP-ALL (WoW)", "items": items, "legend": True},
                 "right": [{"kind": "table", "title": f"{camp['lp_path']} SESSIONS BY SOURCE", "columns": [{"h": "Source", "w": 1.7}, {"h": "Sessions", "w": 1.0, "a": "r"}, {"h": "WoW", "w": 0.95, "a": "r"}], "rows": srows},
                           {"kind": "table", "title": "HALLOWEEN SMS SENDS THIS WEEK", "columns": [{"h": "Day", "w": 0.85}, {"h": "Send", "w": 2.0}, {"h": "Sessions", "w": 0.8, "a": "r"}], "rows": sends}]},
        "_obs": OB("campaign_engagement"), "jamie": True,
        "footer": foot("Polar pixel · category filters are URL tag pages (/collections/halloween/<tag>)", WOW),
    })

    # ===================== CAMPAIGN MODULES
    lm, ltot, litems = parse_clarity(inp["clarity_files"]["campaign_lp"], inp["clarity_labels"]["campaign_lp"])
    log("Campaign modules", "Module click share", "Microsoft Clarity area export (manual)", f"URL contains {camp['lp_path']}; mobile", lm.get("Date range"))
    slides.append({"id": "lp_modules", "type": "finding", "kicker": f"{camp['name']} · where shoppers click", "sec": "02", "pill": "CLARITY · MOBILE",
        "headline": H("lp_modules", "Landing page modules"),
        "body": {"layout": "image_card", "image": f"Clarity click map: {camp['name']} page (mobile)",
                 "card": {"kind": "hbars", "title": f"SHARE OF ALL PAGE CLICKS · {f_int(ltot)} CLICKS, {lm.get('Page views')} PAGE VIEWS", "items": top_modules(litems)}},
        "_obs": OB("lp_modules"), "jamie": True,
        "footer": foot("Microsoft Clarity area export (mobile) · click share = area clicks ÷ all page clicks"),
    })

    # ===================== NEW DROP (only when a drop launched in the last 14 days)
    DR = raw.get("drop")
    if inp.get("drop") and DR:
        dn = inp["drop"]
        crow_d = [[{"t": d["name"], "b": True}, sd(d["launch"]), f"{d['days']}", f_int(d["units"]), f_money(d["net"], k=True), f_int(d["sessions"]),
                   flag(f_rate(rate(d["atc"], d["pdp_views"])), low(d["pdp_views"])), flag(f_rate(rate(d["orders"], d["sessions"])), low(d["sessions"], d["orders"]))]
                  for d in [DR["this"]] + DR["comparisons"]]
        trow = [[{"t": x["title"], "b": True}, x["type"], f_int(x["units"]), flag(f_rate(rate(x["orders"], x["sessions"])), low(x["sessions"], x["orders"]))] for x in DR["top_products"][:6]]
        log("New drop", "Launch-to-date units, sales, sessions; comparison drops at the same day count", "Shopify via Polar + Polar pixel", f"collection_handle IS {dn['handle']}")
        slides.append({"id": "drop", "type": "finding", "kicker": f"New drop · {dn['name']}", "sec": "02", "pill": f"LAUNCHED {sd(dn['launch'])}",
            "headline": H("drop", "New drop"),
            "body": {"layout": "two_cards", "split": 0.58,
                     "left": {"kind": "table", "title": f"LAUNCH TO DATE VS PAST DROPS AT THE SAME DAY COUNT ({DR['this']['days']} DAYS)",
                              "columns": [{"h": "Drop", "w": 1.9}, {"h": "Launched", "w": 0.9}, {"h": "Days", "w": 0.6, "a": "r"}, {"h": "Units", "w": 0.8, "a": "r"}, {"h": "Net sales", "w": 0.95, "a": "r"},
                                          {"h": "Sessions", "w": 0.95, "a": "r"}, {"h": "ATC rate", "w": 0.85, "a": "r"}, {"h": "CVR", "w": 0.75, "a": "r"}], "rows": crow_d},
                     "right": {"kind": "table", "title": "TOP PRODUCTS IN THE DROP BY UNITS", "columns": [{"h": "Product", "w": 2.2}, {"h": "Style", "w": 1.6}, {"h": "Units", "w": 0.7, "a": "r"}, {"h": "CVR", "w": 0.7, "a": "r"}], "rows": trow}},
            "_obs": OB("drop"), "jamie": True,
            "footer": foot(f"Shopify via Polar + Polar pixel · collection {dn['handle']} · sell-through lives in the buyer planner"),
        })

    # ===================== DIVIDER 4 + POST-PURCHASE
    slides.append({"id": "div_pp", "type": "divider", "num": "03", "kicker": "SECTION 3", "title": "Post-purchase and tests", "sub": "AfterSell offers after checkout."})
    ob = raw["aftersell"]["order_browser"]
    a, a0 = raw["aftersell"]["daily_cy"], raw["aftersell"]["daily_wow"]
    acc, acc0 = sum(r["accepted"] for r in a), sum(r["accepted"] for r in a0)
    rev_a = sum(r["revenue"] for r in a)
    oc = raw["aftersell"]["orders_by_channel"]; ocr = dict(oc["rows"])
    web = ocr["Online Store"]; nonweb = [(k, v) for k, v in oc["rows"] if k != "Online Store"]
    elig_web = rate(ob["eligible"], web); accr = rate(acc, ob["shown"])
    pf = [{"label": "All orders (AfterSell)", "value": ob["total_orders"], "display": f_int(ob["total_orders"]), "rate": f"Shopify, all channels: {f_int(oc['total'])}"},
          {"label": "Online Store orders", "value": web, "display": f_int(web),
           "rate": "Excludes " + " · ".join(f"{k} {f_int(v)}" for k, v in nonweb)},
          {"label": "Eligible", "value": ob["eligible"], "display": f_int(ob["eligible"]), "rate": f"{f_rate(elig_web)} of Online Store orders"},
          {"label": "Shown an offer", "value": ob["shown"], "display": f_int(ob["shown"]), "rate": f"{f_rate(rate(ob['shown'], ob['eligible']))} of eligible"},
          {"label": "Accepted", "value": acc, "display": f_int(acc), "rate": f"{f_rate(accr)} of shown"}]
    rs = [(r, n) for r, n in ob["ineligible_reasons"] if r != "Unsupported channel"]
    small = [(r, n) for r, n in rs if n < 100]
    reasons = [{"label": r, "value": n, "display": f_int(n)} for r, n in rs if n >= 100]
    if small: reasons.append({"label": "Other (" + ", ".join(r.lower() for r, _ in small) + ")", "value": sum(n for _, n in small), "display": f_int(sum(n for _, n in small)), "muted": True})
    uc = dict(ob["ineligible_reasons"]).get("Unsupported channel")
    log("Post-purchase", "Orders, eligible, shown, ineligible reasons, revenue", "AfterSell order browser (screenshot)", "post-purchase", ob["source"])
    log("Post-purchase", "Orders by sales channel", "Shopify via Polar (custom_5794)", "all views (TikTok Shop is outside PSD Web)")
    log("Post-purchase", "Accepted offers (week and WoW)", "AfterSell analytics export", "all funnels")
    slides.append({"id": "postpurchase", "type": "finding", "kicker": "Post-purchase offers (AfterSell)", "sec": "03", "pill": "ORDER BROWSER",
        "missing": [f"AfterSell: {x}" for x in inp.get("aftersell_missing", [])],
        "headline": H("postpurchase", "Post-purchase"),
        "body": {"layout": "two_cards", "split": 0.6,
                 "left": {"kind": "funnel", "title": "ALL ORDERS → ONLINE STORE → ELIGIBLE → SHOWN → ACCEPTED", "steps": pf, "rw": 2.7},
                 "right": {"kind": "hbars", "title": "OTHER REASONS ORDERS WERE INELIGIBLE", "items": reasons,
                           "note": f"An order can have several reasons. AfterSell's 'unsupported channel' ({f_int(uc)}) matches TikTok Shop and is covered by the Online Store step." if uc else "An order can have several reasons."}},
        "_obs": OB("postpurchase"), "jamie": ["WHAT CHANGED", "SO WHAT", "KEEP / KILL / CHANGE"],
        "footer": foot("AfterSell order browser + export (manual) · Shopify orders by sales channel via Polar", f"accepted {d_pct(acc, acc0)['t']} WoW"),
    })

    # ===================== DIVIDER 4 + AHEAD
    slides.append({"id": "div_next", "type": "divider", "num": "04", "kicker": "SECTION 4", "title": "Looking ahead", "sub": "Sends and site changes over the next two weeks."})
    nd = [(we + dt.timedelta(days=i)).isoformat() for i in range(1, 15)]
    aev = {d: [] for d in nd}
    for x in inp.get("ahead_items", []):
        if x["date"] in aev: aev[x["date"]].append({"tags": x.get("tags") or [x["tag"]], "text": x["text"]})
    for x in raw["ahead"]["email"]:  # Klaviyo fills email only where the calendar has none that day
        if x["date"] in aev and not any("Email" in i["tags"] for i in aev[x["date"]]):
            aev[x["date"]].append({"tags": ["Email"], "text": x["name"]})
    slides.append({"id": "ahead", "type": "finding", "kicker": "Looking ahead · next two weeks", "sec": "04", "pill": f"{sd(nd[0])}–{sd(nd[-1])}",
        "missing": [f"Looking ahead: {x}" for x in inp.get("ahead_missing", [])],
        "headline": H("ahead", "Next two weeks"),
        "body": {"layout": "calendar2", "calendar": [{"day": f"{dow(d).upper()} {sd(d)}", "items": aev[d]} for d in nd]},
        "_obs": OB("ahead"), "jamie": ["WHAT'S COMING", "DECISIONS NEEDED", "OWNERS"],
        "footer": foot(f"{inp.get('ahead_source', 'Jamie calendar input')} · Klaviyo campaigns", "next 14 days"),
    })

    # ===================== APPENDIX
    slides.append({"id": "div_appx", "type": "divider", "num": "A", "kicker": "", "title": "Appendix", "sub": ""})
    notes = [[{"t": "Missing input", "b": True}, x] for x in missing]
    notes += [[{"t": "Contradiction", "b": True}, x] for x in obs.get("run_notes", {}).get("contradictions", [])]
    notes += [[{"t": "Assumption", "b": True}, x] for x in obs.get("run_notes", {}).get("assumptions", [])]
    slides.append({"id": "appx_notes", "type": "appendix", "kicker": "APPENDIX · RUN NOTES", "headline": "Run notes: missing inputs, contradictions and assumptions",
        "body": {"layout": "card_full", "card": {"kind": "table", "columns": [{"h": "Type", "w": 1.6}, {"h": "Note", "w": 10.2}], "rows": notes}}, "footer": foot("Run")})
    ch = [[r["ch"], f_int(r["sessions"]), f_rate(rate(r["sessions"], sw["sessions"])), flag(f_rate(rate(r["atc"], r["sessions"])), low(r["sessions"])), flag(f_rate(rate(r["cc"], r["sessions"]), 2), low(r["sessions"], r["cc"]))] for r in raw["pixel"]["sitewide"]["by_channel_cy"]]
    gs, gs0 = raw["ga4"]["sitewide"]["paid_social_cy"], raw["ga4"]["sitewide"]["paid_social_ly"]
    gy = [["All traffic", f_int(g["sessions"]), f_int(gl["sessions"]), d_pct(g["sessions"], gl["sessions"])["t"], f"{f_rate(gcvr, 2)} vs {f_rate(gcvr0, 2)}"],
          ["Paid Social", f_int(gs["sessions"]), f_int(gs0["sessions"]), d_pct(gs["sessions"], gs0["sessions"])["t"], f"{f_rate(rate(gs['purchases'], gs['sessions']), 2)} vs {f_rate(rate(gs0['purchases'], gs0['sessions']), 2)}"],
          ["Excl. Paid Social", f_int(g["sessions"] - gs["sessions"]), f_int(gl["sessions"] - gs0["sessions"]), d_pct(g["sessions"] - gs["sessions"], gl["sessions"] - gs0["sessions"])["t"],
           f"{f_rate(rate(g['purchases'] - gs['purchases'], g['sessions'] - gs['sessions']), 2)} vs {f_rate(rate(gl['purchases'] - gs0['purchases'], gl['sessions'] - gs0['sessions']), 2)}"]]
    slides.append({"id": "appx_traffic", "type": "appendix", "kicker": "APPENDIX · TRAFFIC DETAIL", "headline": "Sessions by channel this week, and the GA4 year-over-year split",
        "body": {"layout": "two_cards", "left": {"kind": "table", "title": "PIXEL SESSIONS BY PSD CHANNEL GROUP", "columns": [{"h": "Channel", "w": 1.7}, {"h": "Sessions", "w": 1.1, "a": "r"}, {"h": "Share", "w": 0.8, "a": "r"}, {"h": "ATC", "w": 0.8, "a": "r"}, {"h": "CVR", "w": 0.8, "a": "r"}], "rows": ch},
                 "right": {"kind": "table", "title": "GA4: THIS WEEK VS SAME WEEKDAYS LAST YEAR", "columns": [{"h": "Scope", "w": 1.6}, {"h": "TY", "w": 0.95, "a": "r"}, {"h": "LY", "w": 0.95, "a": "r"}, {"h": "Δ", "w": 0.8, "a": "r"}, {"h": "Purchase rate", "w": 1.5, "a": "r"}], "rows": gy}},
        "footer": foot("Polar pixel; GA4 via Polar", YOY)})
    full = lambda its: [[i["label"], f_int(i["clicks"]), f_rate(i["share"])] for i in its]
    slides.append({"id": "appx_clarity", "type": "appendix", "kicker": "APPENDIX · CLARITY DETAIL", "headline": "Every Clarity area, homepage and campaign page (mobile)",
        "body": {"layout": "two_cards", "left": {"kind": "table", "title": "HOMEPAGE", "columns": [{"h": "Area", "w": 3.2}, {"h": "Clicks", "w": 1.0, "a": "r"}, {"h": "Share", "w": 0.9, "a": "r"}], "rows": full(hitems)},
                 "right": {"kind": "table", "title": camp["name"].upper(), "columns": [{"h": "Area", "w": 3.2}, {"h": "Clicks", "w": 1.0, "a": "r"}, {"h": "Share", "w": 0.9, "a": "r"}], "rows": full(litems)}},
        "footer": foot("Microsoft Clarity area exports (manual)")})
    for i in range(0, len(runlog), 12):
        slides.append({"id": f"appx_log_{i//12+1}", "type": "appendix", "kicker": "APPENDIX · RUN LOG", "headline": f"Run log {i//12+1} of {(len(runlog)+11)//12}: source and filters behind every number",
            "body": {"layout": "card_full", "card": {"kind": "table", "columns": [{"h": "Slide", "w": 1.9}, {"h": "Number", "w": 2.6}, {"h": "Source", "w": 2.6}, {"h": "Filters", "w": 3.6}, {"h": "Dates", "w": 2.3}], "rows": runlog[i:i+12]}},
            "footer": foot("All Polar rows use view Business Channel – PSD Web (31552-mpfv58vy), all sessions")})
    br = bible_rows()
    for i in range(0, len(br), 9):
        slides.append({"id": f"appx_bible_{i//9+1}", "type": "appendix", "kicker": "APPENDIX · METRIC BIBLE", "headline": f"Metric bible v1.3 ({i//9+1} of {(len(br)+8)//9})",
            "body": {"layout": "card_full", "card": {"kind": "table", "columns": [{"h": "Metric", "w": 2.0}, {"h": "Definition", "w": 3.6}, {"h": "Source / key", "w": 3.3}, {"h": "Filters", "w": 3.6}], "rows": br[i:i+9]}},
            "footer": foot("metric-bible.md")})

    deck = {"meta": {"week": WEEK, "title": "Ecom Merch Weekly"}, "slides": slides}
    (WORK / "data" / f"deck_{week}.json").write_text(json.dumps(deck, indent=1, ensure_ascii=False))
    print(f"deck_{week}.json: {len(slides)} slides, {len(runlog)} run-log rows")
    # issues stay out of the deck: they go in the chat reply for Jamie / the user to validate
    iss = ["# Issues to validate (not in the deck)", ""] + [f"- [{x['type']}] {x['issue']}" for x in raw.get("issues", [])]
    (WORK / "data" / f"issues_{week}.md").write_text("\n".join(iss) + "\n")
    print(f"issues_{week}.md: {len(raw.get('issues', []))} issues for the chat reply")

def bible_rows():
    return [
        ["Sessions", "All web storefront sessions (bots included, as in the Daily Flash)", "Polar pp.raw.polar_pixel_sessions", "PSD Web view"],
        ["Visited sessions (page)", "Sessions that viewed the page at any point", "Polar pp.raw.polar_pixel_sessions", "Exact-match page_paths_in_session pattern"],
        ["Landed sessions", "Sessions whose first page was this page", "Polar pp.raw.polar_pixel_sessions", "landing_page_path IS <path>"],
        ["Bounce", "Landed sessions with one page view and no engagement ÷ landed sessions", "Polar polar_pixel_bounced_sessions", "Landing only"],
        ["Add-to-cart rate", "Sessions with an add to cart ÷ sessions, same scope", "Polar funnel_product_added_to_cart_sessions", "Session-scoped"],
        ["Conversion rate", "Checkout-completed sessions ÷ sessions, same scope", "Polar funnel_checkout_completed_sessions", "Web storefront; app orders excluded"],
        ["Funnel step / reach", "Step ÷ prior step / step ÷ first step", "Polar funnel_*_sessions", "Same filter at every step"],
        ["Top-10 PLPs", "/collections/ pages by visited sessions; NEW = not in last week's top 10", "Polar sessions by page_path", "Excludes /products/ paths"],
        ["Featured collections", "Top 5 non-core collections by visited sessions, unless Jamie lists them", "Polar sessions by page_path", "Excludes evergreen list, campaign pages, child pages"],
        ["Category engagement", "Visited sessions on each campaign tag page, next to shop-all", "Polar sessions by page_path", "Tag pages = /collections/<parent>/<tag>"],
        ["Module click share", "Area clicks ÷ all clicks on the page", "Clarity area export", "Mobile only; not Clarity 'CTR'"],
        ["Eligibility", "Eligible orders ÷ Online Store orders", "AfterSell order browser ÷ Shopify via Polar (custom_5794)", "All channels, no view"],
        ["Acceptance rate", "Accepted offers ÷ offers shown", "AfterSell export (accepted) ÷ order browser (shown)", "Flag if scopes differ"],
        ["Net sales / orders / AOV", "Adjusted Net Sales, orders, Adjusted AOV", "Polar custom_60202, total_orders, custom_60207", "PSD Web view"],
        ["Collection net sales", "Adjusted Net Sales of products in the collection", "Polar custom_60202", "collection_handle IS <handle>"],
        ["Top products", "Top 10 product × style rows by web units; ATC = ATC events ÷ PDP views; CVR = orders ÷ product sessions", "Shopify via Polar + Polar pixel", "Online Store; Mystery excluded"],
        ["Onsite search", "Sessions that viewed /search and their conversion; terms from Searchspring", "Polar pixel + Searchspring (manual)", "Exact-match /search pattern"],
        ["YoY before Apr 2026", "GA4 on both sides; pixel shown for reference only", "GA4 via Polar / GA4 Data API", "Never mix GA4 and pixel in one delta"],
    ]

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "2026-09-28")
