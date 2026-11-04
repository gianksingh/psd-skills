#!/usr/bin/env python3
"""Ecom Ops Weekly Flash: compute every number in the deck.

Usage:  python3 -I compute.py <run_dir> <week_start YYYY-MM-DD>

Reads   <run_dir>/inputs/{gorgias_cy.csv, gorgias_ly.csv, retently.csv, forecast.xlsx[, loop_returns.(csv|xlsx)]}
        <run_dir>/data/raw_<week_start>.json      (connector pulls, schema: references/raw_schema_example.json)
        <run_dir>/data/nps_joined.pkl             (from nps_join.py)
Writes  <run_dir>/data/metrics_<week_start>.json
Fails closed: a missing input or raw key stops the run with a message naming it.
"""
import json, sys, os
from datetime import timedelta
import numpy as np, pandas as pd

RUN, WS = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))
def die(msg): sys.exit(f"COMPUTE FAILED: {msg}")
def need(path):
    if not os.path.exists(path): die(f"missing input {path}")
    return path

WK0 = pd.Timestamp(WS); WK1 = WK0 + timedelta(days=6); PW0 = WK0 - timedelta(days=7)
LY = lambda d: d - timedelta(days=364)                       # 52 weeks back, same weekday
W4 = (WK0 - timedelta(days=21), WK1)                         # last 4 weeks incl. this week
OW = [WK0 - timedelta(weeks=i) for i in range(3, -1, -1)]    # the 4 week starts
raw = json.load(open(need(f"{RUN}/data/raw_{WS}.json")))
for k in ["orders_weekly_cy", "orders_weekly_ly", "orders_daily_week", "tickets_weekly_polar", "fulfillment_weekly",
          "fulfillment_by_service_week", "fulfilled_total_week", "shipping_chosen_week", "unfulfilled_open", "loop_open_stage",
          "loop_reason_amount_4wk", "loop_cohort_return_rate", "loop_top_products"]:
    if k not in raw: die(f"raw_{WS}.json is missing key '{k}'")
M = {"week_start": WS, "week_end": str(WK1.date()), "issues": [], "missing": []}
def r1(x, n=1):
    try:
        return None if x is None or np.isnan(float(x)) else round(float(x), n)
    except TypeError:
        return None
def nps(s):
    s = pd.Series(s).dropna()
    return None if not len(s) else round(100 * ((s >= 9).mean() - (s <= 6).mean()))
key = lambda d: str(d.date())

# ------------------------------------------------------------------ forecast (Q4 Staffing Forecast, Daily Forecast tab)
X = pd.ExcelFile(need(f"{RUN}/inputs/forecast.xlsx"))
F = pd.read_excel(X, CFG["forecast"]["tab"], header=CFG["forecast"]["header_row"])
F = F[pd.to_datetime(F["Date"], errors="coerce").notna()].copy(); F["Date"] = pd.to_datetime(F["Date"])
for c in ["Web orders", "TikTok orders", "Web tickets", "TikTok tickets"]: F[c] = pd.to_numeric(F[c], errors="coerce")
F["wk"] = F.Date.dt.to_period("W-SUN").dt.start_time
FW = F.groupby("wk")[["Web orders", "TikTok orders", "Web tickets", "TikTok tickets"]].sum(); FW["days"] = F.groupby("wk").size()
if WK0 not in FW.index: die(f"forecast has no rows for week {WS}")

# ------------------------------------------------------------------ orders (Polar, custom_5794)
OC = {pd.Timestamp(k): v for k, v in raw["orders_weekly_cy"].items()}
OL = {pd.Timestamp(k): v for k, v in raw["orders_weekly_ly"].items()}
for w in OW:
    if w not in OC: die(f"orders_weekly_cy missing week {key(w)}")
    if LY(w) not in OL: die(f"orders_weekly_ly missing week {key(LY(w))}")
