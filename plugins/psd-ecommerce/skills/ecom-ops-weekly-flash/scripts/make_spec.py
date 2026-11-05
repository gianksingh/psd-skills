#!/usr/bin/env python3
"""Ecom Ops Weekly Flash: build the deck spec from metrics + the run's observations.

Usage:  python3 -I make_spec.py <run_dir> <week_start>
Reads   data/metrics_<week>.json, data/raw_<week>.json, data/observations_<week>.json, scripts/config.json
Writes  data/deck_<week>.json and data/issues_<week>.md
Vocabulary: "order contact rate" = tickets / orders (%). Delivery reasons are rates = tickets with that reason / orders (%).
Defaults: every headline has an auto default; observations may override `headlines`, `callouts`, and must supply
`exec_items` (3) and `notes`. Speaker notes are bulleted facts + interpretation for the presenter to use or drop.
"""
import json, sys, os
from datetime import timedelta
import pandas as pd
RUN, WS = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json"))); TH = CFG["thresholds"]
M = json.load(open(f"{RUN}/data/metrics_{WS}.json")); RAW = json.load(open(f"{RUN}/data/raw_{WS}.json"))
op = f"{RUN}/data/observations_{WS}.json"
OBS = json.load(open(op)) if os.path.exists(op) else {}
WK0 = pd.Timestamp(WS); WK1 = WK0 + timedelta(days=6); W4a = WK0 - timedelta(days=21)
rng = lambda a, b: f"{a:%b %-d}–{b:%-d}, {b:%Y}" if a.month == b.month else f"{a:%b %-d}–{b:%b %-d}, {b:%Y}"
WEEK = rng(WK0, WK1); W4 = rng(W4a, WK1); LYW4 = rng(W4a - timedelta(days=364), WK1 - timedelta(days=364))
f0 = lambda v: f"{v:,.0f}"; pct = lambda v: f"{v:+.0f}%"; p2 = lambda v: f"{v:.2f}%"
lab = lambda w: f"{int(w[5:7])}/{int(w[8:])}"
def st(rule, v):
    kind, a, r = TH[rule]
    if v is None: return "na"
    return ("red" if v >= r else "amber" if v >= a else "green") if kind == "hi" else ("red" if v <= r else "amber" if v <= a else "green")
FILL = {"red": ("B3261E", "FFFFFF"), "amber": ("E8A33D", "1A1A1A"), "green": ("1B7A4B", "FFFFFF"), "watch": ("D9D7CF", "1A1A1A")}

O, CW, CP, TK, OCR, V, ful = M["orders"], M["cs_week"], M["cs_prior"], M["tix_week"], M["ocr"], M["voc_now"], M["ful"]
dl = {d["cat"]: d for d in M["deliv"]}; wis, dnr = dl["Where is my order"], dl["Delivered, not received"]
WL, acc = M["wismo_like"], M["acc_r"]; dnr_wk = M["deliv_weekly"][-1]["dnr_r"]
ol, hist = M["outlook"], M["orders_hist"]
CD = M["cs_days"]
foot = lambda src: f"{src} · Week {WEEK}"
ratio = lambda a, b: None if not b else a / b - 1

