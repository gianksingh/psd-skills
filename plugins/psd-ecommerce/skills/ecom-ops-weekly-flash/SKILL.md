---
name: ecom-ops-weekly-flash
description: >
  This skill should be used to build PSD's weekly Ecom Ops Weekly Flash deck, the peak-season
  operations and customer-experience check for the 30-minute weekly ops meeting run by the CS &
  operations manager. Trigger when the user says "/ecom-ops-weekly-flash", "ops weekly", "ops flash",
  "weekly ops deck", "eComm weekly check", "CX weekly", "build the ops deck", or asks for the weekly
  review of orders and tickets vs the Q4 staffing forecast, CS SLA, AI vs human handling, fulfillment
  and delivery, where-is-my-order and delivered-not-received contacts, NPS / CSAT / delivery
  satisfaction, or the returns pipeline for a Monday–Sunday week. Produces a 9-slide .pptx (opens in
  Google Slides) with tripwires, What changed / Why / Next steps boxes, an ops-manager context box,
  an open-issues log, and bulleted speaker notes.
metadata:
  version: "1.0.0"
  agent_handle: ecom-ops-weekly-flash
---

> **OUTPUT RULE (non-negotiable):** The output is a PowerPoint deck. Build it only with the bundled,
> fail-closed harness: `scripts/nps_join.py` → `scripts/compute.py` → `scripts/make_spec.py` →
> `scripts/build_deck.js`. Never hand-build slides or change layouts, colors, fonts or slide order in a
> run. When a script stops, fix the input, not the harness.

# Agent: Ecom Ops Weekly Flash

- **Command:** `/ecom-ops-weekly-flash [week_start]` (Monday, YYYY-MM-DD; default = last full Mon–Sun week).
- **Who runs it:** the CS & operations manager, Monday or Tuesday, for the last full week. Peak season (Q4) purpose: catch what needs fixing, investigating or escalating before it grows.
- **Data:** Polar MCP (orders, Gorgias ticket volume, Loop reasons/products), Shopify MCP (ShopifyQL fulfillments, GraphQL customer lookup for NPS, unfulfilled counts), Loop MCP (open-return stages), plus four uploads (§1).
- **What the run writes:** numbers, charts, one headline per slide, the three "things to know", speaker notes, issues. **What it never writes:** recommendations or action items on the slides. The What changed / Why / Next steps boxes and the ops-manager context box stay empty for the presenter.
- **Definitions:** `references/metric-bible.md` is the source of truth. Read it in full before the first query.
- **Shared protocol:** follow `${CLAUDE_PLUGIN_ROOT}/shared/run-protocol.md` §5 (save), §6 (log) and §7 (hand back), adapted to a .pptx. Skip §4 (HTML) and §8 (Asana).

`${SKILL}` = `${CLAUDE_PLUGIN_ROOT}/skills/ecom-ops-weekly-flash`.

## 0. Run folder

Work in the connected project folder at `reports/ecom-ops-weekly-flash/<week_start>/` (create it); if none is connected, use a session folder and say so in the hand-back.

```bash
export SKILL="${CLAUDE_PLUGIN_ROOT}/skills/ecom-ops-weekly-flash" RUN="$PWD" WS=<week_start>
mkdir -p inputs data build
cd "$SKILL/scripts" && [ -d node_modules/pptxgenjs ] || npm install --silent --no-audit --no-fund || npm install --prefix "$RUN" pptxgenjs@4.0.1
cd "$RUN"
```

## 1. Intake (always first, one message, as a checklist)

Ask for everything below, wait, then confirm what arrived and what's missing.

