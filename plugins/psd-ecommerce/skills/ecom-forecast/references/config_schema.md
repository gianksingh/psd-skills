# Config schema for build_workbook.py

The builder owns all layout, formulas, and styling. You supply only the numbers
and labels. Build one config per channel (web and TTS are separate workbooks),
write it to a `.json` file, then run:

```
python3 scripts/build_workbook.py config.json /path/to/PSD_<CHANNEL>_<PERIOD>_Forecast.xlsx
```

## Top level

| key | type | notes |
|---|---|---|
| `channel` | `"web"` or `"tts"` | controls columns: web = 17-col w/ Y/Y + OP + ship split; tts = 8-col simplified |
| `period_label` | string | e.g. `"Q3 2026"`, `"July 2026"`. Used in dashboard "<period> TOTAL" header |
| `dashboard_sheet_name` | string | e.g. `"Q3 Total"` |
| `summary_title` | string | dashboard A1 |
| `summary_subtitle` | string | dashboard A2 (the "fill yellow cells…" note + build date) |
| `months` | array | one object per month (see below). Order = left-to-right tab order |
| `appendix` | object | see below |

## months[] — one per month

| key | type | notes |
|---|---|---|
| `name` | string | `"July"` |
| `sheet_name` | string | exact tab name, e.g. `"WEB Jul-26 Daily Fcst"` |
| `daily_title` | string | A1 of the daily tab |
| `daily_subtitle` | string | A2 of the daily tab |
| `total_label` | string | label in the daily total row col A, e.g. `"JUL TOTAL"` |
| `dashboard_title` | string | section header on the dashboard, e.g. `"JULY 2026"` |
| `net_sales_target` | number | monthly adjusted net sales target → Appendix control |
| `baseline_aov` | number | baseline adjusted AOV → Appendix control |
| `baseline_upt` | number | baseline adjusted UPT → Appendix control |
| `op_attach` | number (web only) | order-protection attach rate, e.g. `0.65` |
| `expedited_pct` | number (web only) | expedited share of orders, e.g. `0.03` |
| `ly_actual` | object | monthly LY actuals shown on dashboard col C: `net_sales, orders, units, aov, upt` (omit/null any not comparable) |
| `month_ly` | object (web only) | LY denominators for the daily TOTAL-row Y/Y: `orders, net_sales, units, retail_orders, retail_net_sales, retail_units` |
| `days` | array | one object per calendar day |

### days[] (web)
```json
{ "date": "2026-07-01", "net_sales": 117345, "aov": 77, "upt": 4.2,
  "note": "PROMO: July 4th Markdown Push (Day 1)",
  "cal_ly":    {"orders":1670,"net_sales":109564,"units":6061},
  "retail_ly": {"orders":1769,"net_sales":109062,"units":6183} }
```
- `net_sales` is the **forecast daily net sales** (the allocation you compute). Orders/units/OP/ship are derived by formula.
- `aov`,`upt` are the per-day adjusted AOV/UPT (constants on non-promo days, adjusted on promo days).
- `cal_ly` = same calendar date last year. `retail_ly` = same week#+weekday last year (LY date +1 day).
- `note` optional (DC callouts / promo labels).

### days[] (tts)
```json
{ "date": "2026-07-01", "net_sales": 9032, "note": "Flat run rate" }
```
- AOV/UPT come from the Appendix constants automatically; no LY comps.

## appendix

| key | type | notes |
|---|---|---|
| `title` | string | A1 |
| `note_target`,`note_aov`,`note_upt` | string | source notes in col E of the controls rows |
| `note_op`,`note_expedited` | string (web only) | source notes |
| `dow_weights` | object (web only) | `{"Monday":0.138, ... "Sunday":0.171}` — share-of-week weights |
| `dow_header` | string (web only, optional) | header text for the DOW section |
| `promo_header` | string (web only, optional) | header text for the promo table |
| `promo_events` | array (web only) | `{event, dates, lift, aov, notes}` per event |
| `methodology` | array of strings | numbered methodology lines |

Notes are optional everywhere; omit a key to leave the cell blank.