rows = [
 dict(metric="Web orders vs forecast", value=pct(O["web_var"]), cmp=f"{f0(O['web'])} vs {f0(O['web_f'])} planned", rule="15%+ under plan", status=st("orders_vs_plan_pct", O["web_var"]), trend=M["web_var_series"], slide="03"),
 dict(metric="TikTok Shop orders vs forecast", value=pct(O["tts_var"]), cmp=f"{f0(O['tts'])} vs {f0(O['tts_f'])} planned", rule="15%+ under plan", status=st("orders_vs_plan_pct", O["tts_var"]), trend=M["tts_var_series"], slide="03"),
 dict(metric="Web tickets vs forecast", value=pct(TK["web_var"]), cmp=f"{f0(TK['web'])} vs {f0(TK['web_f'])} planned", rule="20%+ over plan", status=st("tickets_vs_plan_pct", TK["web_var"]), trend=M["tix_web_var_series"], slide="03"),
 dict(metric="TikTok Shop tickets vs forecast", value=pct(TK["tts_var"]), cmp=f"{f0(TK['tts'])} vs {f0(TK['tts_f'])} planned", rule="20%+ over plan", status=st("tickets_vs_plan_pct", TK["tts_var"]), trend=M["tix_tts_var_series"], slide="03"),
 dict(metric="Web order contact rate", value=f"{OCR['web']}%", cmp=f"Same week LY: {OCR['web_ly']}%", rule="25%+ above LY", status=st("order_contact_rate_vs_ly", ratio(OCR["web"], OCR["web_ly"])), trend=M["ocr_web_series"], slide="05"),
 dict(metric="TikTok Shop order contact rate", value=f"{OCR['tts']}%", cmp=f"Same week LY: {OCR['tts_ly']}%", rule="25%+ above LY", status=st("order_contact_rate_vs_ly", ratio(OCR["tts"], OCR["tts_ly"])), trend=M["ocr_tts_series"], slide="05"),
 dict(metric="Human-handled first replies within SLA", value=f"{CW['all']['sla_human']}%", cmp=f"Last week {CP['all']['sla_human']}% ({CD})", rule="Under 90%", status=st("human_sla_pct", CW["all"]["sla_human"]), trend=M["sla_human_series"], slide="05"),
 dict(metric="Order to fulfillment (median)", value=f"{ful['hrs']} hrs", cmp=f"Same week LY: {ful['hrs_ly']} hrs", rule="Over 48 hrs", status=st("order_to_fulfill_hrs", ful["hrs"]), trend=ful["hrs_series"], slide="04"),
 dict(metric="Orders unfulfilled 2+ business days", value=f"{M['unfulfilled_late']}", cmp=f"Open as of {pd.Timestamp(RAW['unfulfilled_open']['asof']):%b %-d}", rule="Over 200", status=st("unfulfilled_2bd", M["unfulfilled_late"]), trend=[], slide="04"),
 dict(metric="Order to delivery (median)", value=f"{ful['days']} days", cmp=f"Same week LY: {ful['days_ly']} days", rule="2+ days slower than LY", status=st("order_to_delivery_days_vs_ly", ful["days"] - ful["days_ly"]), trend=ful["days_series"], slide="04"),
 dict(metric="Where-is-my-order rate (web, like-for-like)", value=p2(WL["cy_r"]), cmp=f"Same 4 wks LY: {p2(WL['ly_r'])}", rule="25%+ above LY", status=st("delivery_rate_vs_ly", ratio(WL["cy_r"], WL["ly_r"])), trend=[x["wismo_r"] for x in M["deliv_weekly"]], slide="04"),
 dict(metric="Delivered-not-received rate", value=p2(dnr_wk), cmp=f"Same 4 wks LY: {p2(dnr['ly_r'])}", rule="25%+ above LY", status=st("delivery_rate_vs_ly", ratio(dnr_wk, dnr["ly_r"])), trend=[x["dnr_r"] for x in M["deliv_weekly"]], slide="04"),
 dict(metric="Missing + wrong-item rate", value=p2(acc["cy"]), cmp=f"Same 4 wks LY: {p2(acc['ly'])}", rule="25%+ above LY", status=st("delivery_rate_vs_ly", ratio(acc["cy"], acc["ly"])), trend=[x["acc_r"] for x in M["deliv_weekly"]], slide="04"),
 dict(metric="NPS, rolling 4 weeks", value=f"{V['nps'][0]}", cmp=f"Same 4 wks LY: {V['nps_ly'][0]}", rule="10+ pts below LY", status=st("nps_pts_vs_ly", V["nps"][0] - V["nps_ly"][0]), trend=M["nps_r4"][-4:], slide="06"),
 dict(metric="CSAT, rolling 4 weeks", value=f"{V['csat'][0]}%", cmp=f"Same 4 wks LY: {V['csat_ly'][0]}%", rule="10+ pts below LY", status=st("csat_pts_vs_ly", V["csat"][0] - V["csat_ly"][0]), trend=M["csat_r4"][-4:], slide="06"),
 dict(metric="Returns: median days to process", value=f"{M['ret_4w']['days_med']}", cmp=f"Same 4 wks LY: {M['ret_4w_ly']['days_med']} (from submission)", rule="Over 10 days", status=st("returns_days_to_process", M["ret_4w"]["days_med"]), trend=[x["days_med"] for x in M["ret_weekly"]], slide="07"),
 dict(metric=f"Returns at the DC {M['at_dc']['oldest_label']} unprocessed", value=f"{M['at_dc']['oldest_n']}", cmp=f"{M['at_dc']['oldest_flagged']} flagged in Loop; {M['at_dc']['n']} at DC in total", rule="Over 25", status=st("returns_at_dc_oldest", M["at_dc"]["oldest_n"]), trend=[], slide="07"),
]
nred, namb, ngrn = (sum(r["status"] == s for r in rows) for s in ("red", "amber", "green"))
NC = M["nps_cuts"]; on_cut, app_cut = NC["Online store orders"], NC["App orders (Tapcart)"]
H = OBS.get("headlines", {}); CO = OBS.get("callouts", {})
pk = O["peak_day"]

