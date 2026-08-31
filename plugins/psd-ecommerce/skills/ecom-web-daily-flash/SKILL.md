---
name: ecom-web-daily-flash
description: >
  This skill should be used to run PSD's Daily Flash — the recurring executive daily
  business snapshot for PSD Web, rendered as a self-contained HTML dashboard plus PDF
  from Polar Analytics, Shopify and GA4 and delivered as files into the conversation.
  Trigger when the user says "/ecom-web-daily-flash", "daily flash", "web daily flash",
  "daily biz flash", "daily snapshot", "yesterday's web numbers", or "how did web do
  yesterday", and for scheduled daily-snapshot runs whose job is to hand back the
  report files. It is a daily (T-1) web snapshot, distinct from the weekly /ecom-review.
metadata:
  version: "0.1.0"
  agent_handle: ecom-web-daily-flash
---

> **OUTPUT RULE (non-negotiable):** Write a BODY fragment from the module gallery in
> `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` (fill each `{{token}}`) plus a
> `tokens.json`, then run `${CLAUDE_PLUGIN_ROOT}/shared/assemble_report.py` per
> run-protocol §4. Never author CSS or the report header/footer. Sections and their
> order vary by agent; the design system does not.

# PSD Web Daily Flash

The recurring daily executive snapshot for a PSD sales channel (default **web**). Output is a
self-contained HTML dashboard **plus** a PDF, built on the shared PSD report template, delivered
as files.

**This skill publishes nothing.** No git push, no `reports.psd.com`, no Resend, no
`recipients.json`, no PAT, no `summary.json`. It reads data and writes two files. That is the whole
contract, and it is deliberate: with nothing leaving the session, a scheduled run cannot mail a bad
number to your executives or deface a live dashboard. The worst failure mode is a file nobody likes.

Publishing is out of scope by design — never add a live-site push or an email path to this skill.
Keeping every number in-session is the safety property, not a limitation.

The rest still matters. This report is designed to run **unattended on a schedule**, so there is no
human between the query and the reader. A wrong number still ships, just more slowly. Most of the
rules below exist because a specific wrong number shipped before — the reasoning is given so you can
generalize when you hit a case this document doesn't name.

**The report body is numbers.** The interpretation lives in the executive summary (one paragraph,
rules in §7) and in the run commentary. Do not scatter commentary through the sections.

---

## 1. Parameters

| Param | Values | Default |
|---|---|---|
| `channel` | `web` \| `tiktok` | `web` |
| `report_date` | the day being reported | yesterday (T-1) |

**Comparisons** — every headline KPI carries two:
- **vs LY** = same **calendar** date one year prior.
- **vs PD** = the **prior day** (T-2 relative to report date).

If someone asks for a weekday-aligned LY instead, that's a deliberate change — confirm before
switching, because it silently moves every YoY number in the report.

### Channel configuration

**`web` — validated, use as-is:**

| Setting | Value |
|---|---|
| Polar view | `31552-mpfv58vy` (Business Channel – PSD Web) |
| Report title | `PSD WEB` |
| Kicker | `DAILY FLASH · PSD WEB` |
| Scope pill | `PSD Web` |
| Monthly plan | `gsheets_custom_report.computed.psd_pdm_net_sales_goal_monthly` (PDM) |

**`tiktok` — NOT yet validated.** The view is `31552-mq6vjhqq` (Business Channel – TikTok Shop),
but the metric keys, method/division dimensions and plan reference have not been confirmed against
TikTok data. Before running TikTok the first time, re-do the discovery in §2 against that view and
confirm which metrics exist and which sections are meaningful — several web sections (App vs Web,
PSD channel-group traffic) may not apply. Do not assume the web configuration transfers. TikTok will
ship as a **separate sibling command `/ecom-tiktok-daily-flash`** once that §2 validation is
complete; until then this skill runs **web only** (don't delete the config — it's the head start).

---

## 2. Metric and dimension keys (validated for `web`)

