#!/usr/bin/env python3
"""Write a FILLER raw.json in the exact shape of the Polar pulls, for testing the
harness and regenerating the example report. Never use it for a real run.

usage: make_fixture.py out_raw.json [--from 2026-11-11 --to 2026-11-17 --cfrom 2026-11-04 --cto 2026-11-10]
"""
import argparse, datetime as dt, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
M = {
    "gross": "shopify_sales_main.raw.gross_sales", "disc": "shopify_sales_main.raw.discounts",
    "net": "shopify_sales_main.computed.net_sales", "orders": "shopify_sales_main.raw.total_orders",
    "sess": "shopify_attribution_pixel.raw.polar_pixel_sessions",
    "atc": "shopify_attribution_pixel.raw.polar_pixel_funnel_product_added_to_cart_sessions",
    "chk": "shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_started_sessions",
    "conv": "shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_completed_sessions",
}
MIX = {"men": {"us": .25, "ut": .21, "uts": .21, "uh": .14, "utsh": .09, "sp": .10},
       "youth": {"us": .29, "ut": .30, "uts": .17, "uh": .12, "utsh": .07, "sp": .05}}
PICKS = {
    "fit-3pk": ["3 Pack - Beach Blaze", "3 Pack - Holiday Heat", "3 Pack - Solids Black", "3 Pack - Snow Leopard", "3 Pack - Candy Cane Camo", "3 Pack - Neon Static"],
    "fit-shorts": ["Snow Leopard Active Short", "Black Camo Active Short", "Solid Navy Active Short", "Cheetah Ice Active Short", "Sunset Fade Active Short"],
    "fit-tee": ["Logo Box Tee - Black", "Logo Box Tee - White", "Peace Sign Tee", "Holiday Script Tee", "Lounge Tee - Heather"],
    "fit-hoodie": ["Logo Hoodie - Black", "Logo Hoodie - Heather", "Snow Leopard Hoodie", "Fleece Pullover - Navy"],
    "fit-pants": ["Lounge Pant - Black", "Lounge Pant - Snow Leopard", "Fleece Jogger - Heather", "Plaid Lounge Pant"],
}
W = [.30, .22, .17, .13, .10, .08]
CHANNELS = [("Paid Social", .34, .036), ("Email", .19, .071), ("SMS", .11, .083), ("Direct", .13, .058),
            ("Organic Search", .09, .041), ("Paid Search", .08, .049), ("Organic Social", .06, .022)]
DEVICES = [("mobile", .78, .041), ("desktop", .19, .067), ("tablet", .03, .044)]


def wpick(d):
    r, acc = random.random(), 0
    for k, w in d.items():
        acc += w
        if r <= acc:
            return k
    return list(d)[-1]


def split_price(total, parts):
    """Spread a kit list value across its items the way item prices would."""
    shares = {"fit-3pk": 62, "fit-shorts": 48, "fit-tee": 40, "fit-hoodie": 75, "fit-pants": 75}
    w = [shares[p] for p in parts]
    out = [round(total * x / sum(w), 2) for x in w]
    out[-1] = round(total - sum(out[:-1]), 2)
    return out


