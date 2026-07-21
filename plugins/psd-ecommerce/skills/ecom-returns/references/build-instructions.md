# PSD Returns Report — Build Instructions

A reusable runbook for regenerating the PSD monthly **Returns operations & economics** report
(`psd-returns-report-YYYY-MM.html`). Cadence: monthly (or ad hoc MTD). Owner: e-commerce analytics.

---

## 0. Concept: two lenses, one report

The report deliberately combines **two data sources on two different date bases**. Keep them
separate — do not try to make them tie out.

| Lens | Source | Basis | Answers |
|---|---|---|---|
| **Settled** (§1–4) | Polar → `loop-returns` connector | **settled-date** (return resolved/closed) | What has been resolved and what it cost |
| **In-flight** (§5) | Loop Returns MCP | **created-date** (return requested) | What has come in and where it is now |

The in-flight returns in §5 settle into §1–4 over the following ~2–4 weeks. This lag is *why*
the §3 trend tapers in the most recent weeks and why the two lenses show different counts
(e.g. July 2026: Loop = 681 requested vs Polar = 317 settled). State this in the method footer
every time.

---

## 1. Period logic

- Default window = **month-to-date**: `dateRangeFrom = <first of month>`, `dateRangeTo = <today>`.
- Timezone: America/Los_Angeles. Week start: Monday.
- For a closed month, use the full calendar month.
- The §3 trend uses the **trailing 8 ISO weeks** ending the current week.

---

## 2. Data pulls

### 2a. Polar setup (once per session)
1. `get_context({ initialQuestion, version: "4.3" })` → save `conversation_id`.
   Confirm `account_status.data == "ready"` and that `loop-returns` is in `custom_connectors`.
2. Metric keys are stable; the ones this report uses are listed below. If a pull errors,
   re-run `get_metrics({ sourceList: "loop-returns,custom-metrics" })` to refresh keys.

### 2b. Polar metric keys (Loop Returns connector)
Raw:
- `generated_root_loop_returns.raw.return_amount` — Returned Item Value ($)
- `generated_root_loop_returns.raw.refund_amount` — Cash Refunded ($)
- `generated_root_loop_returns.raw.exchange_amount` — Revenue retained via exchange ($)
- `generated_root_loop_returns.raw.handling_fee` — Handling Fees Collected ($)
- `generated_root_loop_returns.raw.shipping_cost` — Return Shipping Cost ($)
- `generated_root_loop_returns.raw.returned_units` — Returned Units
- `generated_root_loop_returns.raw.return_orders` / `.returned_order_count` — Return Orders
- `generated_root_loop_returns.raw.order_count` — Orders (return-rate denominator)

Computed:
- `generated_root_loop_returns.computed.order_return_rate` — same-period return rate
- `generated_root_loop_returns.computed.avg_units_per_return` — Avg Units / Return
- `generated_root_loop_returns.computed.exchange_rate` / `.refund_rate`

Custom (PSD-authored — prefer these for headline finance figures):
- `custom_64543` — **Net Return Cost ($)** = cash refunded + return shipping − handling fees
- `custom_64544` — Revenue Retained via Exchange ($)
- `custom_64545` — **Dollar Retention Rate (%)** = exchange ÷ returned value
- `custom_64547` — Same-Period Return Rate (%) = return orders ÷ orders

Compatible dimensions for these metrics (from `list_dimensions`):
`product_title` (variant-level, incl. size/color), `outcome`, `return_reason` (child),
`parent_return_reason`, `state`, `sales_channel`, `return_date`, `order_name`.

### 2c. Polar reports to run (all `granularity` unless noted; `settings={}`, `rules={}`, `metricRules={}`)
1. **§1–2 totals** — `granularity=none`, no dimension. Metrics: the raw + computed + custom list
   above. Read the single totals row.
2. **§3 trend** — `granularity=week`, `dateRangeFrom = Monday 8 weeks back`, no dimension.
   Metrics: `return_orders, returned_units, order_return_rate, exchange_rate`. Sort ASC by date
   for display. **Mark the last ~2 weeks as "still settling"** (they will read near-zero).
3. **§4 products** — `dimensions=product_title`, `limit=10`, order by `returned_units DESC`.
   Metrics: `returned_units, return_amount, refund_amount, exchange_amount, shipping_cost, exchange_rate`.
4. **§3 reasons** — `dimensions=return_reason` (child; gives too small/large split) AND/OR
   `parent_return_reason` (rolls fit into one bar). Metric: `returned_units` (+`return_orders`).

### 2d. Loop MCP pulls (§5, created-date basis)
Loop's `list-returns-tool` has **no created-date filter** and caps paging at ~10,000 rows, so:
- **Requested / status split**: page `sort_by=createdAt, sort_direction=desc, limit=100` until
  `created < first-of-month`; tally status per row (closed = completed; open = outstanding;
  cancelled). July 2026: 681 requested = 283 closed + 388 open + 10 cancelled.
- **Counts without paging**: read the header `"...of N"` from a `limit=1` filtered query.
- **Backlog location** (active-open, strips the multi-year stale tail): `status=["open"]`,
  `day_limit=21`, then bucket by `label_status`:
  - in transit = `["pre_transit","in_transit","out_for_delivery"]`
  - at facility = `["delivered"]`
  - not shipped = `["new","no_label","failure"]`
- **Quality/risk** (`day_limit=21`): `flagged=true`; `fraud_risk=has_unconfirmed_high_fraud_risk`
  / `has_confirmed_fraud_risk`; `is_warranty=true`.
- **Policy**: `read-return-policies-tool` (window, fees, outcomes).
- Note the all-time `status=["open"]` count (stale tail back to 2020) as a data-hygiene flag.

---

## 3. Report structure (section spec)

1. **01 · Settled returns** — 4 KPI cards: Order return rate (label "same-period"),
   Avg units/return, Exchange vs refund, Net return cost. Note explaining same-period basis.
2. **02 · Returned value → kept vs lost** — waterfall (Returned value → +exchange → −refund →
   +fees → −shipping) + revenue/cost table + Dollar Retention callout.
3. **03 · Trend & reasons** — 8-week settled bars (last 2 faded) beside the return-reason
   breakdown; headline callout: fit = X% of units, too-small vs too-large skew.
4. **04 · Products driving returns** — top 10 by units: units, returned value, refunded,
   exchange $, ship, exchange % (color pill: red 0%, amber <25%, green ≥25%).
5. **05 · Open returns & operations** — requested/completed/open, backlog location (in transit /
   at facility / not shipped), quality queue, policy, stale-open flag.
6. **Method & caveats footer** — see §4.

---

## 4. Standing caveats (always include)

- **Same-period return rate** understates the cohort rate (lag; open returns not yet counted).
- **Settlement lag**: recent trend weeks look low because those cohorts are still open in Loop.
- **Reconciliation gap**: returned value ≈ exchange + refund, off by the not-yet-resolved
  portion (~$0.5K in Jul 2026). Waterfall is directional.
- **Reason splits are unit-based**; a return can carry multiple units.
- **No YoY from Loop MCP**: no created-date filter + ~10k row cap put July 2025 out of reach.
  Pull year-over-year from Polar if required.

---

## 5. Styling

Styling comes from the unified template per run-protocol §4 — never author CSS.

## 6. Change log
- 2026-07-21 — v1. Initial build (July 2026 MTD). Sections 01–05 as above.