fw = FW.loc[WK0]
o = M["orders"] = {"web": OC[WK0]["web"], "tts": OC[WK0]["tts"], "web_f": int(fw["Web orders"]), "tts_f": int(fw["TikTok orders"]),
                   "ly_web": OL[LY(WK0)]["web"], "ly_tts": OL[LY(WK0)]["tts"], "pw_web": OC[PW0]["web"], "pw_tts": OC[PW0]["tts"]}
o["total"], o["total_f"] = o["web"] + o["tts"], o["web_f"] + o["tts_f"]
for k in ["web", "tts", "total"]: o[k + "_var"] = r1(100 * (o[k] / o[k + "_f"] - 1))
o["web_yoy"] = r1(100 * (o["web"] / o["ly_web"] - 1)); o["tts_yoy"] = r1(100 * (o["tts"] / o["ly_tts"] - 1))
day = raw["orders_daily_week"]; fd = F[(F.Date >= WK0) & (F.Date <= WK1)].set_index("Date")
o["daily"] = [{"date": d, "web": v["web"], "tts": v["tts"], "web_f": int(fd.loc[d, "Web orders"]), "tts_f": int(fd.loc[d, "TikTok orders"])} for d, v in sorted(day.items())]
peak = max(o["daily"], key=lambda x: x["web_f"])   # the day the plan expected most (usually a promo day)
o["peak_day"] = peak
M["web_var_series"] = [r1(100 * (OC[w]["web"] / FW.loc[w, "Web orders"] - 1), 0) for w in OW]
M["tts_var_series"] = [r1(100 * (OC[w]["tts"] / FW.loc[w, "TikTok orders"] - 1), 0) for w in OW]
M["orders_hist"] = [{"wk": key(w), "orders": OC[w]["web"] + OC[w]["tts"], "web": OC[w]["web"], "tts": OC[w]["tts"],
                     "orders_f": int(FW.loc[w, "Web orders"] + FW.loc[w, "TikTok orders"]) if w in FW.index and FW.loc[w, "days"] == 7 else None} for w in OW]

# ------------------------------------------------------------------ ticket volumes (Polar Gorgias connector: full Mon-Sun)
TP = raw["tickets_weekly_polar"]; tpc = {pd.Timestamp(k): v for k, v in TP["cy"].items()}; tpl = {pd.Timestamp(k): v for k, v in TP["ly"].items()}
for w in OW:
    if w not in tpc: die(f"tickets_weekly_polar.cy missing week {key(w)}")
tk = M["tix_week"] = {"web": tpc[WK0][0], "tts": tpc[WK0][1], "web_f": round(fw["Web tickets"]), "tts_f": round(fw["TikTok tickets"]),
                      "pw_web": tpc[PW0][0], "pw_tts": tpc[PW0][1], "ly_web": tpl[LY(WK0)][0], "ly_tts": tpl[LY(WK0)][1]}
tk["web_var"] = r1(100 * (tk["web"] / tk["web_f"] - 1), 0); tk["tts_var"] = r1(100 * (tk["tts"] / tk["tts_f"] - 1), 0)
tk["all"], tk["all_f"] = tk["web"] + tk["tts"], tk["web_f"] + tk["tts_f"]; tk["all_var"] = r1(100 * (tk["all"] / tk["all_f"] - 1), 0)
lyw = OL[LY(WK0)]
M["ocr"] = {"web": r1(100 * tk["web"] / OC[WK0]["web"]), "tts": r1(100 * tk["tts"] / OC[WK0]["tts"]),
            "web_ly": r1(100 * tk["ly_web"] / lyw["web"]), "tts_ly": r1(100 * tk["ly_tts"] / lyw["tts"]),
            "web_pw": r1(100 * tk["pw_web"] / OC[PW0]["web"]), "tts_pw": r1(100 * tk["pw_tts"] / OC[PW0]["tts"])}
