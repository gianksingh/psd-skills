#!/usr/bin/env python3
"""Ecom Ops Weekly Flash: preflight. Run BEFORE any connector pull or build.

Usage:  python3 -I check_inputs.py <run_dir> <week_start YYYY-MM-DD> [--windows-only]

1. Prints the reporting windows every slide uses for this week (paste into the intake confirmation).
2. Checks each uploaded file in <run_dir>/inputs/ exists, has the columns the harness reads, and covers
   the dates it needs. Exit code 0 = all required inputs pass; 1 = stop and ask the user for what's listed.
"""
import sys, os
from datetime import timedelta
import pandas as pd

RUN, WS = sys.argv[1], sys.argv[2]
WK0 = pd.Timestamp(WS); WK1 = WK0 + timedelta(days=6); LY = lambda d: d - timedelta(days=364)
if WK0.weekday() != 0: sys.exit(f"PREFLIGHT FAILED: {WS} is not a Monday")
d = lambda x: f"{x:%a %b %-d, %Y}"
W = {
 "This week":                  (WK0, WK1),
 "Prior week":                 (WK0 - timedelta(days=7), WK1 - timedelta(days=7)),
 "Same week last year":        (LY(WK0), LY(WK1)),
 "Last 4 weeks":               (WK0 - timedelta(days=21), WK1),
 "Same 4 weeks last year":     (LY(WK0 - timedelta(days=21)), LY(WK1)),
 "NPS prior 4 weeks (base)":   (WK0 - timedelta(days=49), WK0 - timedelta(days=22)),
 "13-week survey trend":       (WK0 - timedelta(days=84 + 21), WK1),
 "Outlook (next 4 weeks)":     (WK0 + timedelta(days=7), WK1 + timedelta(days=28)),
}
USE = [
 ("Peak tripwires (02)", "This week vs plan / same week LY; delivery and survey rows on the last 4 weeks vs the same 4 weeks LY; sparkline = last 4 weeks"),
 ("Volume, plan and outlook (03)", "Last 4 weeks actual vs plan, then the next 4 weeks: forecast vs projection, with same week LY"),
 ("Fulfillment and delivery (04)", "Medians this week vs same week LY; delivery-contact rates last 4 weeks vs same 4 weeks LY; shipping service this week"),
 ("Customer service (05)", "This week vs prior week (volumes Mon–Sun; SLA/AI from the export days); CSAT this week; AI vs human CSAT last 4 weeks"),
 ("Voice of the customer (06)", "Rolling 4 weeks vs same 4 weeks LY; 13-week trend; NPS cuts last 4 weeks vs NPS prior 4 weeks"),
 ("Returns pipeline (07)", "Open stages and at-DC aging as of the run date; submitted / processed / exchanges last 4 weeks vs same 4 weeks LY"),
 ("Return trends (08)", "Reasons last 4 weeks vs same 4 weeks LY; return rate and products for orders placed 8–5 weeks ago"),
]
print(f"REPORTING WINDOWS · week of {WS}\n")
for k, (a, b) in W.items(): print(f"  {k:<28} {d(a)} → {d(b)}")
print()
for s, r in USE: print(f"  {s:<32} {r}")
if "--windows-only" in sys.argv: sys.exit(0)

print("\nINPUT CHECKS")
ok = True
def res(name, good, msg, required=True):
    global ok
    tag = "PASS" if good else ("FAIL" if required else "WARN")
    if not good and required: ok = False
    print(f"  [{tag}] {name}: {msg}")
def need(path, name, required=True):
    if not os.path.exists(path): res(name, False, f"missing ({os.path.relpath(path, RUN)})", required); return False
    return True
def covers(series, a, b): return series.min() <= a + timedelta(days=1) and series.max() >= b - timedelta(hours=1)

GCOLS = ["Ticket id", "Tags", "Channel", "Creation date", "Closed date", "First response time (s)", "Resolution time (s)", "Customer email",
         "Ticket Field: Ticket Reason", "Ticket Field: Order Number", "Ticket Field: AI Agent Outcome", "Ticket Field: Resolution", "Created by an agent"]
for f, (a, b), label in [("gorgias_cy.csv", W["Last 4 weeks"], "Gorgias tickets, last 4 weeks"), ("gorgias_ly.csv", W["Same 4 weeks last year"], "Gorgias tickets, same 4 weeks LY")]:
    p = f"{RUN}/inputs/{f}"
    if need(p, label):
        g = pd.read_csv(p, low_memory=False); miss = [c for c in GCOLS if c not in g.columns]
        if miss: res(label, False, f"missing columns {miss}"); continue
        c = pd.to_datetime(g["Creation date"], format="%m/%d/%Y %H:%M", errors="coerce")
        full = covers(c, a, b)
        res(label, c.min() <= a + timedelta(days=1), f"{len(g):,} tickets, {c.min():%b %-d} → {c.max():%b %-d}; needs {a:%b %-d} → {b:%b %-d}"
            + ("" if full else (" (ends early: SLA/AI rows will cover fewer days)" if "LY" not in label else " (ends early: LY delivery rates cover fewer days)")))