slides = []
# 1 executive summary: three things to know (written by the run in observations)
exec_items = OBS.get("exec_items") or [
  dict(head=f"Tickets ran {TK['all_var']:+.0f}% vs plan while orders ran {O['total_var']:+.0f}%",
       body=f"Web order contact rate {OCR['web']}% (same week LY {OCR['web_ly']}%); TikTok Shop {OCR['tts']}% ({OCR['tts_ly']}%).", slide="SLIDES 03, 05"),
  dict(head=f"Web where-is-my-order rate {p2(WL['cy_r'])} vs {p2(WL['ly_r'])} LY", body=f"Median order to fulfillment {ful['hrs']} hrs; order to delivery {ful['days']} days vs {ful['days_ly']}.", slide="SLIDE 04"),
  dict(head=f"NPS {V['nps'][0]} over 4 weeks vs {V['nps_ly'][0]} LY", body=f"Online-store orders {on_cut[2]} (was {on_cut[0]}); app orders {app_cut[2]} (was {app_cut[0]}).", slide="SLIDE 06")]
slides.append(dict(type="exec", id="exec", kicker=f"WEEK OF {WEEK.upper()} · MON–SUN", title="Ecom Ops Weekly", pill="PSD WEB + TIKTOK SHOP", items=exec_items,
  strip=[dict(status="red", label=f"{nred} red"), dict(status="amber", label=f"{namb} amber"), dict(status="green", label=f"{ngrn} green")],
  missing=M["missing"] + OBS.get("missing", []), foot_left=f"Prepared {pd.Timestamp.now(tz=CFG['timezone']):%b %-d, %Y} for the weekly ops meeting · Polar, Shopify, Gorgias, Retently, Loop"))

# 2 tripwires + ops manager context box
slides.append(dict(type="tripwires", id="tripwires", sec="01", kicker="Peak tripwires", pill="VS LY + TARGETS",
  headline=H.get("tripwires", f"{nred} red, {namb} amber, {ngrn} green. Red rows set the agenda."),
  footer=foot("Polar (Shopify orders, Gorgias tickets), ShopifyQL fulfillments, Gorgias export, Retently, Loop, Q4 Staffing Forecast"),
  card=dict(kind="scorecard", title="TREND = LAST 4 WEEKS", rows=rows,
   note=f"Order contact rate = tickets ÷ orders. Delivery rates = tickets with that reason ÷ orders, {W4} vs same weeks LY (DNR row: this week). SLA rows: {CD}, first reply within {CFG['sla']['ticket_hours']} business hours (SMS {CFG['sla']['sms_hours']})."),
  notes=OBS.get("notes", {}).get("tripwires", [])))

# 3 volume, plan, outlook
LEG = [["box", "2B3FE0", "Web"], ["box", "8C97F0", "TikTok Shop"], ["dash", "2B3FE0", "Projected"], ["tick", "B3261E", "Forecast"], ["dot", "7A7A74", "Same wk LY"]]
items = [dict(label=lab(h["wk"]), value=h["orders"], fcst=h["orders_f"], display=f"{h['orders']/1000:.1f}K", parts=[h["web"], h["tts"]], hl=h is hist[-1],
              sub=pct(100 * (h["orders"] / h["orders_f"] - 1)) if h["orders_f"] else "", subc="bad" if h["orders_f"] and h["orders"] < h["orders_f"] * .9 else None) for h in hist]
items += [dict(label=lab(o["wk"]), value=o["orders_p"], fcst=o["orders_f"], ly=o["ly_orders"], proj=True, display=f"{o['orders_p']/1000:.1f}K", sub="projected") for o in ol]
titems = [dict(label=lab(t["wk"]), value=t["web"] + t["tts"], fcst=t["web_f"] + t["tts_f"], display=f0(t["web"] + t["tts"]), parts=[t["web"], t["tts"]], hl=t is M["tickets_weekly"][-1],
               sub=pct(100 * ((t["web"] + t["tts"]) / (t["web_f"] + t["tts_f"]) - 1)), subc="bad" if t["web"] + t["tts"] > (t["web_f"] + t["tts_f"]) * 1.1 else None) for t in M["tickets_weekly"]]