| Element | Key |
|---|---|
| Adjusted Net Sales | `custom_60202` |
| Adjusted Demand $ | `custom_64021` |
| Adjusted Units | `custom_60206` |
| Adjusted AOV | `custom_60207` |
| Adjusted UPT | `custom_60208` |
| Orders | `shopify_sales_main.raw.total_orders` |
| New customer rate | `shopify_sales_main.computed.new_customer_rate` |
| Return customer rate | `shopify_sales_main.computed.repeat_customer_rate` |
| New / total customers | `shopify_sales_main.raw.new_customers` / `…total_customers` |
| OP attach rate | `custom_61578` |
| OP gross sales | `custom_62988` |
| OP rev share (est.) | `custom_62989` |
| Ad spend | `total_marketing_spend` |
| Blended CAC | `custom_60086` (PSD-filtered) |
| LTV | `shopify_sales_main.computed.ltv` |
| LTV:CAC | `custom_60102` |
| Gross sales / discounts / returns | `shopify_sales_main.raw.gross_sales` / `…discounts` / `…returns` |
| Pixel sessions / CVR / bounce | `shopify_attribution_pixel.raw.polar_pixel_sessions` / `…computed.polar_pixel_conversion_rate` / `…computed.polar_pixel_session_bounce_rate` |
| GA4 sessions / CVR | `ga_main.raw.sessions` / `ga_main.computed.conversion_rate` |
| Sales channel | `custom_5794` (Sales Channel – PSD Unified) |
| Sales method | `custom_5903` (Sales Method) |
| Division | raw `product_division` — **not** `custom_6321` |
| PSD channel group | `custom_5984` |
| Direct segmentation | `custom_5987` |

