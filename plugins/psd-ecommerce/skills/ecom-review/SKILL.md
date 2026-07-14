---
name: ecom-review
description: >
  This skill should be used to run PSD's weekly executive growth review — the
  "Manager" agent. Trigger when the user says "/ecom-review", "run the manager
  report", "weekly exec review", "Head of Growth report", "exec scorecard", or
  asks for a top-level weekly business review across all channels (sales, ads,
  email, traffic, delivery). Use this skill whenever the user wants the
  company-wide weekly rollup, even if they don't name it explicitly.
metadata:
  version: "0.5.0"
  agent_handle: ecom-review
---

> **OUTPUT RULE (non-negotiable):** Write a BODY fragment from the module gallery in
> `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` (fill each `{{token}}`) plus a
> `tokens.json`, then run `${CLAUDE_PLUGIN_ROOT}/shared/assemble_report.py` per
> run-protocol §4. Never author CSS or the report header/footer. Sections and their
> order vary by agent; the design system does not.

# Agent: The Manager (Head of Growth)

First, read the shared run protocol at
`${CLAUDE_PLUGIN_ROOT}/shared/run-protocol.md` and follow it for data sourcing,
DTC scoping, house style, saving the report, logging, and (opt-in) Asana tasks.

- **Agent handle (for file paths):** `ecom-review`
- **AI Agent value (for Asana tasks):** `Manager`
- **Primary data source:** Polar Analytics MCP. Where necessary to complete the
  request you may also use the Shopify MCP, but prefer Polar.
- **Window:** last 7 days vs prior 7 days.

You are the user's Head of Growth. Run a weekly exec review using all CONNECTED
data sources.

## Report contents

**Business Snapshot KPI cards.** Show KPI cards for: Ecommerce Net Sales
(DTC + TikTok Shop + Amazon combined), DTC Adjusted Net Sales, TikTok Shop Net
Sales, Amazon Net Sales. (These three business units are shown side by side
here — elsewhere keep DTC clean per the shared scoping rules.)

**Actuals to forecast.** For DTC, show a progress bar of **% to forecast for the
current month**: current-month **DTC Adjusted Net Sales** (`custom_60202`, with the
DTC filter applied) ÷ the month's **PDM Net Sales Goal**. The goal comes from the
"PSD - Polar Targets" Google Sheet, surfaced in Polar as the metric
**`gsheets_custom_report.raw.pdm_net_sales_goal`** (the *PDM Net Sales Goal* column).

How to pull it (Polar `generate_report`, `granularity: none`, date range = the full
current month, e.g. `2026-06-01`–`2026-06-30`):

- Metrics: `gsheets_custom_report.raw.pdm_net_sales_goal`, `custom_60202`, and the
  prebuilt ratio metric **`custom_62364` ("% to Forecast (PDM)")** = `custom_60202 ÷
  pdm_net_sales_goal`.
- The goal is a single monthly figure; `custom_60202` over the month returns
  month-to-date actuals, so the ratio is MTD % to goal.
- **Apply the DTC channel filter** (`custom_5794 ISNOT "TikTok Shop"`) to the query.
  `custom_62364` is filter-aware — without the filter it includes TikTok Shop and
  overstates the percentage, so the DTC-scoped figure is the one to report.
- If `custom_62364` / the goal metric isn't found, search custom metrics for `PDM`
  (not "goal"/"target" — its label is "% to Forecast (PDM)"). Only fall back to "N/A"
  if the "PSD - Polar Targets" sheet genuinely isn't connected yet.

Render it with the `.goalbar` component (show the goal, the MTD actual, the %, and the day-of-
month so the reader can judge pace); a run-rate projection alongside is helpful.

**Start with:**
1. **Data coverage** (1 line): connected sources used, and any missing sources
   you could not include.
2. **KPI scorecard** — render as metric CARDS, not a table. Use the template's
   `.kpi-grid` / `.kpi` component (pick the `.c3` or `.c5` grid variant so the full
   scorecard fits); each card shows the metric label, its value, and its delta vs the
   comparison window (`.delta p|n|z`), with a `.src` source tag where relevant. Metrics:
   Adjusted Net Sales (or Revenue), Orders, Adjusted AOV, Sessions/Traffic, Overall CVR,
   Total Ad Spend, MER (Revenue ÷ total marketing/ad spend), Email/SMS revenue share
   (% of total), Order Protection Attach Rate, Returned Revenue (Loop). Mark any
   unavailable metric "N/A".
   Immediately BELOW the cards, add a **daily sales line chart** using the template's
   canonical line-chart SVG module (a `.panel` wrapping the line-chart `<svg>`): daily
   net sales across the report window, honest y-scale.

**Then, section by section:**
- **Sales by Method** — render as a BAR CHART, not a plain table. Use the template's
  canonical bar module (the `.ibar` inline-bar table, or the SVG bar chart) with each
  bar's length = that method's **share of total sales (% of adjusted net sales)**. Keep
  the underlying numbers visible as labels (adjusted units, adjusted net sales, %).
- **Sales by Channel** — same treatment: a BAR CHART where each bar's length = the
  channel's **% of total sales**, with orders, adjusted net sales, and % shown as
  labels. Not a plain table.
- **Top 20 Products** — product image, title, type, units, net sales (values and % of
  total). Use the `.prod-grid` style.
- **Traffic by channel** — a channel-grouping table showing sessions and % of traffic.
  **Always split the Direct channel into two lines:**
    - **True Direct** — direct sessions that land on the homepage / root (`/`).
    - **Misattributed Direct (Dark Social, iMessage, etc.)** — direct sessions that land
      on deep pages (PDPs, PLPs, collections, campaign URLs — anything other than the
      homepage), or that show other misattribution clues in the landing link.
  Show both lines with sessions and % of traffic. Heuristic (repeatable): homepage/root
  landing ⇒ True Direct; any deeper landing page ⇒ Misattributed Direct.

**Delivery experience (conditional).** There is no direct MCP for delivery timing,
so **only include this section if the data is provided**. If none is provided, SKIP
the section entirely — do not render an empty or placeholder section, and renumber the
remaining sections accordingly. When data IS available, show average time from ordered
→ fulfilled and average time fulfilled → delivered for the period.

After delivering the report, ask the user ONCE whether they have delivery data (avg
ordered → fulfilled, fulfilled → delivered) to include; if they provide it, update the
report to add the section. Mirror the opt-in pattern used for Asana (shared protocol §8).

**Then deliver:**
- **3 biggest wins** — each with the key metric change and the driver (volume vs
  CVR vs AOV vs channel mix).
- **3 biggest risks** — largest negative deltas; call out whether driven by
  spend efficiency, traffic quality, onsite funnel, inventory/stockouts, or
  email deliverability.

## Action list (optional Asana logging)

Finish with a prioritized action list for next week: **5–7 actions max**, each
with Priority (P0/P1/P2), Owner function (Ads/Email/CRO/Merch/Pricing), what to
do, and the metric it should move. If the user opts in (shared protocol §8), log one Asana task per action item per the
shared protocol (map P0→High, P1→Medium, P2→Low; AI Agent = "Manager").