M["ocr_web_series"] = [r1(100 * tpc[w][0] / OC[w]["web"]) for w in OW]
M["ocr_tts_series"] = [r1(100 * tpc[w][1] / OC[w]["tts"]) for w in OW]
M["tix_web_var_series"] = [r1(100 * (tpc[w][0] / FW.loc[w, "Web tickets"] - 1), 0) for w in OW]
M["tix_tts_var_series"] = [r1(100 * (tpc[w][1] / FW.loc[w, "TikTok tickets"] - 1), 0) for w in OW]
M["tickets_weekly"] = [{"wk": key(w), "web": tpc[w][0], "tts": tpc[w][1], "web_f": round(FW.loc[w, "Web tickets"]), "tts_f": round(FW.loc[w, "TikTok tickets"])} for w in OW]

# ------------------------------------------------------------------ outlook (next 4 weeks)
r2 = [PW0, WK0]
ratio_web = sum(OC[w]["web"] for w in r2) / sum(FW.loc[w, "Web orders"] for w in r2)
ratio_tts = sum(OC[w]["tts"] for w in r2) / sum(FW.loc[w, "TikTok orders"] for w in r2)
ratio_tix = sum(sum(tpc[w]) for w in OW) / sum(FW.loc[w, "Web tickets"] + FW.loc[w, "TikTok tickets"] for w in OW)
M["outlook"] = []
for i in range(1, 5):
    w = WK0 + timedelta(weeks=i)
    if w not in FW.index: M["issues"].append(f"forecast has no rows for {key(w)}; outlook stops there"); break
    f = FW.loc[w]
    M["outlook"].append({"wk": key(w), "orders_f": int(f["Web orders"] + f["TikTok orders"]), "orders_p": int(f["Web orders"] * ratio_web + f["TikTok orders"] * ratio_tts),
                         "tix_f": int(f["Web tickets"] + f["TikTok tickets"]), "tix_p": int((f["Web tickets"] + f["TikTok tickets"]) * ratio_tix),
                         "ly_orders": (OL[LY(w)]["web"] + OL[LY(w)]["tts"]) if LY(w) in OL else None, "ly_tix": sum(tpl[LY(w)]) if LY(w) in tpl else None})
M["ratio"] = {"web": r1(100 * ratio_web), "tts": r1(100 * ratio_tts), "tix": r1(100 * ratio_tix)}

# ------------------------------------------------------------------ Gorgias ticket exports (SLA, AI split, reasons)
RS = CFG["gorgias"]["reason_map"]
def load_g(p):
    g = pd.read_csv(need(p), low_memory=False)
    g["c"] = pd.to_datetime(g["Creation date"], format=CFG["gorgias"]["date_format"])
    g["closed"] = pd.to_datetime(g["Closed date"], format=CFG["gorgias"]["date_format"], errors="coerce")
    g["ch"] = np.where(g.Channel == "tiktok-shop", "tts", "web")
    g["reason"] = g["Ticket Field: Ticket Reason"].fillna(""); g["tags"] = g.Tags.fillna("")
    g["frt"] = pd.to_numeric(g["First response time (s)"], errors="coerce"); g["res"] = pd.to_numeric(g["Resolution time (s)"], errors="coerce")
    out = g["Ticket Field: AI Agent Outcome"].fillna("")
    g["handler"] = np.select([out.str.startswith("Close"), out.str.startswith("Handover")], ["AI resolved", "AI then human"], "Human only")
    g["noise"] = g.reason.str.contains(RS["noise_reason"], case=False) | g.tags.str.contains(RS["noise_tags"])
    def dcat(r):
        r = r.upper()
        for cat, pat in RS["delivery"]:
            if any(p in r for p in pat): return cat
        return None
    g["dcat"] = g.reason.map(dcat)
    return g