titems += [dict(label=lab(o["wk"]), value=o["tix_p"], fcst=o["tix_f"], ly=o["ly_tix"], proj=True, display=f0(o["tix_p"]), sub="projected") for o in ol]
last = ol[-1] if ol else None
slides.append(dict(type="finding", id="volume", sec="02", kicker="Volume, plan and outlook", pill="VS Q4 STAFFING FORECAST", jamie=True,
  headline=H.get("volume", f"Tickets ran {TK['all_var']:+.0f}% vs plan on orders {O['total_var']:+.0f}% vs plan" + (f"; at this pace the week of {lab(last['wk'])} needs ~{f0(last['tix_p'])} tickets vs {f0(last['tix_f'])} planned" if last else "")),
  callout=CO.get("volume"), footer=foot("Orders: Polar, Web = Online Store + Tapcart + Shop App + Fermat · Tickets: Gorgias via Polar · Plan: Q4 Staffing Forecast"),
  body=dict(layout="two_cards", split=0.5,
   left=dict(kind="colbars", title="ORDERS PER WEEK", items=items, split=len(hist), legendItems=LEG,
             note=f"Projection = forecast × last 2 weeks' actual-to-plan (web {M['ratio']['web']:.0f}%, TikTok Shop {M['ratio']['tts']:.0f}%). Biggest planned day ({pd.Timestamp(pk['date']):%b %-d}): {f0(pk['web'])} web orders vs {f0(pk['web_f'])} planned."),
   right=dict(kind="colbars", title="TICKETS PER WEEK", items=titems, split=len(M["tickets_weekly"]), legendItems=LEG,
              note=f"Projection = forecast × {M['ratio']['tix']/100:.2f} (last 4 weeks' actual-to-plan).")),
  notes=OBS.get("notes", {}).get("volume", [])))

# 4 fulfillment and delivery
drows = [[d["cat"], f0(d["cy"]), p2(d["cy_r"]), p2(d["ly_r"]), {"t": (f"{d['chg']:+.0f}%" if d["chg"] is not None else "n/a"), "c": "bad" if (d["chg"] or 0) >= 25 else ("good" if (d["chg"] or 0) < 0 else None), "b": (d["chg"] or 0) >= 25}] for d in M["deliv"]]
ch = RAW["shipping_chosen_week"]; cht = sum(x["orders"] for x in ch)
svc_rows = [[x["svc"], f0(x["orders"]), f"{100*x['orders']/cht:.1f}%", x.get("ships_as", ""), x.get("ship", "n/a"), x.get("deliver", "n/a")] for x in ch]
unk = sum(x["fulfilled"] for x in RAW["fulfillment_by_service_week"] if x["service"].startswith("Service not recorded")); ftot = RAW["fulfilled_total_week"]
wl_call = (f"all-channel {p2(wis['cy_r'])} vs {p2(wis['ly_r'])} overstates it. TikTok Shop WISMO went {WL['tts_ly']} to {WL['tts_cy']} as its Gorgias volume changed; "
           f"{WL['unl_all_ly']:.0f}% of LY tickets had no reason ({WL['unl_all_cy']:.0f}% now).") if WL["overstated"] else None
slides.append(dict(type="finding", id="fulfillment", sec="03", kicker="Fulfillment and delivery", pill="RATES = % OF ORDERS", jamie=True,
  headline=H.get("fulfillment", f"The DC ships in {ful['hrs']} hours; web where-is-my-order contacts {WL['chg']:+.0f}% per order vs LY ({p2(WL['cy_r'])} vs {p2(WL['ly_r'])})"),
  callout=CO.get("fulfillment", wl_call), footer=foot("ShopifyQL fulfillments · shipping method chosen: Polar · Gorgias ticket reasons incl. Order Protection claims"),
  body=dict(layout="two_cards", split=0.5,
   left=dict(kind="stack", title=f"DELIVERY CONTACTS AS A % OF ORDERS · {W4.upper()} VS LY", parts=[
      dict(kind="table", h=2.25, columns=[{"h": "Contact reason", "w": 2.8}, {"h": "Tickets", "w": 0.9, "a": "r"}, {"h": "Rate", "w": 1.0, "a": "r"}, {"h": "Rate LY", "w": 1.0, "a": "r"}, {"h": "Change", "w": 0.9, "a": "r"}], rows=drows,
           note=f"All channels. LY rates run low when LY tickets were less often labeled ({WL['unl_all_ly']:.0f}% unlabeled LY, {WL['unl_all_cy']:.0f}% now), so year-over-year changes here read high. Order Protection claim codes are added to the matching reason."),
      dict(kind="hbars", h=1, title=f"DELIVERED-NOT-RECEIVED OUTCOMES · {M['dnr_n']} TICKETS", items=[{"label": k, "value": v, "display": f"{v} ({round(100*v/max(M['dnr_n'],1))}%)", "hl": k.startswith("Closed")} for k, v in sorted(M["dnr_disp"].items(), key=lambda x: -x[1])])]),
   right=dict(kind="stack", title="THIS WEEK VS SAME WEEK LY · MEDIANS", parts=[
      dict(kind="statrow", h=0.85, big=22, items=[
         {"value": f"{ful['hrs']}h", "label": "Order to fulfilled", "sub": f"LY: {ful['hrs_ly']}h"},
         {"value": f"{ful['days']}d", "label": "Order to delivered", "sub": f"LY: {ful['days_ly']}d", "c": "bad" if ful["days"] > ful["days_ly"] else None},
         {"value": f"{M['unfulfilled_late']}", "label": "Unfulfilled 2+ bus. days", "sub": f"open, as of {pd.Timestamp(RAW['unfulfilled_open']['asof']):%b %-d}"}]),
      dict(kind="table", h=1.9, title="SHIPPING SERVICE CHOSEN · THIS WEEK", columns=[{"h": "Service", "w": 1.15}, {"h": "Orders", "w": 0.7, "a": "r"}, {"h": "Share", "w": 0.65, "a": "r"}, {"h": "Ships as", "w": 2.35}, {"h": "Ship", "w": 0.7, "a": "r"}, {"h": "Deliver", "w": 0.75, "a": "r"}], rows=svc_rows,
           note=f"Medians from fulfillments where Shopify records the service. {f0(unk)} of {f0(ftot)} fulfillments ({100*unk/ftot:.0f}%) have UPS tracking but no service in Shopify (TikTok Shop, Express on the second UPS account, international, exchanges).")])),
  notes=OBS.get("notes", {}).get("fulfillment", [])))

