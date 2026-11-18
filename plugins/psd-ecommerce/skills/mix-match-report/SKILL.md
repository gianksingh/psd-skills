---
name: mix-match-report
description: >
  This skill should be used to build PSD's Gift Builder / Mix & Match ("Build Your
  Outfit") performance report. Trigger when the user says "/mix-match-report",
  "mix match report", "mix & match report", "gift builder report", "build your outfit
  report", "how is the gift builder doing", or asks how the outfit builder is doing:
  orders, outfits, men's vs youth split, kit × division performance, builder page
  traffic, add-to-cart or conversion rate, for a date range against a comparison
  range. Produces a self-contained HTML dashboard and an Excel workbook from Polar.
metadata:
  version: "1.0.0"
  agent_handle: mix-match-report
---

> **OUTPUT RULE (non-negotiable):** build the report only with the bundled, fail-closed harness:
> `scripts/compute.py` → `scripts/build_html.py` + `scripts/build_xlsx.py`. Never hand-build HTML,
> never edit `assets/template.html`, its CSS or its layout during a run, and never type numbers into
> the report. When a script stops, fix the input (the pulls or the periods), not the harness.

# Mix & Match (Gift Builder) report

- **What it measures:** orders from the Gift Builder at `/pages/gift-builder`. Every line added by the builder carries `_fit_id`, `_fit` (kit), `_fit_division` (men/youth), `_fit_slot`, `_fit_name`, `_fit_icon` and `_fit_price` (kit price in cents). The order carries the code **Build Your Outfit**.
- **Data:** Polar MCP only, view `31552-mpfv58vy` (PSD Web), for both the Gift Builder figures and the web totals. Shopify MCP is not needed. Kit names and fallback prices are in `config.json`; refresh them from the Shopify Fit metaobject (`metaobjects(type: "fit")`) when kits change.
- **The run writes:** numbers and charts. **It never writes:** recommendations or commentary inside the report. Data problems go in the chat hand-back, not the report.
- **Shared protocol:** if `${CLAUDE_PLUGIN_ROOT}/shared/run-protocol.md` exists, follow its save, log and hand-back sections, adapted to the two files below. Skip its HTML assembly and Asana sections, because this report has its own template and no action items.

`${SKILL}` below means this skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/mix-match-report`.

## 1. Intake: report and comparison periods (always first)

If the user's message already gives both a report period and a comparison period, use them and skip to step 2.

Otherwise ask before pulling anything, using AskUserQuestion (or plain text if it isn't available), with one question each:

1. **Report period.** Options: "Last full week (Mon–Sun)", "Month to date", "Last full month", "Since launch (Oct 23, 2026)". The user can type a custom range under "Other".
2. **Comparison period.** Options: "Previous period (same length, right before)", "Same period last year", "None". The user can type a custom range under "Other".

Then turn the answers into exact dates in America/Los_Angeles (Polar's `resolve_date_range` can do this) and confirm them back in one line, for example "Nov 11–17, 2026 vs Nov 4–10, 2026". If the comparison is "None", use the previous period anyway and say so: the report always shows a comparison. If the two periods have different lengths, say that totals won't be like-for-like and carry on.

Never invent a default period without telling the user. If the session is unattended (a scheduled run), use last full Mon–Sun week vs the week before and state that at the top of the hand-back.

## 2. Set up the run folder

Work in the connected project folder at `reports/mix-match-report/<from>_<to>/` (create it). If no folder is connected, use a folder in the session workspace and say so in the hand-back.

```bash
export SKILL="${CLAUDE_PLUGIN_ROOT}/skills/mix-match-report" RUN="$PWD"
mkdir -p data build
python3 -c "import openpyxl" 2>/dev/null || pip install openpyxl --break-system-packages -q
```

## 3. Pull the data (Polar MCP)

Call `get_context` first. Then run the 7 pulls in `${SKILL}/references/polar-pulls.md` for each period (14 calls; pages for `lines` and `orders` when the row limit is hit). Write the responses into `data/raw.json` in the shape of `${SKILL}/references/raw_schema_example.json`:

```json
{"meta": {"period": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
          "compare": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
          "generated": "<today>", "notes": []},
 "cur":  {"lines": {...}, "orders": {...}, "web": {...}, "traffic_daily": {...},
          "traffic_landers": {...}, "traffic_channel": {...}, "traffic_device": {...}},
 "prev": {same keys}}