G = load_g(f"{RUN}/inputs/gorgias_cy.csv"); GL = load_g(f"{RUN}/inputs/gorgias_ly.csv")
GOR_END = min(G.c.max(), WK1 + timedelta(hours=23, minutes=59))
if G.c.max() < WK1: M["missing"].append(f"Gorgias export ends {G.c.max():%b %-d}; SLA and handling cover Mon–{GOR_END:%a}")
if G.c.min() > W4[0]: M["missing"].append(f"Gorgias export starts {G.c.min():%b %-d}; needs {W4[0]:%b %-d}")
BH0, BH1 = CFG["sla"]["business_hours"]
def bh_elapsed(start, secs):
    if pd.isna(start) or pd.isna(secs): return np.nan
    end = start + timedelta(seconds=float(secs)); tot = 0.0; d = start.normalize()
    while d <= end.normalize():
        if d.weekday() < 5:
            a = max(start, d + timedelta(hours=BH0)); b = min(end, d + timedelta(hours=BH1))
            if b > a: tot += (b - a).total_seconds()
        d += timedelta(days=1)
    return tot / 3600
def sla_frame(g, asof):
    s = g[(~g.noise) & (g["Created by an agent"] != True) & (~g.Channel.isin(CFG["sla"]["exclude_channels"]))].copy()
    s["lim"] = np.where(s.Channel == "sms", CFG["sla"]["sms_hours"], CFG["sla"]["ticket_hours"])
    s["frt_bh"] = [bh_elapsed(a, b) for a, b in zip(s.c, s.frt)]
    s["open_wait"] = [bh_elapsed(a, (asof - a).total_seconds()) if pd.isna(f) and pd.isna(cl) else np.nan for a, f, cl in zip(s.c, s.frt, s.closed)]
    s = s[s.frt.notna() | s.open_wait.notna()]
    s["met"] = np.where(s.frt.notna(), s.frt_bh <= s.lim, s.open_wait <= s.lim)
    return s
def cs_block(a, b):
    w = G[(G.c >= a) & (G.c <= b)]; s = sla_frame(w, GOR_END); out = {}
    for ch, sub in [("all", w), ("web", w[w.ch == "web"]), ("tts", w[w.ch == "tts"])]:
        ss = s if ch == "all" else s[s.ch == ch]; hum = ss[ss.handler == "Human only"]
        out[ch] = {"tickets": int(len(sub)), "noise": int(sub.noise.sum()), "sla": r1(100 * ss.met.mean()), "sla_n": int(len(ss)),
                   "sla_human": r1(100 * hum.met.mean()) if len(hum) else None, "human_n": int(len(hum)),
                   "frt_human_bh": r1(hum.frt_bh.median()) if len(hum) else None, "res_med_h": r1(sub.res.median() / 3600),
                   "ai_res_share": r1(100 * (sub.handler == "AI resolved").mean())}
    return out
span = GOR_END - WK0
M["cs_week"] = cs_block(WK0, GOR_END); M["cs_prior"] = cs_block(PW0, PW0 + span)
M["cs_days"] = f"Mon–{GOR_END:%a}"
M["sla_human_series"] = [r1(100 * (lambda h: h.met.mean())(sla_frame(G[(G.c >= w) & (G.c <= min(w + timedelta(days=6, hours=23, minutes=59), GOR_END))], GOR_END).query("handler == 'Human only'"))) for w in OW]

# CSAT (Retently ticket-solved survey, joined to Gorgias on ticket id)
R = pd.read_csv(need(f"{RUN}/inputs/retently.csv"), low_memory=False)
R["dt"] = pd.to_datetime(R["Response date (ISO)"]).dt.tz_convert(CFG["timezone"]).dt.tz_localize(None)
R["wk"] = R.dt.dt.to_period("W-SUN").dt.start_time
CS = R[R.Campaign == CFG["retently"]["csat_campaign"]].copy(); CS["tid"] = pd.to_numeric(CS.ticket_id, errors="coerce")
CS = CS.merge(G[["Ticket id", "handler"]].rename(columns={"Ticket id": "tid"}), on="tid", how="left"); CS["pos"] = CS["Main rating"] >= 4
cs4 = CS[(CS.dt >= W4[0]) & (CS.dt < W4[1] + timedelta(days=1))]
wk_all = G[(G.c >= WK0) & (G.c <= GOR_END)]
M["ai"] = [{"h": h, "share": r1(100 * (wk_all.handler == h).mean()), "n": int((wk_all.handler == h).sum()),
            "res_med_h": r1(wk_all[wk_all.handler == h].res.median() / 3600),
            "csat": r1(100 * cs4[cs4.handler == h].pos.mean(), 0) if (cs4.handler == h).any() else None, "csat_n": int((cs4.handler == h).sum())}
           for h in ["AI resolved", "AI then human", "Human only"]]