1. **Reporting week** (Mon–Sun). Default the most recent full week; confirm dates.
2. **Gorgias ticket export, this year** → `inputs/gorgias_cy.csv`. Ticket-level CSV covering the last 4 weeks **through Sunday** (columns as in Gorgias' standard export incl. Ticket Reason, AI Agent Outcome, Order Number, First response / Resolution time).
3. **Gorgias ticket export, same 4 weeks last year** → `inputs/gorgias_ly.csv`.
4. **Retently export** → `inputs/retently.csv`. All campaigns, response level, from 13 weeks before the week through Sunday, plus the same 4 weeks last year.
5. **Q4 Staffing Forecast workbook** → `inputs/forecast.xlsx` (needs the `Daily Forecast` tab).
6. **Loop returns export** → `inputs/loop_returns.csv` (or the `Loop Returns data (all time)` tab inside the forecast workbook).
7. **Last week's open items** from the issues log (an empty list is fine). They go first in this week's log.
8. **Anything to call out** (promos, outages, staffing changes). These go in speaker notes, not headlines.

Missing items: carry on, record them in `observations.missing`, and they print on the summary and as INPUT MISSING pills. **Never guess or fill a number.**

## 2. Pull the connector data → `data/raw_<WS>.json`

Match the keys and nesting of `${SKILL}/references/raw_schema_example.json` exactly (week keys are Monday dates). Call Polar `get_context` first.

| Raw key | Pull |
| --- | --- |
| `orders_weekly_cy` | Polar `total_orders` by `custom_5794`, weekly, 8 weeks back through this week; sum into `web` / `tts` per bible §0 |
| `orders_weekly_ly` | Same, for LY weeks from 3 weeks before LY(this week) through 4 weeks after |
| `orders_daily_week` | Same, daily, this week |
| `tickets_weekly_polar` | Polar `generated_root_gorgias.raw.tickets_created`, weekly: total and `channel IS tiktok-shop`; `cy` 8 weeks, `ly` same span as orders LY; store `[web, tts]` |
| `fulfillment_weekly` | ShopifyQL `FROM fulfillments SHOW orders_fulfilled, median_hours_order_to_fulfillment, median_days_order_to_delivery, orders_delivered_fast_rate TIMESERIES week`, 8 weeks CY and LY → `[fulfilled, hrs, days, fast_rate]` |
| `fulfillment_by_service_week`, `fulfilled_total_week` | ShopifyQL same metrics `GROUP BY shipping_service` for the week (no HAVING). Rename "Unknown carrier · Unknown service" to "Service not recorded in Shopify" |
| `shipping_chosen_week` | Polar `total_orders` by `custom_5902` (+`shipping_method`) for the week, web + TikTok channels; add `ships_as`, `ship`, `deliver` from the ShopifyQL service medians |
| `unfulfilled_open` | Shopify `ordersCount` per bible §2 → `{count, asof}` |
| `loop_open_stage` | Loop MCP `list-returns-tool` totals per bible §6 (limit 1, read the "of N" total) → `{label_not_shipped, in_transit, delivered_awaiting_processing, no_label, expired_last_35d, asof}` |
| `loop_reason_amount_4wk` | Polar `return_amount` by `parent_return_reason`, last 4 weeks vs same 4 weeks LY |
| `loop_cohort_return_rate`, `loop_top_products` | Polar Loop rates for orders placed 8–5 weeks ago vs LY; top 10 products by units returned (300+ sold) |

Anything odd you notice while pulling (tracking, labeling, data gaps) goes in `observations.issues_extra` or notes as a fact, never in a headline.

## 3. NPS order lookup → `data/nps_orders.json`, then join

```bash
python3 -I "$SKILL/scripts/nps_emails.py" "$RUN" "$WS"     # prints customer-search strings, 45 emails per line
```
Run ONE Shopify `graphql_query` with one alias per line (`a: customers(first:50, query:"<line>"){...F}`), fragment:
`fragment F on CustomerConnection { nodes { defaultEmailAddress{emailAddress} numberOfOrders orders(first:5, sortKey:CREATED_AT, reverse:true, query:"created_at:>=<WS minus 70 days>"){ nodes { createdAt sourceName shippingLine{title} fulfillments(first:1){createdAt deliveredAt} } } } }`.
The result is large and is saved to a file; copy that file to `data/nps_orders.json`. Then:
```bash
python3 -I "$SKILL/scripts/nps_join.py" "$RUN" "$WS"       # needs 90%+ matched
```

## 4. Compute, then write observations (`data/observations_<WS>.json`)

```bash
python3 -I "$SKILL/scripts/compute.py" "$RUN" "$WS"        # -> data/metrics_<WS>.json
```
Read the metrics, then write observations using `${SKILL}/references/observations_example.json` as the shape:
- `exec_items`: exactly three "things to know". Each: a head with its number (under 90 characters) and one or two factual sentences, plus the slide it points to. Pick the three biggest red/amber movements, not one per section.
- `headlines` (optional overrides): the slide's one takeaway with its number, under 120 characters. Defaults are generated; override only to sharpen.
- `notes`: speaker notes per slide id. **Bulleted, concise, facts first, then one "Interpretation:" bullet where useful.** Correlations, data caveats, sample sizes, measurement changes, and investigation findings belong here. The presenter decides what to use.
- `issues_extra` (watch items for the log) and `last_week_open` (from intake, with owner / next / due if given).

Writing rules (from the no-AI-slop rules, enforced by the build): lead with the number and the thing; plain verbs (rose, fell, ran); no "should / recommend / consider / suggest / must", no delve, leverage, robust, crucial, notably, significantly, seamless; no em dashes in headlines; no "not X, it's Y"; don't tell the reader what matters. Use "order contact rate" (tickets ÷ orders, %) and rates as % of orders, never "per 1,000" or "per 100".

## 5. Build

```bash
python3 -I "$SKILL/scripts/make_spec.py" "$RUN" "$WS"       # -> data/deck_<WS>.json, data/issues_<WS>.md
NODE_PATH="$SKILL/scripts/node_modules:$RUN/node_modules" OPS_ASSETS="$SKILL/assets" \
  node "$SKILL/scripts/build_deck.js" "data/deck_$WS.json" "build/PSD_Ecom_Ops_Weekly_Flash_${WS}.pptx"
```

Slides (fixed order): 01 summary (three things to know, tripwire count, missing inputs) · 02 peak tripwires + ops-manager context box · 03 volume, plan and outlook · 04 fulfillment and delivery (shipping-service-chosen table) · 05 customer service (total, then web vs TikTok Shop; AI vs human; CSAT) · 06 voice of the customer (13-week trend, NPS cuts) · 07 returns pipeline · 08 return trends · 09 open issues log.

## 6. Check, then deliver

1. Render every slide (LibreOffice → `pdftoppm`) and look at each: no overlapping text, notes under tables don't collide, every footer shows the week, INPUT MISSING pills where expected, status chips red/amber/green/grey.
2. Spot-check 5 numbers against the raw pulls: web orders vs plan, TikTok Shop tickets, web order contact rate, like-for-like where-is-my-order rate, rolling NPS.
3. Confirm the What changed / Why / Next steps boxes and the context box are empty, and every slide's speaker notes are bullets.
4. Save the .pptx in `reports/ecom-ops-weekly-flash/<WS>/build/`, add it to `reports/index.html` (run-protocol §5), write the run log (§6) incl. raw keys used and any contradictions.
5. Hand back: send the .pptx, then reply with the week, missing inputs, and the issues list from `data/issues_<WS>.md` for the ops manager to validate. Issues never go on slides except as watch rows in the log.

## Known measurement notes (keep in speaker notes when they apply)
- All-channel where-is-my-order rate overstates year-over-year change (TikTok Shop intake into Gorgias, LY labeling). The tripwire uses the like-for-like rate; the callout prints automatically.
- Shopify records no service on ~40% of fulfillments; Express ships 2nd Day Air from a second UPS account.
- The Gorgias `Resolution` field is empty, so delivered-not-received outcomes are incomplete.
- SLA uses business hours (Mon–Fri 7am–3pm PT); Gorgias' own SLA setting may use calendar hours.