# 5 customer service
fpc = lambda v: "n/a" if v is None else f"{v}%"
fh = lambda v: "n/a" if v is None else (f"{v*60:.0f} min" if v < 1 else f"{v} hrs")
def cs_row(lbl, k, fmt): return [lbl] + [fmt(CW[c].get(k)) + (f"  ({fmt(CP[c].get(k))})" if CP[c].get(k) is not None else "") for c in ("all", "web", "tts")]
cw = M["csat_week"]
csrows = [
  ["Tickets created vs plan", f"{f0(TK['all'])} vs {f0(TK['all_f'])}  ({f0(TK['pw_web']+TK['pw_tts'])})", f"{f0(TK['web'])} vs {f0(TK['web_f'])}  ({f0(TK['pw_web'])})", {"t": f"{f0(TK['tts'])} vs {f0(TK['tts_f'])}  ({f0(TK['pw_tts'])})", "c": "bad" if TK["tts_var"] >= 20 else None, "b": TK["tts_var"] >= 20}],
  ["Order contact rate (same week LY)", f"{100*TK['all']/O['total']:.1f}%", f"{OCR['web']}%  ({OCR['web_ly']}%)", {"t": f"{OCR['tts']}%  ({OCR['tts_ly']}%)", "c": "bad" if OCR["tts"] > OCR["tts_ly"] * 1.25 else None, "b": True}],
  ["CSAT, ticket-solved survey", f"{cw['cur']:.0f}%  ({cw['pw']:.0f}%)", f"{cw['cur']:.0f}%  ({cw['pw']:.0f}%)  n={cw['cur_n']}", {"t": "no survey", "c": "muted"}],
  cs_row("First reply within SLA, all*", "sla", fpc), cs_row("First reply within SLA, human-only*", "sla_human", fpc),
  cs_row("Median first reply, human-only*", "frt_human_bh", fh), cs_row("Median resolution time*", "res_med_h", fh)]