M["csat_match"] = r1(100 * cs4.handler.notna().mean(), 0)
cw_ = lambda a, b: CS[(CS.dt >= a) & (CS.dt < b + timedelta(days=1))]
M["csat_week"] = {"cur": r1(100 * cw_(WK0, WK1).pos.mean(), 0), "cur_n": int(len(cw_(WK0, WK1))),
                  "pw": r1(100 * cw_(PW0, PW0 + timedelta(days=6)).pos.mean(), 0), "pw_n": int(len(cw_(PW0, PW0 + timedelta(days=6))))}

# ------------------------------------------------------------------ delivery contacts as % of orders (last 4 weeks vs same 4 weeks LY)
g4 = G[(G.c >= W4[0]) & (G.c <= GOR_END)]; gl4 = GL[(GL.c >= LY(W4[0])) & (GL.c < LY(W4[1]) + timedelta(days=1))]
if len(gl4) == 0: die("gorgias_ly.csv has no tickets in the same 4 weeks last year")
ord4 = sum(OC[w]["web"] + OC[w]["tts"] for w in OW); ordl4 = sum(OL[LY(w)]["web"] + OL[LY(w)]["tts"] for w in OW)
M["orders_4w"] = {"cy": ord4, "ly": ordl4, "web_cy": sum(OC[w]["web"] for w in OW), "web_ly": sum(OL[LY(w)]["web"] for w in OW)}
M["deliv"] = []
for cat, _ in RS["delivery"]:
    a, b = int((g4.dcat == cat).sum()), int((gl4.dcat == cat).sum())
    M["deliv"].append({"cat": cat, "cy": a, "ly": b, "cy_r": r1(100 * a / ord4, 2), "ly_r": r1(100 * b / ordl4, 2), "chg": r1(100 * ((a / ord4) / (b / ordl4) - 1), 0) if b else None})
d = g4[g4.dcat == "Delivered, not received"].copy()
d["disp"] = np.select([d.tags.str.contains("Reshipment"), d.reason.str.startswith("ORDER PROTECTION"), d.closed.isna()],
                      ["Reshipped by CS", "Order Protection claim", "Still open"], "Closed, outcome not recorded")
M["dnr_disp"] = d.disp.value_counts().to_dict(); M["dnr_n"] = int(len(d))
if G["Ticket Field: Resolution"].notna().sum() == 0: M["issues"].append("Gorgias Resolution field is empty on every ticket; delivered-not-received outcomes cannot be recorded")
M["deliv_weekly"] = []
for w in OW:
    sub = G[(G.c >= w) & (G.c < w + timedelta(days=7))]; orders = OC[w]["web"] + OC[w]["tts"]
    acc = ((sub.dcat == "Missing items") | (sub.dcat == "Wrong item / size")).sum()
    M["deliv_weekly"].append({"wk": key(w), "dnr_r": r1(100 * (sub.dcat == "Delivered, not received").sum() / orders, 2),
                              "wismo_r": r1(100 * (sub.dcat == "Where is my order").sum() / orders, 2), "acc_r": r1(100 * acc / orders, 2)})
acc_ = lambda g: ((g.dcat == "Missing items") | (g.dcat == "Wrong item / size")).sum()
M["acc_r"] = {"cy": r1(100 * acc_(g4) / ord4, 2), "ly": r1(100 * acc_(gl4) / ordl4, 2)}
# like-for-like where-is-my-order: web only, scaled to the share of web tickets that carry a reason
def wis_web(g):
    w = g[g.ch == "web"]; return int((w.dcat == "Where is my order").sum()), (w.reason != "").mean()
