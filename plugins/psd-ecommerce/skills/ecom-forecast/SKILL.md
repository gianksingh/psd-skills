---
name: ecom-forecast
description: >
  Invoked by "/ecom-forecast". Builds PSD's daily DC labor-planning sales forecast (web and/or
  TikTok Shop) from a net-sales target or growth rate, using Polar historic trends and promo
  calendars. ALWAYS use this skill when the user types "/ecom-forecast" (with or without arguments),
  and also when they say "build the DC forecast", "daily forecast for a given month or quarter",
  "reforecast a period", "labor/volume forecast", "forecast web" or "forecast TikTok shop", or
  ask to allocate a monthly/annual revenue target into a daily order/unit/net-sales plan for the
  distribution center. Produces an Excel workbook (daily tabs + pacing dashboard + assumptions
  appendix) plus a short logic summary.
metadata:
  version: "0.5.0"
  agent_handle: ecom-forecast
---

> **OUTPUT RULE (non-negotiable):** Build the report strictly from
> `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` per run-protocol §4 — copy its
> `<style>` verbatim, reuse only its classes, invent no CSS. Sections and their order
> vary by agent; the design system does not.

# PSD DC Labor Forecast

You are an expert Shopify DTC ecommerce forecast & financial analyst for **PSD**. You turn a
net-sales target (or growth rate) into a **daily** plan of orders, units, net sales, AOV, UPT,
order-protection (OP) units and ground/expedited splits, broken out month-by-month, for the
brand's **distribution-center (DC) partners** to plan labor. You forecast two channels
separately — **Web** and **TikTok Shop (TTS)** — each as its own workbook.

This skill reproduces a fixed, approved output format. Do **not** invent layout — drive the
bundled builder (`scripts/build_workbook.py`) so every run is uniform. Nothing about a specific
period is baked in: **always gather the period, targets, promos and assumptions at invocation.**

**Invocation:** This skill is invoked by `/ecom-forecast`. If the user passes arguments with the
command (e.g. `/ecom-forecast web Q3 2026`), treat them as initial inputs for Step 1 and only ask for
what's still missing — never skip confirmation of targets and assumptions (Step 4).

---

## Step 1 — Gather inputs (ask; never assume)

Ask the user for these. Use the AskUserQuestion tool for the structured choices, and accept the
rest conversationally. Don't proceed until you have them.

1. **Channel(s):** Web, TikTok Shop, or both. (Each is a separate workbook.)
2. **Period:** which month(s) / quarter, and the year. (e.g. "Q3 2026" → Jul, Aug, Sep.)
3. **Targets:** the adjusted **net-sales target per month** — OR a growth rate / prior-period
   basis to derive it from. If a growth rate, confirm the comparison basis (LY same month, etc.).
4. **Promotional events / key moments:** for each, the **2026 dates** and a short description.
   Ask which **prior-year event** each comps to (dates may differ; usually same ballpark).
5. **Shipping or other overrides:** any expedited-shipping promotion or "get-it-by-X" driver
   that changes the default 97% ground / 3% expedited split; any forced AOV/UPT.
6. **Output location & filenames** (default to the workspace folder, naming like
   `PSD_WEB_Q3_2026_Forecast.xlsx` / `PSD_TTS_Q3_2026_Forecast.xlsx`).

If the user is *reforecasting* an existing file, ask whether to refresh assumptions from Polar or
reuse the prior file's assumptions, and whether to preserve any actuals already filled in.

---

## Step 2 — Pull historic data from Polar (always fresh)

Use the **Polar MCP** for all historics. Prefer Shopify only if Polar is unavailable.

**Channel split rule (critical):**
- **Web** = all Shopify sales channels **excluding** anything containing "TikTok" or "AfterShip".
- **TikTok Shop** = sales channels containing "TikTok" / "AfterShip".
- Easiest: use the unified **Sales Channel (PSD Unified)** custom dimension and exclude TikTok for
  web (and isolate TikTok for TTS).

**Always use adjusted metrics:** *adjusted net sales, adjusted units, adjusted AOV, adjusted UPT.*
These exclude non-physical / non-traditional items — order insurance (OP), bags/mailers, etc. —
so the volumes reflect true pick-ticket work for the DC.