airows = [[a["h"], f"{a['share']}%", f0(a["n"]), fh(a["res_med_h"]), {"t": (f"{a['csat']:.0f}%" if a["csat"] is not None else "n/a"), "c": "bad" if (a["csat"] or 100) < 45 else None}, f0(a["csat_n"])] for a in M["ai"]]
slides.append(dict(type="finding", id="cs", sec="04", kicker="Customer service", pill="VS PRIOR WEEK", jamie=True, missing=OBS.get("missing_cs", ["human reply time after AI handoff"]),
  headline=H.get("cs", f"TikTok Shop tickets ran {TK['tts_var']:+.0f}% vs plan at a {OCR['tts']}% order contact rate; CSAT {cw['cur']:.0f}% (last week {cw['pw']:.0f}%)"),
  callout=CO.get("cs"), footer=foot(f"Volumes: Gorgias via Polar (Mon–Sun) · *SLA and handling: Gorgias ticket export ({CD}) · CSAT: Retently"),
  body=dict(layout="two_cards", split=0.6,
   left=dict(kind="table", title="TOTAL, THEN WEB VS TIKTOK SHOP · (PRIOR WEEK)", columns=[{"h": "Measure", "w": 2.6}, {"h": "Total", "w": 1.7, "a": "r"}, {"h": "Web", "w": 1.8, "a": "r"}, {"h": "TikTok Shop", "w": 1.6, "a": "r"}], rows=csrows,
             note=f"*{CD} vs the same days last week. SLA: first reply within {CFG['sla']['ticket_hours']} business hours (SMS {CFG['sla']['sms_hours']}), Mon–Fri {CFG['sla']['business_hours'][0]}am–{CFG['sla']['business_hours'][1]-12}pm PT; 'all' counts AI agent replies. TikTok Shop tickets get no AI agent and no CSAT survey."),
   right=dict(kind="table", title=f"AI AGENT VS HUMAN · {CD.upper()} (CSAT: LAST 4 WKS)", columns=[{"h": "Handled by", "w": 1.5}, {"h": "Share", "w": 0.75, "a": "r"}, {"h": "Tickets", "w": 0.85, "a": "r"}, {"h": "Resolve", "w": 0.95, "a": "r"}, {"h": "CSAT", "w": 0.75, "a": "r"}, {"h": "n", "w": 0.45, "a": "r"}], rows=airows,
              note=f"CSAT = 4 or 5 of 5. {M['csat_match']:.0f}% of CSAT responses matched a ticket in the export; samples are small.")),
  notes=OBS.get("notes", {}).get("cs", [])))

# 6 voice of the customer
def seg_row(c, s):
    b, bn, cu, cn = NC[s]; chg = None if b is None else cu - b
    return [c, s, ("no data" if b is None else f"{b}  (n={bn})"), {"t": f"{cu}  (n={cn})", "b": True, "c": "bad" if cu is not None and cu < 40 else None},
            {"t": "n/a" if chg is None else f"{chg:+d}", "c": "bad" if (chg or 0) <= -15 else None}]
segs = [("Channel", "App orders (Tapcart)"), ("Channel", "Online store orders"), ("Online store", "Online store, first-time"), ("Online store", "Online store, repeat"),
        ("Delivery time", "Delivered within 7 days"), ("Delivery time", "Took over 7 days"), ("CS contact", "Contacted CS about the order"), ("CS contact", "No CS contact")]
nj = M["nps_join"]
slides.append(dict(type="finding", id="voc", sec="05", kicker="Voice of the customer", pill="ROLLING 4 WEEKS", jamie=True,
  headline=H.get("voc", f"NPS {V['nps'][0]} vs {V['nps_ly'][0]} LY; online-store orders {on_cut[2]} (was {on_cut[0]}), app orders {app_cut[2]} (was {app_cut[0]})"),
  callout=CO.get("voc"), footer=foot("Retently NPS / CSAT / delivery surveys · NPS responses joined to Shopify orders by email · CS contact: Gorgias"),
  body=dict(layout="two_cards", split=0.45,
   left=dict(kind="stack", title="13-WEEK TREND · ROLLING 4 WEEKS", parts=[
      dict(kind="lines", h=2.3, labels=[lab(w) for w in M["voc_weeks"]], every=2, min=40, max=80, grid=[40, 60, 80],
           series=[{"name": "NPS", "values": M["nps_r4"], "color": "2B3FE0", "labels": True, "dots": True},
                   {"name": "Delivery sat. %", "values": M["dsat_r4"], "color": "8A8A84"}, {"name": "CSAT %", "values": M["csat_r4"], "color": "E8A33D"}],
           note=f"This week alone: NPS {V['nps_wk'][0]} (n={V['nps_wk'][1]}). Year to date before these 4 weeks: {V['nps_ytd']}."),
      dict(kind="statrow", h=0.9, big=20, items=[{"value": f"{V['nps'][0]}", "label": "NPS", "sub": f"n={V['nps'][1]} · LY: {V['nps_ly'][0]}", "c": "bad" if V["nps"][0] < V["nps_ly"][0] - 10 else None},
                                                 {"value": f"{V['csat'][0]}%", "label": "CSAT", "sub": f"n={V['csat'][1]} · LY: {V['csat_ly'][0]}%"},
                                                 {"value": f"{V['dsat'][0]}%", "label": "Delivery sat.", "sub": f"n={V['dsat'][1]} · LY: {V['dsat_ly'][0]}%"}])]),
   right=dict(kind="table", title="WHERE THE NPS CHANGE SITS · PRIOR 4 WKS VS LAST 4 WKS", columns=[{"h": "Cut", "w": 1.15}, {"h": "Segment", "w": 2.25}, {"h": "Prior 4 wks", "w": 1.15, "a": "r"}, {"h": "Last 4 wks", "w": 1.15, "a": "r"}, {"h": "Change", "w": 0.75, "a": "r"}],
              rows=[seg_row(c, s) for c, s in segs],
              note=f"Orders over 7 days: {nj['slow_base']:.0f}% of responses before, {nj['slow_cur']:.0f}% now (median {nj['dtot_base']} vs {nj['dtot_cur']} days). {nj['det_cur_web']} of {nj['det_cur']} detractors bought on the online store. {nj['match']:.0f}% matched. Cuts under 30 responses are directional.")),
  notes=OBS.get("notes", {}).get("voc", [])))