**LTV sanity check:** the all-time metric reads ≈ **$104.49** over 2021→present on PSD Web. If a run
returns something far from ~$103–105, the query is wrong — do not build with it. (Net sales ÷ customers
gives ≈$88 because customers don't sum across periods; the native metric handles the dedup.)

Start every run with `get_context` for a fresh `conversation_id`, the Shopify sync cut-off and
connector health.

---

## 3. Data rules — the traps

### 3a. Derived fields lag; raw fields don't

Polar has raw passthrough fields (land with the order, accurate immediately) and derived fields
(computed by a job that backfills *progressively* over 24–48h). On a report about **yesterday**,
derived fields are the single biggest source of confidently-wrong numbers.

Measured on this report: the same Bundle Builder query for the same date returned **$5,142 / 247
units**, then **$9,260 / 512 units** an hour later — a 44.5% understatement, with the missing
revenue misfiled into Single Item Merchandise. Nothing about the earlier result looked broken.

**Consequence for §6:** source **Bundle Builder from the raw field**, not from `custom_5903`'s
`bundle_title` rule:

```
Bundle Builder  → rules: {"order_line_properties":[{"value":["Build Your Own Bundle Pack"],"operator":"CONTAINS"}]}
Everything else → breakdown by custom_5903 with
                  {"order_line_properties":[{"value":["Build Your Own Bundle Pack"],"operator":"NOTCONTAINS"}]}
```

Validated across Aug 5–11: raw vs derived agree within **1% on every settled day** (+0.40% over the
week), and raw is always equal or slightly higher — it catches lines the derived rule misses. So raw
costs nothing on settled days and is correct on recent ones.

Generalize: prefer `product_tags` (plural) over `product_tag`, `order_line_properties` over
`bundle_title` / `is_bundle` / `custom_5509`, `order_tags_in_order` over `order_tag`.

### 3b. Exclude Order Protection from mix sections

Order Protection is a warranty product, not merchandise. Left in, it distorts the mix: it once put
749 phantom orders and −$65 into the division table's blank row, and a negative "Insurance" line
into the method table.

**§6 and §7 filter it out at query time:** `{"product_title":[{"value":["Order Protection"],"operator":"ISNOT"}]}`

This makes those sections total ≈$155 less than headline Adjusted Demand $ on a typical day — that
is expected and correct. Label §6's total row **"Merchandise total"** so the difference is
self-evident rather than looking like a reconciliation failure. OP still appears in §1 as its own
KPI card (attach rate, gross, rev share).

### 3c. Other things that bite

1. **Orders against a product-level dimension are "orders containing"** — they never sum to total
   orders. Report demand $ and units as the summable measures; only show orders where the dimension
   is order-level.
2. **`md_*` discount-decomposition metrics ignore `rules`.** Use them only on unfiltered whole-day
   queries, never under a filter — filtered, they silently return a day-level number that looks like
   a subset.
3. **Never trust `totalData` when `metricRules` is set** — it returns unfiltered.
4. **Filter logic:** same dimension, flat array = OR, nested array = AND. Different dimensions are
   always ANDed.
5. **Channel-group attribution completeness varies with sync recency.** On a same-day pull, 30–50%
   of demand can carry no channel group while sessions attribute fully. Always compute the residual
   explicitly and render a **"Not attributed to a channel group"** row when non-zero — never let the
   shown rows imply they're the whole picture.
6. **Comparisons:** use `comparisonPeriod: "range"` with explicit dates, or `previousPeriod` /
   `previousYear` where the resolved range is verified. Prefer **Adjusted** metric variants.
7. **Before writing down any zero, cross-check it in Shopify.**

---

## 4. Freshness gate — run this before building anything

This report builds itself on a schedule. Nothing is pushed or emailed, but on a scheduled run
nobody is reading over your shoulder either — the files land and get read later, out of context.
Decide up front whether the data is trustworthy enough to render.

1. `get_context` — note the Shopify sync cut-off and connector health.
2. If any connector is `warning` or `broken`, run `get_connector_statuses`, and
   `get_data_integrity_report(datasource_id)` if `data_integrity.failed > 0`. That report gives a
   per-day expected-vs-actual comparison and names failing dates.
3. Cross-check the same window in ShopifyQL
   (`FROM sales SHOW gross_sales, net_sales, discounts, returns, orders TIMESERIES day`) and compare
   the day-over-day *shape*. If Shopify shows −20% and Polar shows −58%, the gap is the sync, not the
   business.

**A day that reads sharply down deserves suspicion before it deserves rendering.** A real example:
Polar showed −34% YoY when the integrity report revealed 46.6% of that day's orders simply hadn't
landed yet.

**If the gate fails: build nothing.** Do not render a report you don't trust — a plausible-looking
dashboard is more dangerous than no dashboard, because it gets forwarded. Emit the withheld notice
instead (§11), naming the date, the suspected gap, the evidence, and when a re-run should be clean.
Late is recoverable; a wrong number that someone acts on is not.

---

## 5. Section order

Numbered `01`–`10` (09 is intentionally unused — the numbering leaves room without renumbering
everything). Hero and headline metrics precede §01.

| # | Section | Component | Contents |
|---|---|---|---|
| — | Executive summary | `callout` | One paragraph, rules in §7 |
| 01 | Yesterday — Top-line KPIs | `kpi-grid` | 8 cards, each with **two** delta chips (vs LY, vs PD): Adj Net Sales, Adj Demand $, Orders, Adj Units, Adj AOV, Adj UPT, New customer rate (sub: `{new} new / {total} total`), OP attach rate (sub: `Gross $X · est. rev share $Y`) |
| 02 | Month-to-date pace to plan | `goalbar` + `<details>` accordion | Adj Net Sales vs the monthly plan. Below the bar, daily detail collapsed in an accordion: Day, Actual, % of MTD, Δ vs plan, share-of-MTD bar |
| 03 | Marketing efficiency | `kpi-grid c4` | Ad spend, Blended CAC, LTV, LTV:CAC — with `.src` source tags |
| 04 | Onsite traffic | `kpi-grid c4` + `callout` | Pixel sessions, pixel CVR, rev/session, bounce — all current-year. The callout carries the **GA4 YoY** (§8) |
| 05 | Demand by sales channel | `split`: donut + panel | Donut of Adj Demand $ by `custom_5794`, anything **< $500 → Other**. Right panel: app share % plus an App-vs-Web table (Adj AOV, Adj UPT, new customer rate, return customer rate) |
| 06 | Sales by method | table + `ibar` | Adj Demand $ and units by method. **Excl. OP. Bundle Builder from raw** (§3a). Total row = "Merchandise total" |
| 07 | Division selling | table + `ibar` | Adj Demand $, % rev, units, orders by raw `product_division`. **Excl. OP.** Merge `Women`/`WOMEN`; blank → "No division assigned" |
| 08 | Top 10 styles | `prod-grid` | Rank, product image, title, type, net units, Adj Demand $ and % — images inlined as data URIs (§9) |
| 10 | Traffic by PSD channel group | table + `ibar` | Channel group, sessions, share, volume bar, Adj Demand $, share $, orders, CVR, rev/session. **True Direct and Dark Social are indented sub-rows *under* Direct** (subsets, share = % of Direct sessions), not peers. Add the "Not attributed" row when the residual is non-zero |

**App share means Mobile App (Tapcart) only.** Shop App is a separate channel and stays out of it.

**Every mix must reconcile.** §5, §6, §7 each tie to their stated total in dollars and units. §6/§7
tie to the ex-OP total; §5 ties to full Adjusted Demand $. Compute this in code, not by eye — an
unreconciled mix is the clearest signal that a filter did something you didn't intend.

---

## 6. Visual conventions

House style is locked. **Never author CSS, the header or the footer** — the assembler injects them.

- Delta chips: `.delta.p` positive, `.delta.n` negative, `.delta.z` neutral/no-comp. Direction of
  "good" is metric-dependent — CAC down is good.
- Chips carry **comparisons only**. Never put process commentary ("verified at line level") in a
  delta slot. No comp available reads `≈ no LY comp`.
- Bars encode magnitude and must be scaled to something stated in the header ("% of MTD", "Volume").
  A bar whose basis isn't obvious is noise — drop it.
- Parent rows carry the volume bar; sub-rows leave it blank.
- Keep `{{token}}` values free of double quotes.

---

## 7. Executive summary rules

Written for a reader who has seen nothing else — an exec skimming the PDF on a phone. Never assume
they've read the report below.

1. **Sentence 1 — where the day landed.** Channel, date, headline metric in absolute dollars, both
   comps.
2. **Sentence 2 — the cause, with arithmetic that ties.** Name the driver, give both sides of the
   number, and say how much of the gap it explains.
3. **Sentence 3 — the counterweight.** What held or improved, so the read is balanced, not alarmist.
4. **Sentence 4 — one forward-looking number.** MTD pace or plan attainment. Nothing else.
5. **Limits:** 4 sentences, ~110 words. Every claim carries a number *and* its comparison basis.
6. **Order is fixed: outcome → cause → counterweight → pace.** Leading with the diagnosis assumes
   knowledge the reader doesn't have.
7. **Assert cause only when the arithmetic supports it.** If the driver doesn't reconcile to the gap,
   write "coincides with", not "because". A single-day correlation is not a finding.
8. **No jargon, no metric keys, no methodology, no recommendations.** Those live in the footer and
   the run commentary (§11).
9. **Bold exactly two things:** the outcome and the driver.

**Worked example** (Aug 11 2026, PSD Web):

> PSD Web closed Tuesday Aug 11 at **$71.6K Adjusted Net Sales — down 20.0% from Monday and 2.8%
> below last year**, while Adjusted Demand of $89.5K slipped only 3.3% day-over-day and ran 16.4%
> ahead of last year. The gap is **returns processed: $18.1K against $3.3K on Monday**, a $14.8K
> swing that accounts for roughly 83% of the $17.9K net-sales decline — gross sales were down just
> 3.2% and discounting was flat. Demand quality held: AOV $82.35 (+14.0% YoY) and UPT 3.37 (+11.9%
> YoY) both improved, with 1,090 orders up 2.3% on the year. August is 66% to the $3.5M month plan at
> day 11 of 31.

Note what makes it work: the reader learns the outcome before the explanation, the $14.8K swing is
shown to explain 83% of a $17.9K decline (so "the gap is" is earned, not asserted), and the
counterweight prevents a returns-timing artifact from reading as a business collapse.

---

## 8. Onsite traffic YoY — the pixel has no last year

The Polar pixel wasn't live a year ago, so pixel sessions/CVR have no YoY comp. **Do not cross
pixel-current-year against GA4-last-year** — the two count sessions differently (bot filtering,
session windowing, consent) and routinely sit 10–30% apart, so the "delta" would be measuring the
instrumentation, not the business.

Instead:
- Headline current-year onsite numbers come from the **pixel**, which ties to the channel-group
  section and to orders.
- The YoY trend comes from **GA4 on both sides** (GA4 CY vs GA4 LY), labelled as GA4, in the callout.
- Never put a pixel-vs-GA number in one delta cell.

Revisit once ≥12 months of pixel history exists, then move to pixel-on-pixel YoY.

---

## 9. Build

1. **Shared assets** live in `${CLAUDE_PLUGIN_ROOT}/shared/` — `assemble_report.py`, `report.css`,
   `report-shell.html`, and `report-template.html` (the component pick-list). Use those paths; do
   not guess at `.remote-plugins/*` or `~/.claude/plugins/*`.
2. **Write only a body fragment and a `tokens.json`.** Compute every number in code — percentages,
   deltas, pacing, bar widths, donut dash arrays. Never arithmetic by hand.
3. **Inline product images as data URIs** when the image CDN is reachable. Fetch each top-10
   product image and base64-embed it — remote `<img>` URLs break in the PDF and a report full of
   broken image icons reads as a broken report.
   **In practice `cdn.shopify.com` has been unreachable from the sandbox on every run to date.**
   Test it once with a HEAD request; if it fails, render the `prod-grid` placeholder tiles, say so
   in `METHOD_NOTES`, and move on. Do not spend the run retrying, and do not leave live remote URLs
   in the HTML as a fallback.
4. **Assemble** (per run-protocol §4):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/shared/assemble_report.py \
     --css   ${CLAUDE_PLUGIN_ROOT}/shared/report.css \
     --shell ${CLAUDE_PLUGIN_ROOT}/shared/report-shell.html \
     --body  body.html --tokens tokens.json \
     --out   ecom-web-daily-flash-YYYY-MM-DD.html
   ```
   Filename carries the **report date**. Assembly fails closed on any unfilled `{{token}}`.
5. **Tokens:** `REPORT_TITLE` (e.g. `PSD WEB`), `ACCENT_WORD` = `· <MON D, YYYY>` of the **report
   date** (not the run date), `REPORT_KICKER`, `AGENT_NAME` = `Biz Flash Agent`, `DATE_UPDATED` =
   `ran <Mon D YYYY>, <h:MM AM/PM> PT` (actual run time, Pacific), `WINDOW`, `WINDOW_DAYS`,
   `COMP_WINDOW`, `COMP_DAYS`, `SCOPE`, `SOURCE`, `HEADLINE_METRICS` (4 `.hmetric` cells),
   `DATA_COVERAGE`, `METHOD_NOTES`, `FILENAME` (the output filename itself, e.g.
   `ecom-web-daily-flash-2026-08-26.html` — there is no repo path here).
   `METHOD_NOTES` is where methodology belongs — comparison bases, the OP exclusion, the raw bundle
   rule, and the pacing approximation. Keeping it there is what lets the body stay clean.
6. **PDF** — render the assembled HTML per **run-protocol §4**: headless Chromium (not WeasyPrint),
   one continuous page. Render at 1200px width, measure `document.documentElement.scrollHeight`, and
   emit a single page that tall — `page.pdf(width='1200px', height=f'{h}px', print_background=True,
   margin={'top':'0','right':'0','bottom':'0','left':'0'})`. `print_background=True` is what keeps
   the hero dark instead of pink. **Before rendering, force the §02 MTD `<details>` accordion OPEN**
   (add the `open` attribute, or flatten it to a plain block) so the daily detail isn't hidden —
   content that exists only in the PDF must be visible. Verify the PDF is non-empty.

---

## 10. QA before delivering

- No `{{token}}` anywhere.
- Every table: header cell count == cells per body row (parent/child rows in §10 legitimately differ).
- **Mixes reconcile in dollars and units** — §5 to Adjusted Demand $, §6/§7 to the ex-OP total.
  This is the single most important check.
- LTV lands in the ~$103–105 range.
- Deltas and pacing recomputed in code, never by hand.
- Delta chips carry comparisons only.
- Shares total ~100%; the channel-group residual row appears when non-zero.
- Title date = **report date**; `DATE_UPDATED` = actual run time in Pacific.
- Render the PNG and actually look at it: hero dark (not pink), KPI grids 4-across, no broken image
  icons, tables unclipped, bars sane, and the §02 accordion showing expanded in the PDF.

---

## 11. Deliver

There is exactly one delivery mode: **hand back the files.** No mode table, no publish decision, no
opt-in. Every successful run produces the same two artifacts.

### What every run outputs

| Artifact | Name | Notes |
|---|---|---|
| HTML dashboard | `ecom-web-daily-flash-<YYYY-MM-DD>.html` | self-contained, opens in any browser |
| PDF | `ecom-web-daily-flash-<YYYY-MM-DD>.pdf` | single long page, rendered per run-protocol §4 (headless Chromium) |

Both filenames carry the **report date**, not the run date.

Deliver both files into the conversation so they are downloadable, then write a short commentary:

1. **Freshness verdict** — one line. Connector health, the Shopify sync cut-off, and the ShopifyQL
   day-shape cross-check.
2. **The headline read** — the executive summary's substance, plus anything a reader of the report
   would miss.
3. **Reconciliation result** — state that the mixes tied in dollars and units, or exactly which one
   didn't and by how much.
4. **Caveats worth acting on** — data caveats (an unattributed residual, a metric that fell back to
   a secondary method, an unreachable image CDN) and business caveats (an efficiency threshold
   crossed, a comparison basis that flatters or punishes the day).

Do **not** paste the whole report into the message. The files are the report.

### Running unattended on a schedule

A scheduled run has nobody to ask, so:

- **Never ask a clarifying question.** Default to `channel = web` and `report_date = yesterday (T-1)`
  in the runner's timezone unless the task prompt says otherwise. State the assumption in the
  commentary.
- **Never skip the freshness gate to save time.** It is the only thing standing between a sync gap
  and a confident-looking wrong number.
- **Never partially render.** If one section's query fails, either render that section with an
  explicit "data unavailable for this run" note *and* flag it at the top of the commentary, or
  withhold the whole report. Silently omitting a section is the one unacceptable outcome, because
  the report looks complete.
- **Re-running a date is normal operation, not an error.** Polar figures move for 24–48 hours after
  a day closes, so a later run of the same date will differ. Nothing is overwritten anywhere, so
  just build it again and say which run is newer.

### If the freshness gate fails

Produce **no report**. Output a withheld notice instead:

```
DAILY FLASH WITHHELD — PSD <channel> — <report date>

Reason:    <one line: what looked wrong>
Evidence:  <the specific numbers — connector status, integrity-report failed dates,
            the Polar-vs-ShopifyQL shape gap>
Expected:  <when the data should be settled enough to re-run>
```

Name the evidence, never just the conclusion. "Polar shows −34% YoY while ShopifyQL shows −6% for
the same day; the integrity report lists 2026-08-18 with 46.6% of orders missing" is actionable.
"Data looked wrong" is not.

### What this skill must never do

- Clone, commit, or push to any git repository.
- Write to `reports.psd.com`, Vercel, or any hosting target.
- Call Resend or any email API, or read `recipients.json`.
- Accept, store, or ask for a GitHub PAT, a Resend key, or any publishing credential.
- Emit a `summary.json` — it existed only to trigger a publishing Action.

If a run seems to need any of those, stop and say so rather than improvising a publish path.
Publishing is intentionally not part of this skill.

---

## 12. Known gaps

- **No daily plan curve yet.** The plan is monthly, so pace-to-date is a flat proration and is
  labelled as an approximation. Promo events front-load months, which makes flat proration
  misleading early in the month. Replacing the monthly goal with a daily curve is the single
  biggest accuracy improvement available.
- **TikTok configuration is unvalidated** (§1). The view ID is known; the metric keys, method and
  division dimensions and applicable sections are not. Do a discovery pass before its first run
  (it will ship as `/ecom-tiktok-daily-flash`).
- **App-share day/YoY comps** are not wired.
- **Product images have not successfully inlined on any run to date** — `cdn.shopify.com` is
  unreachable from the sandbox, so §08 renders placeholder tiles (§9 step 3).
- **Onsite YoY comes from GA4**, not the Polar pixel, because the pixel wasn't live a year ago.
  Revisit once there are 12 months of pixel history, then move to pixel-on-pixel YoY.
- **The channel-group dollar residual can go either way.** It has been observed both positive
  (demand not yet attributed) and negative (rows over-summing headline demand by ~0.4%, an
  attribution overlap). Compute it, render it honestly, and never normalize it away — see §3c.5.