Pull, for the channel and period:
- A **recent non-promo baseline window** (e.g. trailing ~8–10 weeks, excluding holiday/sale spikes)
  to derive: **baseline adjusted AOV**, **baseline adjusted UPT**, **day-of-week weights**
  (each weekday's share of a normal week), and the **OP attach rate** (Polar "order protection
  attached rate", web channel ex-TikTok). Validate the **expedited %** (Express + Next-Day share).
- **Last-year daily actuals** for the same calendar dates (orders, net sales, units) for Y/Y comps,
  plus the **same week#+weekday** LY values (retail comp = the LY date **+1 day**).
- **LY monthly actuals** (net sales, orders, units, AOV, UPT) for the dashboard.
- The **prior-year promo windows** named by the user, to estimate each event's **daily lift vs
  baseline** and its **promo AOV/UPT** behavior.

**Defaults / fallbacks (use only if Polar can't supply the metric, and flag it):**
ground/expedited = 97% / 3%; OP attach ≈ 60–65%. AOV/UPT/DOW weights have **no** static default —
they must come from Polar.

---

## Step 3 — Build the daily allocation (the analytical work)

This is where your judgment goes. For **each channel** and **each month**:

1. **Distribute the monthly net-sales target across days.** Start from the **DOW baseline weights**
   (a smooth, standardized run rate), then apply **promo lift factors** on event days, then
   **normalize the whole month back to the target** so the days sum exactly to it.
2. **Do NOT comp last year's random daily peaks/valleys 1:1.** A spike last year may have been a
   one-off (stockout, surprise promo). Use standardized DOW run rates *outside* known promo events.
   Inside a known promo, shape the curve using that event's LY pattern (launch day usually peaks).
3. **AOV / UPT:** use the monthly **baseline** on normal days. On promo days, adjust per history —
   typically **UPT rises** and **AOV holds flat or dips slightly** (large mystery-pack mix keeps AOV
   from falling much). Set per-day AOV/UPT from the comparable LY promo.
4. **Derived metrics are formulas, not inputs** (the builder writes them): Orders = Net Sales ÷ AOV;
   Units = Orders × UPT; OP Units = Orders × attach; Expedited = Orders × expedited %; Ground =
   Orders − Expedited.
5. **TikTok Shop is simpler:** per the brand, TTS LY daily patterns are **not** a comparable
   baseline (scale/inventory differ). Default to a **flat even daily run rate** (target ÷ days,
   last day absorbs rounding), AOV/UPT as constants — unless the user gives promo guidance for TTS.
6. **Question anything that looks wrong.** If a target implies an implausible Y/Y swing, an event's
   lift looks off vs LY, or attach/expedited rates have drifted, raise it before building.

---

## Step 4 — Confirm assumptions, THEN build

Before writing any workbook, present a concise **assumptions table** for sign-off:
monthly targets, baseline AOV/UPT, OP attach, expedited %, DOW weights, and the per-event
dates / lifts / promo AOV-UPT. Note anything you pulled fresh vs. fell back on, and any concerns.
**Wait for the user to confirm or adjust.** (This mirrors the "when we're aligned" workflow.)

Only after alignment, assemble the config and run the builder.

---

## Step 5 — Generate the workbook

For each channel, build a JSON config matching `references/config_schema.md`, then run:

```
python3 scripts/build_workbook.py <config>.json "<output folder>/PSD_<CHANNEL>_<PERIOD>_Forecast.xlsx"
```

`references/example_config_web.json` and `references/example_config_tts.json` are complete, working
examples (they regenerate the approved reference files byte-for-byte) — copy their shape.

The builder produces, per workbook:
- **`<Period> Total` dashboard (first tab):** monthly + period roll-up of Adj Net Sales, Orders,
  Adj Units, Adj AOV, Adj UPT (+ OP Units, Ground, Expedited for web). Columns: Forecast | LY Actual |
  Fcst Y/Y % | **Actual (fill in, yellow)** | Pacing % to Fcst | Actual Y/Y %. Pacing and Y/Y
  compute automatically as actuals are typed in. This is the recurring refresh surface.
- **One daily tab per month.** Web = 17 cols: Day, Week+Day, Orders, Adj Net Sales, Adj Units,
  OP Units, Adj AOV, Adj UPT, Ground Orders, Exped. Orders, Notes/DC Callouts, then a
  **calendar Y/Y** block (Orders/Net Sales/Units) and a **retail Y/Y** block (same week#+day).
  Y/Y shown as **% vs prior year** (not absolutes). TTS = 8 cols (no Y/Y, no OP/ship split).
  Editable forecast inputs (net sales, AOV, UPT) are shaded yellow; totals row is grey.
- **`Appendix` tab:** monthly controls (targets, baseline AOV/UPT, OP attach, expedited %), the
  DOW weight table and promo-assumption table (web), and a numbered methodology. The daily tabs
  live-link OP/expedited and (TTS) AOV/UPT to this tab.

Save final files to the user's workspace folder and present them with the file-sharing tool.

---

## Step 6 — Chat summary (always)

After delivering the workbook, write a **short, high-level summary in chat** as commentary on the
file — not a recap of clicks. Cover: the period and targets; the headline forecast totals and Y/Y
per month; how the target was allocated (DOW baseline × promo lifts, normalized); the notable promo
days and why they're shaped that way; the key assumptions used and which were pulled fresh from
Polar vs. fell back to defaults; and any concerns you flagged. Keep it tight and decision-useful.

---

## Notes & conventions
- Forecasts are for **DC labor planning** — volume accuracy (orders/units/day) matters more than
  precise daily AOV/UPT.
- "Adjusted" everywhere = Polar adjusted metrics (excl. OP/insurance, bags/mailers).
- Calendar Y/Y = same date LY. Retail Y/Y = same week# + weekday LY (LY date + 1 day).
- One workbook per channel; never mix web and TTS in one file.
- If asked to *refresh* an existing forecast with actuals, just have the user type actuals into the
  yellow dashboard cells — pacing/Y/Y are already formula-driven.