# 7 returns pipeline
stg = RAW["loop_open_stage"]; R4, RL, AD = M["ret_4w"], M["ret_4w_ly"], M["at_dc"]
by_rcv = AD["basis"] == "received"
dproc = f"{R4['days_from_received_med']} days from receipt" if by_rcv and R4.get("days_from_received_med") is not None else f"{R4['days_med']} days median (from submission)"
slides.append(dict(type="finding", id="returns", sec="06", kicker="Returns pipeline", pill="WEB · LOOP", jamie=True,
  missing=[] if by_rcv else ["DC received dates"],
  headline=H.get("returns", f"{AD['n']} returns sit at the DC unprocessed; {AD['oldest_n']} have waited {AD['oldest_label']} since {'receipt' if by_rcv else 'submission'}, {AD['oldest_flagged']} of them flagged in Loop"),
  callout=CO.get("returns"), footer=foot(f"Loop returns export + Loop status by label stage, as of {pd.Timestamp(AD['asof']):%b %-d} · TikTok Shop returns are handled in TikTok"),
  body=dict(layout="two_cards", split=0.52,
   left=dict(kind="funnel", title=f"RETURNS BY STAGE · OPEN AS OF {pd.Timestamp(AD['asof']):%b %-d}, THEN LAST 4 WEEKS".upper(), rw=2.3, steps=[
      {"label": "Label created, not shipped", "value": stg["label_not_shipped"], "display": f0(stg["label_not_shipped"]), "rate": "Customer has not sent it yet"},
      {"label": "In transit to DC", "value": stg["in_transit"], "display": f0(stg["in_transit"]), "rate": "On the way back"},
      {"label": "Delivered to DC, not processed", "value": AD["n"], "display": f0(AD["n"]), "rate": f"{AD['flagged']} flagged in Loop"},
      {"label": "Processed, last 4 weeks", "value": R4["processed"], "display": f0(R4["processed"]), "rate": dproc},
      {"label": "Expired labels, last 35 days", "value": stg["expired_last_35d"], "display": f0(stg["expired_last_35d"]), "rate": "Never shipped back"}]),
   right=dict(kind="hbars", title=("AT THE DC, NOT PROCESSED · DAYS SINCE RECEIVED" if by_rcv else "AT THE DC, NOT PROCESSED · DAYS SINCE SUBMITTED"), legend=["Waiting on DC", "Flagged in Loop"],
              items=[{"label": b["label"], "value": b["waiting"], "cmp": b["flagged"], "display": f"{b['waiting']} + {b['flagged']} flagged", "hl": b["label"] == AD["oldest_label"]} for b in AD["buckets"]],
              note=(("Received date from the DC file. " if by_rcv else "No received date in Loop's export, MCP or Polar, so ages count from submission. ")
                    + f"Flagged = held for review in Loop. Last 4 wks: {R4['submitted']} submitted (LY {RL['submitted']}), {R4['exch_share']:.0f}% exchanges (LY {RL['exch_share']:.0f}%), ${R4['refund_usd']/1000:.1f}K refunded."))),
  notes=OBS.get("notes", {}).get("returns", [])))