nc, labc = wis_web(g4); nl, labl = wis_web(gl4)
wl = M["wismo_like"] = {"cy_r": r1(100 * nc / labc / M["orders_4w"]["web_cy"], 2), "ly_r": r1(100 * nl / labl / M["orders_4w"]["web_ly"], 2),
                        "lab_cy": r1(100 * labc), "lab_ly": r1(100 * labl),
                        "tts_cy": int(((g4.ch == "tts") & (g4.dcat == "Where is my order")).sum()), "tts_ly": int(((gl4.ch == "tts") & (gl4.dcat == "Where is my order")).sum()),
                        "tts_tix_cy": int((g4.ch == "tts").sum()), "tts_tix_ly": int((gl4.ch == "tts").sum()),
                        "unl_all_cy": r1(100 * (g4.reason == "").mean()), "unl_all_ly": r1(100 * (gl4.reason == "").mean())}
wl["chg"] = r1(100 * (wl["cy_r"] / wl["ly_r"] - 1), 0)
wis_all = [x for x in M["deliv"] if x["cat"] == "Where is my order"][0]
wl["overstated"] = bool(wis_all["chg"] is not None and wis_all["chg"] - wl["chg"] >= 25)

# ------------------------------------------------------------------ voice of the customer (Retently)
wks = [WK0 - timedelta(weeks=i) for i in range(12, -1, -1)]
NP = R[R.Metric == "NPS"]; DS = R[R.Campaign == CFG["retently"]["delivery_campaign"]]
csat_fn = lambda s: None if not len(s) else round(100 * (s >= 4).mean())
dsat_fn = lambda s: None if not len(s) else round(100 * (s == 3).mean())
def roll(df, fn, end, n=4):
    sub = df[(df.dt >= end - timedelta(days=7 * n - 1)) & (df.dt < end + timedelta(days=1))]
    return fn(sub["Main rating"]), int(len(sub))
M["voc_weeks"] = [key(w) for w in wks]
M["nps_r4"] = [roll(NP, nps, w + timedelta(days=6))[0] for w in wks]
M["csat_r4"] = [roll(CS, csat_fn, w + timedelta(days=6))[0] for w in wks]
M["dsat_r4"] = [roll(DS, dsat_fn, w + timedelta(days=6))[0] for w in wks]
nw = NP[NP.wk == WK0]["Main rating"]
M["voc_now"] = {"nps": roll(NP, nps, WK1), "nps_ly": roll(NP, nps, LY(WK1)), "nps_wk": (nps(nw), int(len(nw))),
                "csat": roll(CS, csat_fn, WK1), "csat_ly": roll(CS, csat_fn, LY(WK1)), "dsat": roll(DS, dsat_fn, WK1), "dsat_ly": roll(DS, dsat_fn, LY(WK1)),
                "nps_ytd": nps(NP[(NP.dt >= f"{WK0.year}-01-01") & (NP.dt < W4[0])]["Main rating"])}
# NPS cuts from responses joined to Shopify orders (nps_join.py)
J = pd.read_pickle(need(f"{RUN}/data/nps_joined.pkl"))
J["online"] = J.src == "web"; J["repeat"] = J.norders > 1; J["slow"] = J.d_tot > 7
first = G.groupby(G["Customer email"].str.lower()).c.min(); J["first_contact"] = J.em.map(first)
J["cs"] = J.first_contact.notna() & (J.first_contact >= pd.to_datetime(J.created)) & (J.first_contact <= J.dt)
B, Cu = J.per == "base", J.per == "cur"
def cut(mask): return [nps(J[mask & B]["Main rating"]), int((mask & B).sum()), nps(J[mask & Cu]["Main rating"]), int((mask & Cu).sum())]
M["nps_cuts"] = {"App orders (Tapcart)": cut(~J.online), "Online store orders": cut(J.online),
                 "Online store, first-time": cut(J.online & ~J.repeat), "Online store, repeat": cut(J.online & J.repeat),
                 "Delivered within 7 days": cut(~J.slow), "Took over 7 days": cut(J.slow),
                 "Contacted CS about the order": [None, 0] + cut(J.cs)[2:], "No CS contact": [None, 0] + cut(~J.cs)[2:]}