def sim(start, end, scale, kits, path):
    lines, orders, tdaily = [], [], []
    oid = random.randint(7300000000000, 7310000000000)
    T = {k: 0 for k in ("sess", "atc", "chk", "conv")}
    landers = {k: 0 for k in ("sess", "atc", "chk", "conv")}
    web_net = web_orders = 0
    d = dt.date.fromisoformat(start)
    i = 0
    while d <= dt.date.fromisoformat(end):
        n = max(5, int(random.gauss(64 * scale * (1 + .03 * i), 7)))
        for _ in range(n):
            oid += random.randint(3, 40)
            ptype = "new" if random.random() < .57 else "repeat"
            base = "men" if random.random() < .70 else "youth"
            onet = 0
            for j in range(random.choices([1, 2, 3], [.80, .16, .04])[0]):
                div = base if (j == 0 or random.random() < .55) else ("youth" if base == "men" else "men")
                kit = kits[wpick(MIX[div])]
                price, comp = kit["price"][div], kit["compare_at"][div]
                fid = "fit_" + "".join(random.choice("abcdefghijkmnpqrstuvwxyz23456789") for _ in range(12))
                for slot, g in zip(kit["slots"], split_price(comp, kit["slots"])):
                    disc = round(g * (comp - price) / comp, 2)
                    props = [{"key": "_fit_id", "value": fid}, {"key": "_fit", "value": kit["handle"]},
                             {"key": "_fit_division", "value": div}, {"key": "_fit_slot", "value": slot},
                             {"key": "_fit_name", "value": kit["name"].replace("3-Pack", "3-Pack")},
                             {"key": "_fit_icon", "value": f"//www.psd.com/cdn/shop/files/fit-icon-{kit['handle']}.svg"},
                             {"key": "_fit_price", "value": str(int(price * 100))}]
                    lines.append({M["gross"]: g, M["disc"]: -disc, M["net"]: round(g - disc, 2), "custom_60206": 1,
                                  "order_line_properties": json.dumps(props, separators=(",", ":")),
                                  "order_id": str(oid), "product_title": random.choices(PICKS[slot], W[:len(PICKS[slot])])[0],
                                  "purchase_type": ptype, "date": d.isoformat()})
                    onet += g - disc
            if random.random() < .31:
                onet += round(random.uniform(18, 70), 2)
            orders.append({M["orders"]: 1, M["gross"]: 0, M["disc"]: 0, M["net"]: round(onet, 2), "order_id": str(oid), "date": d.isoformat()})
        sess = int(n / random.uniform(.040, .046))
        row = {M["sess"]: sess, M["atc"]: int(sess * random.uniform(.205, .235)), M["conv"]: int(n / random.uniform(.80, .86))}
        row[M["chk"]] = int(row[M["atc"]] * random.uniform(.40, .46))
        tdaily.append({**row, "date": d.isoformat()})
        for k in T:
            T[k] += row[M[k]]
        lshare = random.uniform(.36, .42)
        landers["sess"] += int(sess * lshare); landers["atc"] += int(row[M["atc"]] * lshare * .89)
        landers["chk"] += int(row[M["chk"]] * lshare * .9); landers["conv"] += int(row[M["conv"]] * lshare * 1.15)
        wn = random.gauss(84000, 6000) * (1 + .04 * (scale - 1))
        web_net += wn; web_orders += int(wn / random.uniform(76, 82))
        d += dt.timedelta(days=1); i += 1

    def segs(parts, dim):
        rows, rem = [], dict(T)
        for idx, (name, share, cvr) in enumerate(parts):
            last = idx == len(parts) - 1
            s = rem["sess"] if last else int(T["sess"] * share * random.uniform(.92, 1.08))
            rem["sess"] -= s
            atc = int(s * min(.45, cvr * random.uniform(4.6, 5.4)))
            conv = int(s * cvr * random.uniform(.9, 1.1))
            rows.append({dim: name, M["sess"]: s, M["atc"]: atc, M["chk"]: int(atc * .43), M["conv"]: conv})
        return rows

    tot = lambda r: [{M[k]: v for k, v in r.items()}]
    return {
        "lines": {"tableData": lines},
        "orders": {"tableData": orders},
        "web": {"totalData": [{M["orders"]: web_orders, M["net"]: round(web_net, 2)}]},
        "traffic_daily": {"tableData": tdaily, "totalData": tot(T)},
        "traffic_landers": {"totalData": tot(landers)},
        "traffic_channel": {"tableData": segs(CHANNELS, "custom_5984")},
        "traffic_device": {"tableData": segs(DEVICES, "session_device_type")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--from", dest="f", default="2026-11-11"); ap.add_argument("--to", dest="t", default="2026-11-17")
    ap.add_argument("--cfrom", default="2026-11-04"); ap.add_argument("--cto", default="2026-11-10")
    ap.add_argument("--seed", type=int, default=1118)
    a = ap.parse_args()
    random.seed(a.seed)
    cfg = json.load(open(os.path.join(HERE, "..", "config.json")))
    kits = {k["handle"]: k for k in cfg["kits"]}
    raw = {"meta": {"period": {"from": a.f, "to": a.t}, "compare": {"from": a.cfrom, "to": a.cto}, "generated": a.t, "fixture": True},
           "prev": sim(a.cfrom, a.cto, .86, kits, cfg["landing_path"]),
           "cur": sim(a.f, a.t, 1.0, kits, cfg["landing_path"])}
    json.dump(raw, open(a.out, "w"))
    print("fixture written:", a.out, len(raw["cur"]["lines"]["tableData"]), "lines")


if __name__ == "__main__":
    main()
