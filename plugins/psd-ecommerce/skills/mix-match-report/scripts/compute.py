#!/usr/bin/env python3
"""mix-match-report · compute step.

Reads the raw Polar pulls (raw.json, shape in references/raw_schema_example.json)
and writes data.json, the only input the HTML and Excel builders accept.

Fail-closed: exits 1 with a message when a required pull is missing or the
report period has no Gift Builder orders. Data problems that do not block the
report are written to issues.md for the chat hand-back (never into the report).

usage: compute.py raw.json data.json [--config config.json] [--filler]
"""
import argparse, datetime as dt, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ["lines", "orders", "web", "traffic_daily", "traffic_landers", "traffic_channel", "traffic_device"]
M = {  # Polar metric keys
    "gross": "shopify_sales_main.raw.gross_sales",
    "disc": "shopify_sales_main.raw.discounts",
    "net": "shopify_sales_main.computed.net_sales",
    "orders": "shopify_sales_main.raw.total_orders",
    "sess": "shopify_attribution_pixel.raw.polar_pixel_sessions",
    "atc": "shopify_attribution_pixel.raw.polar_pixel_funnel_product_added_to_cart_sessions",
    "chk": "shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_started_sessions",
    "conv": "shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_completed_sessions",
}


def die(msg):
    print(f"compute.py: STOP · {msg}", file=sys.stderr)
    sys.exit(1)


def num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def label(a, b):
    a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    fa = f"{a:%b} {a.day}" + (f", {a.year}" if a.year != b.year else "")
    return f"{fa} – {b:%b} {b.day}, {b.year}"