if G.c.min() > J[B].dt.min(): M["issues"].append("CS-contact NPS cut has no prior-period figure: the Gorgias export does not reach back to the NPS base window")
M["nps_join"] = {"match": r1(100 * J.matched.mean(), 0), "dtot_base": r1(J[B].d_tot.median()), "dtot_cur": r1(J[Cu].d_tot.median()),
                 "slow_base": r1(100 * J[B].slow.mean(), 0), "slow_cur": r1(100 * J[Cu].slow.mean(), 0),
                 "det_cur": int((Cu & (J["Main rating"] <= 6)).sum()), "det_cur_web": int((Cu & (J["Main rating"] <= 6) & J.online).sum())}

# ------------------------------------------------------------------ returns (Loop export)
lp = f"{RUN}/inputs/loop_returns.csv"
if os.path.exists(lp): L = pd.read_csv(lp)
elif os.path.exists(f"{RUN}/inputs/loop_returns.xlsx"): L = pd.read_excel(f"{RUN}/inputs/loop_returns.xlsx")
else: L = pd.read_excel(X, CFG["loop_tab_fallback"])
for c in ["Return Submitted Date", "Return Processed Date"]: L[c] = pd.to_datetime(L[c])
L["sub"], L["proc"] = L["Return Submitted Date"], L["Return Processed Date"]
L["days"] = (L.proc - L["sub"]).dt.total_seconds() / 86400; L["exch"] = L["Exchange Order Name"].notna()
def ret_block(a, b):
    s = L[(L["sub"] >= a) & (L["sub"] < b + timedelta(days=1))]; p = L[(L.proc >= a) & (L.proc < b + timedelta(days=1))]
    return {"submitted": int(len(s)), "processed": int(len(p)), "days_med": r1(p.days.median()), "exch_share": r1(100 * s.exch.mean(), 0),
            "refund_usd": round(float(s.Refund.sum())), "exch_usd": round(float(s["Exchange Item Total"].sum()))}
M["ret_4w"] = ret_block(*W4); M["ret_4w_ly"] = ret_block(LY(W4[0]), LY(W4[1]))
M["ret_weekly"] = [{"wk": key(w), **{k: v for k, v in ret_block(w, w + timedelta(days=6)).items() if k in ("submitted", "processed", "days_med")}} for w in OW]
asof = pd.Timestamp(raw["loop_open_stage"]["asof"])
op = L[L.proc.isna() & (L["sub"] >= asof - timedelta(days=30))].copy(); op["age"] = (asof - op["sub"]).dt.days
M["ret_age"] = {"0-7 days": int((op.age <= 7).sum()), "8-14 days": int(op.age.between(8, 14).sum()), "15-22 days": int(op.age.between(15, 22).sum()), "23-30 days": int(op.age.between(23, 30).sum())}

# ------------------------------------------------------------------ fulfillment (ShopifyQL)
fc = raw["fulfillment_weekly"]["cy"]; fl = raw["fulfillment_weekly"]["ly"]
if WS not in fc or key(LY(WK0)) not in fl: die("fulfillment_weekly needs this week (cy) and the same week last year (ly)")
M["ful"] = {"hrs": fc[WS][1], "hrs_ly": fl[key(LY(WK0))][1], "days": fc[WS][2], "days_ly": fl[key(LY(WK0))][2], "fulfilled": fc[WS][0],
            "hrs_series": [fc[k][1] for k in sorted(fc)][-4:], "days_series": [fc[k][2] for k in sorted(fc)][-4:]}
M["unfulfilled_late"] = raw["unfulfilled_open"]["count"]

json.dump(M, open(f"{RUN}/data/metrics_{WS}.json", "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
print(f"wrote data/metrics_{WS}.json · missing: {M['missing'] or 'none'} · issues: {len(M['issues'])}")