# 8 return trends
rc, rl = RAW["loop_reason_amount_4wk"]["cy"], RAW["loop_reason_amount_4wk"]["ly"]; coh = RAW["loop_cohort_return_rate"]
wrong_chg = round(100 * (rc.get("Received Wrong Item", 0) / max(rl.get("Received Wrong Item", 1), 1) - 1)); tot_chg = round(100 * (sum(rc.values()) / sum(rl.values()) - 1))
slides.append(dict(type="finding", id="return_trends", sec="07", kicker="Return trends", pill="LAST 4 WKS VS LY", jamie=True,
  headline=H.get("return_trends", f"Wrong-item returns {wrong_chg:+d}% to ${rc.get('Received Wrong Item',0)/1000:.1f}K while total returned value {tot_chg:+d}%; return rate {100*coh['cy']['rate']:.1f}% vs {100*coh['ly']['rate']:.1f}%"),
  callout=CO.get("return_trends"), footer=foot(f"Polar Loop Returns connector · reasons by return date ({W4} vs {LYW4}) · rates by order date ({coh.get('_window','')})"),
  body=dict(layout="two_cards", split=0.48,
   left=dict(kind="hbars", title="RETURNED VALUE BY REASON · LAST 4 WEEKS VS SAME WEEKS LY", legend=["Last 4 wks", "LY"],
             items=[{"label": k, "value": v, "cmp": rl.get(k, 0), "display": f"${v/1000:.1f}K vs ${rl.get(k,0)/1000:.1f}K", "hl": k == "Received Wrong Item"} for k, v in rc.items()],
             note=f"Return rate = orders with a return ÷ orders ({f0(coh['cy']['returned'])} of {f0(coh['cy']['orders'])})."),
   right=dict(kind="table", title="MOST-RETURNED PRODUCTS · BY ORDER DATE", columns=[{"h": "Product", "w": 3}, {"h": "Units returned", "w": 1.2, "a": "r"}, {"h": "Units sold", "w": 1.1, "a": "r"}, {"h": "Rate", "w": 0.8, "a": "r"}],
              rows=[[p, f0(u), f0(s_), {"t": f"{100*u/s_:.1f}%", "c": "bad" if u / s_ > 0.035 else None, "b": u / s_ > 0.035}] for p, u, s_ in RAW["loop_top_products"]],
              note="Products with 300+ units sold. Product x reason detail: Polar Loop connector.")),
  notes=OBS.get("notes", {}).get("return_trends", [])))

# 9 issues log: last week's open items first, then this week's red/amber rows, then watch items
chip = lambda s_: {"t": s_.upper(), "fill": FILL[s_][0], "fc": FILL[s_][1], "b": True}
today = f"{pd.Timestamp.now(tz=CFG['timezone']):%b %-d}"
irows = []
for it in OBS.get("last_week_open", []):
    irows.append([str(len(irows) + 1), it["text"], chip(it.get("status", "watch")), it.get("slide", ""), it.get("opened", ""), it.get("owner", ""), it.get("next", ""), it.get("due", "")])
for r in rows:
    if r["status"] in ("red", "amber"): irows.append([str(len(irows) + 1), f"{r['metric']}: {r['value']} ({r['cmp']})", chip(r["status"]), r["slide"], today, "", "", ""])
for it in OBS.get("issues_extra", []): irows.append([str(len(irows) + 1), it["text"], chip("watch"), it.get("slide", ""), today, "", "", ""])
slides.append(dict(type="finding", id="issues", sec="08", kicker="Open issues log", pill="CARRIES WEEK TO WEEK", jamie=False,
  headline=H.get("issues", f"{len(irows)} open items; owner, next step and date get set in the meeting"),
  footer=foot("Carried items from last week, then this week's red and amber tripwires"),
  body=dict(layout="card_full", card=dict(kind="table", title="OPEN ITEMS · CLOSE AN ITEM ONLY WHEN ITS TRIPWIRE IS GREEN", dense=True,
   columns=[{"h": "#", "w": 0.35}, {"h": "Issue", "w": 6.2}, {"h": "Status", "w": 0.8}, {"h": "Slide", "w": 0.55}, {"h": "Opened", "w": 0.7}, {"h": "Owner", "w": 1.2}, {"h": "Next step", "w": 2.2}, {"h": "Due", "w": 0.7}], rows=irows))))

notes = OBS.get("notes", {})
for s_ in slides:
    s_.setdefault("notes", notes.get(s_["id"], []))
    if s_.get("callout") is None: s_.pop("callout", None)
    for b in s_["notes"]:
        if len(b) > 260: sys.exit(f"SPEC FAILED: note on {s_['id']} over 260 characters: {b[:60]}...")
json.dump({"meta": {"week": WEEK, "title": "Ecom Ops Weekly Flash"}, "slides": slides}, open(f"{RUN}/data/deck_{WS}.json", "w"), indent=1, ensure_ascii=False)
with open(f"{RUN}/data/issues_{WS}.md", "w") as fh_:
    fh_.write(f"# Data issues · week {WEEK}\n\n" + "\n".join(f"- {x}" for x in M["issues"] + M["missing"]) + "\n")
print(f"wrote data/deck_{WS}.json · {nred} red, {namb} amber, {ngrn} green")
for s_ in slides: print(f"  {s_['id']}: {s_.get('headline', '')}")