def days(a, b):
    a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    return [(a + dt.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def total(resp):
    t = resp.get("totalData") or [{}]
    return t[0] if t else {}


def parse_props(s, issues):
    try:
        arr = json.loads(s) if isinstance(s, str) else (s or [])
        return {p.get("key"): p.get("value") for p in arr if isinstance(p, dict)}
    except json.JSONDecodeError:
        issues.append(f"Could not parse line properties: {str(s)[:80]}")
        return {}


def period(raw, cfg, issues, tag):
    for k in REQUIRED:
        if k not in raw:
            die(f"raw.{tag}.{k} is missing. Run every pull in references/polar-pulls.md for both periods.")
    units_key = cfg["units_metric"]
    divs = cfg["divisions"]

    # ---- builder lines -------------------------------------------------
    lines = []
    for r in raw["lines"].get("tableData", []):
        p = parse_props(r.get("order_line_properties"), issues)
        if not p.get("_fit_id"):
            continue
        div = (p.get("_fit_division") or "").lower()
        if div not in divs:
            issues.append(f"{tag}: line in order {r.get('order_id')} has _fit_division '{div}', skipped")
            continue
        lines.append({
            "date": r.get("date"), "order_id": str(r.get("order_id")), "fit_id": p["_fit_id"],
            "kit": p.get("_fit") or "?", "div": div, "slot": p.get("_fit_slot") or "?",
            "fit_name": p.get("_fit_name"), "fit_price": num(p.get("_fit_price")) / 100,
            "product": r.get("product_title") or "(unknown product)",
            "purchase_type": r.get("purchase_type"),
            "gross": num(r.get(M["gross"])), "disc": -num(r.get(M["disc"])), "net": num(r.get(M["net"])),
            "units": num(r.get(units_key)),
        })

    # ---- orders (full order incl. add-ons, from discount code) ----------
    order_net, order_date = defaultdict(float), {}
    for r in raw["orders"].get("tableData", []):
        oid = str(r.get("order_id"))
        order_net[oid] += num(r.get(M["net"]))
        order_date.setdefault(oid, r.get("date"))

    line_orders = {l["order_id"] for l in lines}
    code_only = set(order_net) - line_orders
    if code_only:
        issues.append(f"{tag}: {len(code_only)} order(s) used code \"{cfg['discount_code']}\" but have no _fit lines "
                      f"(e.g. {sorted(code_only)[:3]}). Not counted as Gift Builder orders.")
    no_code = line_orders - set(order_net)
    if no_code:
        issues.append(f"{tag}: {len(no_code)} order(s) have _fit lines but no \"{cfg['discount_code']}\" code "
                      f"(e.g. {sorted(no_code)[:3]}). Counted; their add-on sales are unknown and treated as $0.")

    by_order = defaultdict(list)
    for l in lines:
        by_order[l["order_id"]].append(l)

    s = Counter()
    mix = Counter()
    div = {d: Counter() for d in divs}
    kd = defaultdict(Counter)
    kd_orders = defaultdict(set)
    kd_fits = defaultdict(set)
    div_fits = {d: set() for d in divs}
    picks = defaultdict(Counter)
    prices = defaultdict(Counter)      # (kit,div) -> Counter(fit_price)
    compares = defaultdict(Counter)    # (kit,div) -> Counter(list value of a full outfit)
    fit_gross = defaultdict(float)
    fit_key = {}
    daily = defaultdict(Counter)
    daily_fits = defaultdict(set)
    kit_meta = {}

    for oid, ls in by_order.items():
        lnet = sum(l["net"] for l in ls)
        onet = order_net.get(oid, lnet)
        addon = max(onet - lnet, 0.0) if oid in order_net else 0.0
        s["gb_orders"] += 1
        s["kit_net_sales"] += lnet
        s["addon_net_sales"] += addon
        s["addon_orders"] += 1 if addon > 0.5 else 0
        s["new_orders"] += 1 if any(l["purchase_type"] == "new" for l in ls) else 0
        dset = {l["div"] for l in ls}
        mix["mixed" if len(dset) > 1 else f"{next(iter(dset))}_only"] += 1
        for d_ in dset:
            div[d_]["orders"] += 1
        day = ls[0]["date"] or order_date.get(oid)
        daily[day]["orders"] += 1
        daily[day]["net_sales"] += lnet + addon
        for l in ls:
            k = (l["kit"], l["div"])
            s["units"] += l["units"]; s["gb_gross_sales"] += l["gross"]; s["gb_discounts"] += l["disc"]
            div[l["div"]]["units"] += l["units"]; div[l["div"]]["net_sales"] += l["net"]
            div[l["div"]]["gross_sales"] += l["gross"]; div[l["div"]]["discounts"] += l["disc"]
            div_fits[l["div"]].add(l["fit_id"])
            kd[k]["units"] += l["units"]; kd[k]["net_sales"] += l["net"]
            kd[k]["gross_sales"] += l["gross"]; kd[k]["discounts"] += l["disc"]
            kd_orders[k].add(oid); kd_fits[k].add(l["fit_id"])
            picks[l["slot"]][l["product"]] += l["units"]
            if l["fit_price"]:
                prices[k][round(l["fit_price"], 2)] += 1
            fit_gross[l["fit_id"]] += l["gross"]; fit_key[l["fit_id"]] = k
            daily_fits[day].add(l["fit_id"])
            kit_meta.setdefault(l["kit"], {"name": l["fit_name"], "slots": set()})["slots"].add(l["slot"])
    for f, g in fit_gross.items():
        compares[fit_key[f]][round(g, 2)] += 1
    s["outfits"] = len(fit_gross)
    for d_ in divs:
        div[d_]["outfits"] = len(div_fits[d_])
    for k in kd:
        kd[k]["outfits"] = len(kd_fits[k]); kd[k]["orders"] = len(kd_orders[k])
    for day_, fs in daily_fits.items():
        daily[day_]["outfits"] = len(fs)
    s["gb_net_sales"] = s["kit_net_sales"] + s["addon_net_sales"]

    # ---- web totals ------------------------------------------------------
    w = total(raw["web"])
    s["web_net_sales"] = num(w.get(M["net"]))
    s["web_orders"] = num(w.get(M["orders"]))
    if not s["web_orders"]:
        issues.append(f"{tag}: PSD Web totals are zero; share-of-web figures will read 0%.")

    # ---- traffic ---------------------------------------------------------
    t = total(raw["traffic_daily"])
    lt = total(raw["traffic_landers"])
    s["sessions_visited"] = num(t.get(M["sess"]))
    s["atc_sessions"] = num(t.get(M["atc"]))
    s["checkout_sessions"] = num(t.get(M["chk"]))
    s["converted_sessions"] = num(t.get(M["conv"]))
    s["landers"] = num(lt.get(M["sess"]))
    for r in raw["traffic_daily"].get("tableData", []):
        daily[r.get("date")]["sessions_visited"] += num(r.get(M["sess"]))
        daily[r.get("date")]["converted_sessions"] += num(r.get(M["conv"]))

    def seg(name, row):
        n = num(row.get(M["sess"]))
        return {"segment": name, "sessions": n,
                "atc_rate": num(row.get(M["atc"])) / n if n else 0,
                "cvr": num(row.get(M["conv"])) / n if n else 0}

    mid = {k: num(t.get(k)) - num(lt.get(k)) for k in (M["sess"], M["atc"], M["conv"])}
    entry = [seg("Landed on builder", lt), seg("Reached it mid-session", mid)]
    ch = cfg["channel_dimension"]
    by_channel = sorted([seg(r.get(ch) or "(none)", r) for r in raw["traffic_channel"].get("tableData", [])], key=lambda x: -x["sessions"])
    by_device = sorted([seg((r.get("session_device_type") or "(none)").capitalize(), r) for r in raw["traffic_device"].get("tableData", [])], key=lambda x: -x["sessions"])

    return {"summary": dict(s), "division": {d_: dict(v) for d_, v in div.items()}, "mix": dict(mix),
            "kd": {k: dict(v) for k, v in kd.items()}, "picks": picks, "daily": daily,
            "prices": prices, "compares": compares, "kit_meta": kit_meta,
            "traffic": {"entry": entry, "by_channel": by_channel, "by_device": by_device}, "lines": len(lines)}


def r2(d):
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw"); ap.add_argument("out")
    ap.add_argument("--config", default=os.path.join(HERE, "..", "config.json"))
    ap.add_argument("--filler", action="store_true", help="mark the report as filler data (banner on every output)")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    raw = json.load(open(a.raw))
    for k in ("meta", "cur", "prev"):
        if k not in raw:
            die(f"raw.{k} is missing")
    m = raw["meta"]
    for k in ("period", "compare"):
        if not (m.get(k, {}).get("from") and m.get(k, {}).get("to")):
            die(f"raw.meta.{k}.from/to is missing. Ask the user for the report and comparison periods first.")
    issues = []
    C = period(raw["cur"], cfg, issues, "report period")
    P = period(raw["prev"], cfg, issues, "comparison period")
    if C["summary"].get("gb_orders", 0) == 0:
        die("no Gift Builder orders (lines with _fit_id) in the report period. Check the dates and the lines pull; nothing was built.")
    if P["summary"].get("gb_orders", 0) == 0:
        issues.append("Comparison period has no Gift Builder orders; every change reads as a dash.")

    # ---- kits: config order, then any new handle seen in the data ----------
    kits = []
    known = {k["handle"]: k for k in cfg["kits"]}
    order = [k["handle"] for k in cfg["kits"]] + sorted(set(C["kit_meta"]) - set(known))
    for h in order:
        base = known.get(h)
        if not base:
            meta = C["kit_meta"][h]
            issues.append(f"New kit handle '{h}' ({meta['name']}) is not in config.json; shown with prices from the orders.")
            slots = [s_ for s_ in cfg["slot_order"] if s_ in meta["slots"]] + sorted(meta["slots"] - set(cfg["slot_order"]))
            base = {"handle": h, "name": meta["name"] or h, "slots": slots, "price": {}, "compare_at": {}}
        kit = {"handle": h, "name": base["name"], "slots": base["slots"], "price": {}, "compare_at": {}}
        for d_ in cfg["divisions"]:
            seen_p = C["prices"].get((h, d_)) or P["prices"].get((h, d_))
            seen_c = C["compares"].get((h, d_)) or P["compares"].get((h, d_))
            kit["price"][d_] = seen_p.most_common(1)[0][0] if seen_p else base["price"].get(d_, 0)
            kit["compare_at"][d_] = seen_c.most_common(1)[0][0] if seen_c else base["compare_at"].get(d_, 0)
            cp, cc = base["price"].get(d_), base["compare_at"].get(d_)
            if seen_p and cp is not None and abs(kit["price"][d_] - cp) > 0.01:
                issues.append(f"Kit {h}/{d_}: orders show price ${kit['price'][d_]:g}, config says ${cp:g}. Report uses the order price; update config.json if the change is permanent.")
            if seen_c and cc is not None and abs(kit["compare_at"][d_] - cc) > 0.01:
                issues.append(f"Kit {h}/{d_}: outfit list value on orders is ${kit['compare_at'][d_]:g}, config compare-at is ${cc:g}. Item prices may have changed.")
        kits.append(kit)

    kit_division = []
    zero = {"outfits": 0, "orders": 0, "units": 0, "net_sales": 0.0, "gross_sales": 0.0, "discounts": 0.0}
    for k in kits:
        for d_ in cfg["divisions"]:
            c = {**zero, **C["kd"].get((k["handle"], d_), {})}
            p = {**zero, **P["kd"].get((k["handle"], d_), {})}
            kit_division.append(r2({"kit": k["handle"], "kit_name": k["name"], "division": d_,
                                    "price": k["price"][d_], "compare_at": k["compare_at"][d_], **c,
                                    "prev_outfits": p["outfits"], "prev_net_sales": p["net_sales"]}))

    # ---- daily, aligned by day index ------------------------------------
    cd = days(m["period"]["from"], m["period"]["to"])
    pd = days(m["compare"]["from"], m["compare"]["to"])
    if len(cd) != len(pd):
        issues.append(f"Report period is {len(cd)} days and comparison is {len(pd)} days; totals are not like-for-like and the daily chart pairs days by position.")
    daily = []
    for i, d_ in enumerate(cd):
        c = C["daily"].get(d_, {})
        pdd = pd[i] if i < len(pd) else None
        p = P["daily"].get(pdd, {}) if pdd else {}
        daily.append({"date": d_, "net_sales": round(c.get("net_sales", 0), 2), "orders": c.get("orders", 0),
                      "outfits": c.get("outfits", 0), "sessions_visited": c.get("sessions_visited", 0),
                      "converted_sessions": c.get("converted_sessions", 0), "prev_date": pdd,
                      "prev_net_sales": round(p.get("net_sales", 0), 2) if pdd else None,
                      "prev_orders": p.get("orders", 0) if pdd else None, "prev_outfits": p.get("outfits", 0) if pdd else None,
                      "prev_sessions_visited": p.get("sessions_visited", 0) if pdd else None})

    top = {}
    for slot, prods in C["picks"].items():
        tot = sum(prods.values()) or 1
        top[slot] = [{"product": p, "units": u, "share": round(u / tot, 4)} for p, u in prods.most_common(5)]

    keys = ["gb_orders", "outfits", "units", "gb_gross_sales", "gb_discounts", "kit_net_sales", "addon_net_sales",
            "addon_orders", "new_orders", "web_net_sales", "web_orders", "gb_net_sales", "sessions_visited",
            "landers", "atc_sessions", "checkout_sessions", "converted_sessions"]
    summ = lambda s: r2({k: s.get(k, 0) for k in keys})
    divz = lambda D: {d_: r2({**zero, **D.get(d_, {})}) for d_ in cfg["divisions"]}
    mixz = lambda x: {k: x.get(k, 0) for k in ("men_only", "youth_only", "mixed")}

    if C["summary"].get("sessions_visited", 0) < 100:
        issues.append(f"Only {int(C['summary'].get('sessions_visited', 0))} builder sessions in the report period; traffic rates are low-confidence.")

    data = {
        "meta": {"title": cfg["report_title"], "store": cfg["store"], "filler": bool(a.filler),
                 "period": {**m["period"], "label": label(m["period"]["from"], m["period"]["to"])},
                 "compare": {**m["compare"], "label": label(m["compare"]["from"], m["compare"]["to"])},
                 "landing_path": cfg["landing_path"], "discount_code": cfg["discount_code"],
                 "view": cfg["polar_view_name"], "generated": m.get("generated") or dt.date.today().isoformat()},
        "kits": kits,
        "summary": {"cur": summ(C["summary"]), "prev": summ(P["summary"])},
        "division": {"cur": divz(C["division"]), "prev": divz(P["division"])},
        "order_mix": {"cur": mixz(C["mix"]), "prev": mixz(P["mix"])},
        "kit_division": kit_division,
        "daily": daily,
        "traffic": {k: [r2(x) for x in v] for k, v in C["traffic"].items()},
        "top_picks": top,
        "issues": issues,
    }
    json.dump(data, open(a.out, "w"), indent=1)
    issues_path = os.path.join(os.path.dirname(os.path.abspath(a.out)), "issues.md")
    with open(issues_path, "w") as f:
        f.write("# Issues found while computing\n\n" + ("\n".join(f"- {i}" for i in issues) if issues else "- None") + "\n")
    s = data["summary"]["cur"]
    print(f"compute.py: OK · {int(s['gb_orders'])} orders, {int(s['outfits'])} outfits, ${s['gb_net_sales']:,.2f} net · "
          f"{C['lines']} builder lines · {len(issues)} issue(s) → {issues_path}")


if __name__ == "__main__":
    main()