p = f"{RUN}/inputs/retently.csv"
if need(p, "Retently export"):
    r = pd.read_csv(p, low_memory=False)
    miss = [c for c in ["Email", "Campaign", "Metric", "Main rating", "Response date (ISO)", "Topics", "Main open-ended", "ticket_id"] if c not in r.columns]
    if miss: res("Retently export", False, f"missing columns {miss}")
    else:
        t = pd.to_datetime(r["Response date (ISO)"], errors="coerce").dt.tz_convert("America/Los_Angeles").dt.tz_localize(None)
        camps = set(r.Campaign.dropna())
        need_c = ["CSAT: Ticket Solved - Email", "DSAT: US Delivery Service Experience"]
        res("Retently campaigns", all(c in camps for c in need_c) and (r.Metric == "NPS").any(), f"NPS {'yes' if (r.Metric=='NPS').any() else 'NO'}, " + ", ".join(f"{c} {'yes' if c in camps else 'NO'}" for c in need_c))
        a = W["13-week survey trend"][0]; la = W["Same 4 weeks last year"][0]
        res("Retently dates", t.min() <= min(a, la) + timedelta(days=1) and t.max() >= WK1 - timedelta(days=1),
            f"{t.min():%b %-d, %Y} → {t.max():%b %-d, %Y}; needs {min(a, la):%b %-d, %Y} → {WK1:%b %-d, %Y}")
p = f"{RUN}/inputs/forecast.xlsx"
if need(p, "Q4 Staffing Forecast"):
    x = pd.ExcelFile(p)
    if "Daily Forecast" not in x.sheet_names: res("Q4 Staffing Forecast", False, "no 'Daily Forecast' tab")
    else:
        F = pd.read_excel(x, "Daily Forecast", header=3); F = F[pd.to_datetime(F["Date"], errors="coerce").notna()]
        dts = pd.to_datetime(F["Date"]); miss = [c for c in ["Web orders", "TikTok orders", "Web tickets", "TikTok tickets"] if c not in F.columns]
        a, b = W["Last 4 weeks"][0], W["Outlook (next 4 weeks)"][1]
        res("Q4 Staffing Forecast", not miss and dts.min() <= a and dts.max() >= WK1,
            f"Daily Forecast {dts.min():%b %-d} → {dts.max():%b %-d}" + (f"; missing columns {miss}" if miss else "") + (f"; outlook stops at {dts.max():%b %-d}" if dts.max() < b else ""))
lp = [f"{RUN}/inputs/loop_returns.csv", f"{RUN}/inputs/loop_returns.xlsx"]
L = None
if os.path.exists(lp[0]): L = pd.read_csv(lp[0])
elif os.path.exists(lp[1]): L = pd.read_excel(lp[1])
elif os.path.exists(f"{RUN}/inputs/forecast.xlsx") and "Loop Returns data (all time)" in pd.ExcelFile(f"{RUN}/inputs/forecast.xlsx").sheet_names:
    L = pd.read_excel(f"{RUN}/inputs/forecast.xlsx", "Loop Returns data (all time)")
if L is None: res("Loop returns export", False, "missing (inputs/loop_returns.csv or the 'Loop Returns data (all time)' tab)")
else:
    miss = [c for c in ["Return ID", "Order Name", "Return Submitted Date", "Return Processed Date", "Exchange Order Name", "Refund", "Exchange Item Total"] if c not in L.columns]
    sd = pd.to_datetime(L.get("Return Submitted Date"), errors="coerce")
    res("Loop returns export", not miss and sd.min() <= W["Same 4 weeks last year"][0] and sd.max() >= WK1,
        (f"missing columns {miss}; " if miss else "") + f"submitted {sd.min():%b %-d, %Y} → {sd.max():%b %-d, %Y}")
rp = f"{RUN}/inputs/dc_received.csv"
if os.path.exists(rp):
    rc = pd.read_csv(rp); cols = set(rc.columns)
    res("DC received dates", ({"Return ID", "Order Name"} & cols) and ("Received Date" in cols), f"{len(rc):,} rows", required=False)
else:
    res("DC received dates", False, "not provided; at-DC aging falls back to days since submitted (slide 07 shows INPUT MISSING)", required=False)
print("\nPREFLIGHT:", "PASS" if ok else "FAIL (ask the user for the items marked FAIL; do not pull data or build)")
sys.exit(0 if ok else 1)
