#!/usr/bin/env python3
"""Join Retently NPS responses to the Shopify order each one rated.

Usage: python3 -I nps_join.py <run_dir> <week_start>
Reads  <run_dir>/inputs/retently.csv and <run_dir>/data/nps_orders.json (the saved Shopify GraphQL result, see SKILL.md §3)
Writes <run_dir>/data/nps_joined.pkl
Windows: cur = last 4 weeks (incl. this week), base = the 4 weeks before.
Match rule: the customer's latest order fulfilled at least 5 days before the response (survey fires 7 days after fulfillment).
"""
import json, sys
from datetime import timedelta
import numpy as np, pandas as pd
RUN, WS = sys.argv[1], sys.argv[2]
WK0 = pd.Timestamp(WS); END = WK0 + timedelta(days=7); CUR0 = WK0 - timedelta(days=21); BASE0 = WK0 - timedelta(days=49)
data = json.load(open(f"{RUN}/data/nps_orders.json"))["data"]
rows = []
for v in data.values():
    for c in v["nodes"]:
        em = ((c.get("defaultEmailAddress") or {}).get("emailAddress") or "").lower()
        for o in c["orders"]["nodes"]:
            f = (o.get("fulfillments") or [{}]); f = f[0] if f else {}
            rows.append(dict(em=em, norders=int(c["numberOfOrders"]), created=o["createdAt"], src=o["sourceName"],
                             ship=(o.get("shippingLine") or {}).get("title"), ful=f.get("createdAt"), dlv=f.get("deliveredAt")))
O = pd.DataFrame(rows)
for c in ["created", "ful", "dlv"]: O[c] = pd.to_datetime(O[c], utc=True).dt.tz_convert("America/Los_Angeles").dt.tz_localize(None)
r = pd.read_csv(f"{RUN}/inputs/retently.csv", low_memory=False)
r["dt"] = pd.to_datetime(r["Response date (ISO)"]).dt.tz_convert("America/Los_Angeles").dt.tz_localize(None)
r["em"] = r.Email.str.lower().str.strip()
n = r[(r.Metric == "NPS") & (r.dt >= BASE0) & (r.dt < END)].copy()
def match(row):
    c = O[(O.em == row.em) & O.ful.notna() & (O.ful <= row.dt - pd.Timedelta(days=5))]
    return c.sort_values("ful").iloc[-1] if len(c) else None
m = [match(x) for x in n.itertuples()]
n["matched"] = [x is not None for x in m]
for col in ["created", "ful", "dlv", "ship", "src", "norders"]: n[col] = [x[col] if x is not None else None for x in m]
n["per"] = np.where(n.dt >= CUR0, "cur", "base")
n["d_ship"] = (pd.to_datetime(n.ful) - pd.to_datetime(n.created)).dt.total_seconds() / 86400
n["d_tot"] = (pd.to_datetime(n.dlv) - pd.to_datetime(n.created)).dt.total_seconds() / 86400
n.to_pickle(f"{RUN}/data/nps_joined.pkl")
print(f"NPS responses {len(n)} · matched {n.matched.mean():.0%} · base {int((n.per=='base').sum())} · cur {int((n.per=='cur').sum())}")
if n.matched.mean() < 0.9: print("WARNING: under 90% matched; check the email lookup covered every respondent")