```

Write the responses with a short Python script that dumps them as they are. Don't retype rows by hand. Copy `tableData` and `totalData` exactly as Polar returned them.

## 4. Compute and build

```bash
python3 "$SKILL/scripts/compute.py"    data/raw.json data/data.json          # → data/data.json, data/issues.md
python3 "$SKILL/scripts/build_html.py" data/data.json "build/PSD_Mix_Match_Report_<from>_to_<to>.html"
python3 "$SKILL/scripts/build_xlsx.py" data/data.json "build/PSD_Mix_Match_Report_<from>_to_<to>.xlsx"
```

- `compute.py` stops (exit 1) when a pull is missing, the periods are missing, or the report period has no Gift Builder lines. Report the stop message to the user and don't build anything.
- If the xlsx skill is available, run its `scripts/recalc.py` on the workbook. It must report `success` with 0 errors before delivery.
- Never pass `--filler` on a real run. That flag is only for `scripts/make_fixture.py` test data, and it puts a FILLER banner on both files.

## 5. Check, then deliver

1. Open the HTML in a headless browser (Playwright is preinstalled in Cowork), take a full-page screenshot and look at it. Check that the KPIs show values (no `NaN` or `$NaN`), the period line shows the confirmed dates, and there is no FILLER banner.
2. Spot-check 3 numbers against the raw pulls: Gift Builder orders (distinct `order_id` in `lines`), builder sessions (`traffic_daily.totalData`), and PSD Web orders (`web.totalData`).
3. Deliver both files with SendUserFile (HTML first, then the xlsx), and save them in the run folder. If a folder is connected, also write them there.
4. Hand back in a few lines:
   - the two periods;
   - net sales, orders, outfits and the men's/youth outfit split;
   - everything listed in `data/issues.md` (code-only orders, kit price changes, low-traffic warnings, uneven period lengths), for the user to check;
   - any `dataThrough` caveat from the pulls.

   Don't add recommendations unless the user asks.

## Files

| Path | Role |
|---|---|
| `config.json` | Polar view, builder path, discount code, kit names, slots and fallback prices |
| `references/polar-pulls.md` | the 7 Polar pulls, with exact parameters |
| `references/raw_schema_example.json` | shape of `data/raw.json` (2 rows per pull) |
| `scripts/compute.py` | raw pulls → `data.json` + `issues.md`. Parses `_fit*` properties: outfits = distinct `_fit_id`, kit price = `_fit_price`, compare-at = list value of the outfit's items |
| `scripts/build_html.py` | injects `data.json` into `assets/template.html` (Shopify admin-style dashboard, no external assets) |
| `scripts/build_xlsx.py` | 9-tab workbook: Summary, Division, Kit x Division, Daily, Traffic, Top Picks, Kit Config, Definitions. Inputs in blue, calculations as live formulas |
| `scripts/make_fixture.py` | writes synthetic `raw.json` for testing (`make_fixture.py data/raw.json`, then `compute.py ... --filler`) |
| `assets/template.html` | the report template. Never edit it during a run |

## Definitions (kept in sync with the report's Definitions panel)

- **Gift Builder order:** an order with at least one `_fit_id` line. Orders that used the code but have no builder lines are excluded and listed in issues.
- **Outfit:** one distinct `_fit_id`.
- **Division:** men or youth from `_fit_division`. An order holding both is "mixed", so division order counts add up to more than total orders.
- **Net sales:** gross + discounts + returns, excluding shipping and tax. Program net sales include add-on items; outfit net sales cover builder lines only.
- **Share of web:** Gift Builder ÷ PSD Web orders or net sales, both in the PSD Web view.
- **Builder sessions / landing sessions:** Polar Pixel sessions whose `page_paths_in_session` contains the builder path, or whose `landing_page_path` is the builder path.
- **Conversion rate:** in the overview and funnel, Gift Builder orders ÷ builder sessions. In the segment tables, builder sessions that placed any order ÷ builder sessions.
