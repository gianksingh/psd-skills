# PSD Sale-Event Recap — Report Build Spec

**Version:** 1.0 · Draft for review (precursor to a `/sale-recap` skill — do **not** convert to a skill yet)
**Purpose:** Produce a single-page executive recap of a PSD sale event, uniform in **data rules, comparison logic, structure, and styling** to the July 4th 2026 recap. Output is an in-chat HTML dashboard **plus** an A4-landscape PDF. No GitHub, no Asana, no publishing pipeline for now.

Reference build: `manager-july4-sale-recap-2026-07-07.html` (Jun 30 – Jul 5 2026 vs LY Jul 1–6 2025).

**Companion files:**
- **`PSD-Sale-Recap-Template.html`** — the canonical, locked stylesheet + component library. Copy its CSS verbatim and its component markup with `{{PLACEHOLDER}}` tokens (see §7). This is what guarantees visual parity across runs.
- `manager-july4-sale-recap-2026-07-07.html` / `.pdf` — the reference build, as a filled-in worked example.

---

## 0. How to use this doc

Every run has three phases:

1. **Intake** — ask the questions in §1 and wait for answers before pulling data. Never assume dates, comparison basis, which mechanics ran, or that a data source exists.
2. **Build** — pull data per §2–§6, assemble the HTML per §7–§8, integrity-check per §9.
3. **Deliver** — QA per §10, generate HTML + PDF per §11, present both in chat.

---

## 1. Intake — always ask first

Open every run by collecting these. Ask them as a short batch; do not proceed on assumptions.

**A. Dates & comparison (required)**
- Sale **start and end date** (current year).
- **Comparison** start and end date (prior-year event, or whatever baseline they want).
- **Nature of the comparison** — clarify explicitly:
  - Is it **exact sale dates vs exact sale dates**, or is there **overlap / asymmetry** (e.g., one year ran more days, a pre-sale BAU ramp day, a VIP early-access window, a different weekday alignment)?
  - If day counts differ, ask how to handle it (see §3): pad the shorter period with an adjacent BAU day to match day-count, compare sale-days-only, or report both.
  - Confirm whether **any adjustment to what's being compared** is needed (exclude VIP early access, isolate sale SKUs, etc.).

**B. Event mechanics (required — drives which sections render)**
Ask which of these ran, so conditional sections are included only when real:
- Build-Your-Own-Bundle (BYOB)?
- Post-purchase upsell funnels (AfterSell) and/or a **specific sale offer** (e.g., a "Mystery" offer) to drill into?
- Rokt Thanks Network (post-purchase ad monetization)?
- Order protection?
- A dedicated **sale collection** structure (for the sale-page CVR section)?
- **Anything else** — any other datasets, offers, or metrics run for this event that should be accounted for.

**C. Non-Polar inputs (required — request explicitly)**
Several sections depend on data **not in Polar**. When a requested/needed section relies on an external source, **explicitly tell the user what's needed and ask them to provide it** (CSV export, screenshot, dashboard image). Known external dependencies:
- **AfterSell all-funnels metrics** (§6.8a) — screenshot/export of the AfterSell dashboard for the event window.
- **AfterSell specific-offer metrics** (§6.8a drill-down) — the offer's revenue / accepts / impressions / rev-per-visit.
- **Rokt Thanks Network** (§6.8b) — Rokt "Network Analytics" screenshot (revenue, transactions, RPT, impressions, referrals, verticals table).
- **App push performance** (§6.2 note / §6.10 risk) — Tapcart push campaign screenshot (sends, orders, revenue), because push is under-attributed in Polar.

> **Do not silently omit a section.** If a needed input is missing, say: *"I need X to build section Y — please upload it, or tell me to skip Y."* Only drop a section if the user explicitly says so or confirms the mechanic didn't run.

---

## 2. Scope & data-source rules

- **Source of truth: Polar Analytics.** Pull all quantitative data from Polar unless a metric only exists in an external tool (then request it per §1C).
- **View:** PSD Web business channel — `views: ["31552-mpfv58vy"]`.
- **Fresh context each run:** call `get_context` at the start of the session to obtain a working `conversation_id`; reuse it for all `generate_report` calls in that run.
- **DTC scope / exclusions (default):** the PSD Web view already scopes DTC. Additionally, unless a specific run says otherwise, **exclude sales channels containing `tiktok` or `aftersell`** (TikTok Shop business unit) and **exclude `Amazon`** (marketplace). TikTok Shop / Amazon are reported only when explicitly requested for that run.
- **Comparison mechanic:** for YoY/period comps use `comparisonPeriod: "range"` with `comparisonDateRangeFrom` / `comparisonDateRangeTo`. Do **not** rely on `previousYear` when the comparison window is offset from the current window (it is, whenever day-counts are padded).
- **Discrepancy handling — never fabricate.** If a Polar figure conflicts with a user-supplied number, use the **Polar figure**, keep the report internally consistent, and **flag the discrepancy** to the user with the offer to switch (with a source note) if theirs comes from a specific dashboard with a different definition. (Precedent: app sessions were −41.7% in Polar vs a "28%" figure supplied verbally; the report used −41.7% and flagged it.)
- **Pixel history:** Polar Pixel was not live before ~2026, so **YoY onsite/funnel comparisons use GA4** (`ga_main.raw.sessions`) rather than pixel. State this in the funnel note and footer.

---

## 3. Window & comparison logic

- **Leading comp = full period (CY) vs full comparison period.** Headline KPIs and the daily chart use the full windows the user provides.
- **Day-count asymmetry** (e.g., 5 sale days this year vs 6 last year) is handled by whatever the user chose in §1A. The July 4th precedent was: **pad the current period with the adjacent pre-sale BAU day** to match LY's day count, report the padded full-period comp as the headline, and report a **sale-day daily-average** (excluding the BAU day) as the secondary read. This is **not automatic** — confirm per event.
- **Always include a method note** (in the exec summary and/or footer) stating the exact comparison basis, any padding, and any known tracking caveats for the window (e.g., a CMP/consent migration that dented tracking on specific dates).
- **Leading revenue metric = Adjusted Demand $ (`custom_64021`)** unless the run specifies otherwise. Adjusted Net Sales is the secondary revenue line.

---

## 4. Metric & dimension registry

**Defaults below. At run start, verify keys via `get_metrics` (sourceList `custom-metrics`, connector names as needed). If a key has moved, re-resolve by its label. The user may request or substitute metrics for a given run.**

### Core sales metrics
| Metric | Key |
|---|---|
| **Adjusted Demand $** (leading) | `custom_64021` |
| Adjusted Net Sales | `custom_60202` |
| Adjusted AOV | `custom_60207` |
| Adjusted Units | `custom_60206` |
| Adjusted UPT | `custom_60208` |
| Orders | `shopify_sales_main.raw.total_orders` |
| Gross margin | `shopify_sales_main.computed.gross_margin` |
| Total customers | `shopify_sales_main.raw.total_customers` |
| Repeat customers | `shopify_sales_main.raw.repeat_customers` |

- **% New customers** = `(total_customers − repeat_customers) / total_customers`.

### Onsite pixel (2026-on; no LY)
| Metric | Key |
|---|---|
| Sessions | `shopify_attribution_pixel.raw.polar_pixel_sessions` |
| Product viewed (sessions) | `shopify_attribution_pixel.raw.polar_pixel_funnel_product_viewed_sessions` |
| Added to cart (sessions) | `shopify_attribution_pixel.raw.polar_pixel_funnel_product_added_to_cart_sessions` |
| Checkout started (sessions) | `shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_started_sessions` |
| Checkout completed (sessions) | `shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_completed_sessions` |
| Onsite CVR | `shopify_attribution_pixel.computed.polar_pixel_conversion_rate` |
| Bounce rate | `shopify_attribution_pixel.computed.polar_pixel_session_bounce_rate` |

### YoY traffic & app
| Metric | Key |
|---|---|
| GA4 sessions (YoY source) | `ga_main.raw.sessions` |
| Tapcart app sessions | `generated_root_tapcart.raw.sessions` |
| Tapcart session CVR | `generated_root_tapcart.computed.session_cvr` |

### Order protection
| Metric | Key |
|---|---|
| Attach rate | `custom_61578` |
| OP gross sales | `custom_62988` |
| OP net sales | `custom_62987` |
| Est. rev share | `custom_62989` |

### Dimensions
| Dimension | Key | Use |
|---|---|---|
| Sales channel | `sales_channel_name` | App vs Web split; per-channel Adj Demand $ |
| Landing Page Type (PSD) | `custom_6294` | 7-type landing breakdown (100% coverage) |
| Direct Traffic Segmentation | `custom_5987` | Split Direct → True Direct vs Misattributed/dark-social |
| PSD Custom Channel Grouping | `custom_5984` | Traffic-by-channel table (non-direct channels) |
| Bundle vs Non-Bundle | `custom_5509` | BYOB isolation (`IS "Bundle"`) |
| BYOB Bundle Pack Size | `custom_6023` | Pack-mix breakdown |
| Landing page path (raw) | `landing_page_path` | Sale-page CVR (`CONTAINS "/collections/sale"`), builder page |

**Dimension notes:** rules evaluate in **first-match order** — check specific URL patterns (`/products/`) before broad ones (`/collections/`) to avoid double-counting. For full-coverage categorical breakdowns, **create/keep a custom dimension and group by it** rather than pulling raw rows and bucketing client-side (more accurate; e.g., surfaced PDPs = ~24% of entry sessions vs. an undercount from sampling).

---

## 5. Report structure

Fixed order, numbered `01`–`NN`. Renumber sequentially if a conditional section is dropped.

| # | Section | Render when |
|---|---|---|
| 01 | Overview & Daily Performance | Always |
| 02 | App vs Web Performance | Always (if app channel exists) |
| 03 | Traffic to Site by Channel | Always |
| 04 | Onsite Funnel | Always |
| 05 | Landing Pages — by Type | Always |
| 06 | Conversion Rate by Sale Page | If a sale collection structure ran (usual) |
| 07 | Build-Your-Own-Bundle (BYOB) | If BYOB ran |
| 08 | Aftersell & Rokt | If AfterSell and/or Rokt ran (needs external inputs) |
| 09 | Order Protection | If order protection ran |
| 10 | Wins & Risks | Always |
| 11 | Key Learning for Next Event | Always |

Hero + Executive Summary always precede §01.

---

## 6. Per-section spec

**Hero** — full-bleed black (`--ink`) with red+purple radial glows and a red→purple flagstrip. Brandmark = white PSD logo (`https://www.psd.com/cdn/shop/files/logo-white_a1a0e905-e6cb-408b-a6a3-906e6a371a3c.png`) + divider + "EVENT POST-MORTEM · PSD WEB". Byline right: "Prepared by Growth Agent · {date updated}". Title: "{EVENT} RECAP" with the second word in `--lime`. Period pills (report window, comp window, scope, source). Headline metric row (4): **Adj Demand $, Adj Net Sales, Adj AOV, Sessions** — each with YoY delta.

**Executive Summary** — one tight paragraph. State the core narrative (what drove the number — volume vs AOV vs mix), the leading full-period comp, and the secondary sale-day read if day-counts were padded. Keep it concise; tie every later section back to this thesis.

**01 Overview & Daily Performance** — KPI grid: Adj Demand $, Adj Net Sales, Orders, Adj AOV, Adj Units, Adj UPT, % New Customers, Total Customers (each with per-day sub where useful + YoY delta). Daily chart: grouped bars, **current year (colored) + prior year (gray, positionally aligned)**, value labels on **both** series (~10.5px), legend, and a callout with the finish/finale and sale-day daily-avg read.

**02 App vs Web** — 4 KPI cards (Web Adj Demand $, App Adj Demand $, Web AOV, App AOV) + two side-by-side tables (Web / App) each with rows: **Adj Demand $, Net sales, Orders, AOV, Units, Sessions, Conversion rate**. Web sessions/CVR = pixel (LY = n/a, noted); App = Tapcart (real YoY). Read callout including the push note if provided.

**03 Traffic to Site by Channel** — one table: Channel · Sessions · Share · volume bar · Onsite CVR. Build channels from `custom_5984`, replace its "Direct" with the `custom_5987` split (True Direct + Misattributed/dark-social). Bars scaled to top channel. Callout on largest low-CVR pool and under-fed high-CVR channels.

**04 Onsite Funnel** — 5-step session funnel (Sessions → Viewed → ATC → Checkout started → Completed) with bars **scaled to true value** (no min-width flooring that collapses small steps). YoY note uses GA4 sessions + the value/volume framing.

**05 Landing Pages — by Type** — table over `custom_6294` (7 types): Page type · Sessions · Share · volume bar · CVR. Callout on the recoverable PLP pool and PDP entry share. (No "top individual pages" table — keep it type-level and concise.)

**06 Conversion Rate by Sale Page** — dual-metric table: Sale page · Sessions · **Volume bar** (scaled to biggest) · CVR · **CVR bar** (scaled to best converter, colored by performance). Shows the volume-vs-conversion tension (generic hub owns traffic, converts worst; segmented pages convert best).

**07 BYOB** — vs-PY table (Adj Demand $, Net sales, Share of DTC, orders, units/order). 50:50 split: small donut (Web vs App, ~160px viewBox) + pack-size mix bars. Builder-paradox callout (bundle-builder page sessions / CVR / bounce). Isolate BYOB via `custom_5509 IS "Bundle"`; pack mix via `custom_6023`.

**08 Aftersell & Rokt** — two sub-sections:
- **8a Post-Purchase Upsell** — lead with **all-funnels** AfterSell metrics (Revenue, Conversion rate, Accepted offers, Impressions, Rev/visit 1-click + TY, Avg upsell value), then a **drill-down panel** (red left border) for any **event-specific offer** (e.g., Mystery), showing its revenue / accept rate / accepts / impressions and its share of the funnel. Include the storefront reconciliation note if the offer's units also land in Shopify as organic PDP demand. (All from user-provided AfterSell data.)
- **8b Rokt Thanks Network** — cards (Revenue, Transactions, RPT, Impressions) + verticals table (Referrals / Impressions / Referral rate). Frame as incremental ad revenue, not storefront sales. (From user-provided Rokt screenshot.)

**09 Order Protection** — 4 cards (Attach Rate, OP Gross, OP Net, Est. Rev Share) + daily attach-rate line chart.

**10 Wins & Risks** — 2 columns. 3–4 wins, 3–4 risks, each a bordered card with a headline, a metric chip, and one tight sentence tying to a driver (volume / CVR / AOV / mix / spend / traffic quality / inventory / deliverability). Include tracking/method caveats as risks where relevant.

**11 Key Learning for Next Event** — priority table: Priority (P0/P1/P2) · Owner (Ads/Email/CRO/Merch/Pricing/Growth/Data) · What to do · Impact metric. 5–7 rows. Impact-metric column stays uniform (metric name only, no inline targets).

**Footer** — data coverage (sources, scope, comparison basis, leading metric), method notes (padding, tracking caveats, pixel-vs-GA4, dimension definitions, external-source caveats), and a generation byline.

---

## 7. Styling & layout conventions

> **Canonical asset — start here, don't rebuild from prose.** The file **`PSD-Sale-Recap-Template.html`** is the locked stylesheet + component library. Every run: copy its `<style>` block **verbatim** (never re-derive the CSS), and copy each component's exact markup from its gallery, replacing `{{PLACEHOLDER}}` tokens with run data. The tables and hex values below are a human-readable index of what's in that file — the template is the source of truth for parity. Update the template and this section together if the design ever changes.

### Brand palette (CSS `:root`)
```
--ink:#161616;  --ink2:#333333;  --muted:#777777;  --paper:#F7F7F7;  --card:#FFFFFF;
--line:#E7E7E7; --line2:#DADADA;
--red:#E31C3D;  --purple:#9C00FF; --lime:#CCFF00;      /* accents */
--pos:#2E9E63;  --pos-fill:#6FCF97;                     /* positive text / fills */
--neg:#EB5757;                                          /* negative */
--warn:#EDB902;                                         /* warning / NEUTRAL-FLAT comps */
/* washes */ --wash-red:#FCE7EA; --wash-purple:#F3E6FF; --wash-pos:#EAF7EF; --wash-neg:#FDECEC;
```
Role guide: **red** = brand / primary bars / section numbers; **purple** = secondary series / app / P1 / chart accents; **lime** = hero pop only (illegible as text on white); **green** positive, **red** negative, **amber #EDB902** neutral/flat.

### Delta chips
- Positive → `.p` : `color:#2E9E63; background:#EAF7EF`
- Negative → `.n` : `color:#EB5757; background:#FDECEC`
- Neutral/flat → `.z` : **`color:#EDB902; background:#FBF4D8`** (also used for the hero "≈ flat" comp)

### Layout & type
- Container max-width ~1120px, padding `0 22px`. Sans-serif system stack; `Arial Black` for display/headlines; tabular numerals (`.mono`) for all figures.
- Section header: number in `--red` + bold title + right-aligned tag, on a 2px `--ink` bottom rule.
- **Section intro (`.lead`) runs full width** (no max-width cap).
- Cards/panels: white, 1px `--line`, ~14–16px radius, soft shadow. KPI grid = 4 columns (wraps below 900px).
- Formatting discipline: concise commentary, minimal decoration, every callout tied to the core narrative.

### Chart conventions (inline SVG)
- **Daily bars:** grouped CY + PY; CY colored (BAU day a lighter tint, finale/peak in purple), PY in `#D5D5D5`; value labels on both series (~10.5px, CY bold dark, PY `#8A8A8A`); legend.
- **Funnel:** horizontal fills scaled to true value; small steps keep a ~3px min so they stay visible but still differ; labels outside the bar for narrow steps.
- **Donut:** ~150–160px viewBox, `stroke-dasharray` arcs, center total label; red/purple segments.
- **Line (e.g., attach rate):** polyline + light area fill + point labels; y-scale chosen to show real variation honestly (don't exaggerate a flat series).
- Volume/ratio table bars: `.ibar` scaled to the max in the column; color-code ratio bars by performance where it aids reading.

---

## 8. Data-integrity rules

- **Match numerator & denominator** before surfacing any derived metric (e.g., don't divide a bundle-line revenue by all-order counts). Drop derived metrics that can't be cleanly matched.
- **First-match dimension ordering** for URL-based custom dimensions (specific before broad).
- **Full-coverage breakdowns** via a custom dimension + single grouped report, not client-side bucketing of sampled rows.
- **Polar is source of truth**; on conflict with a user figure, use Polar and flag (see §2). Never invent numbers to match an expectation.
- When correcting an error, **rebuild the affected component fully** rather than patching one value in place.
- Round consistently (K for thousands, one decimal on percentages/AOV) and keep a figure's basis labeled where two sources coexist (e.g., "Sessions (pixel)" vs "Sessions (GA4)").

---

## 9. QA checklist (before delivery)

1. **Tag balance** — every `section/div/table/tbody/thead/tr/td/th/svg` opens and closes evenly.
2. **Section order** — numbers are sequential `01…NN` and match the intended set (conditional sections correctly included/dropped and renumbered).
3. **Removed/renamed content** — confirm no leftover strings from prior events.
4. **Visual render** — rasterize the HTML (e.g., `wkhtmltoimage --enable-local-file-access --width 1200`) and eyeball the hero, KPI grids, each chart, and each table. (Grids stack in that old-WebKit preview — that's expected; they render multi-column in a real browser and in the Chromium PDF.)
5. **Numbers reconcile** — shares sum to ~100%, YoY deltas match the pulled values, funnel steps descend, CVR = completed/sessions.

---

## 10. Output & delivery

- **Always produce both:** the HTML dashboard **and** an **A4-landscape PDF**.
- **In-chat only** for now — present both files. **No GitHub push, no repo/index linking, no Asana tasks, no `/logs` writes.**
- **File naming:** `manager-{event-handle}-recap-YYYY-MM-DD.html` / `.pdf` (creation date in the filename; "updated" date in the byline).

---

## 11. PDF generation — two outputs

Render with **headless Chromium** (do **not** use wkhtmltopdf for the deliverable —
its old WebKit stacks grids). Produce **two** PDFs from the same HTML. Both start
with the same logo swap: in a PDF-source copy, replace the remote logo `<img>` with
a white text wordmark (psd.com is outside the sandbox allowlist and renders broken):
`<span style="font-family:'Arial Black',sans-serif;font-weight:900;font-size:20px;letter-spacing:.02em;color:#fff">PSD</span>`
(The delivered **HTML keeps the real logo URL** — it loads in the user's browser.)

Launch:
```
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers
chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
```

**(a) Document PDF — single continuous page (primary deliverable, no page breaks).**
This is the fix for pagination gaps: one tall page matching the single-page
dashboard.
```
page.set_viewport_size({'width':1200,'height':900})
page.goto(<pdfsrc file:// URI>, wait_until='networkidle')
h = page.evaluate("document.documentElement.scrollHeight")
page.pdf(width='1200px', height=f'{h}px', print_background=True,
         margin={'top':'0','right':'0','bottom':'0','left':'0'})
```
File: `ecom-sale-recap-{event-handle}-YYYY-MM-DD.pdf`. The `.wrap` 22px padding
supplies the visual margin.

**(b) Deck PDF — 16:9 slides (for screensharing).** One section per slide; the
template's print CSS turns the hero into slide 1 and each `<section>` into a slide
when `body.mode-deck` is set.
```
page.evaluate("document.body.classList.add('mode-deck')")
page.pdf(width='13.333in', height='7.5in', landscape=True, print_background=True,
         margin={'top':'0','right':'0','bottom':'0','left':'0'})
```
File: `ecom-sale-recap-{event-handle}-deck-YYYY-MM-DD.pdf`. For clean slides, the
report body must group content into `<section>` blocks per §5.

**Print CSS lives in the template** (`@media print`): color-exact; atomic blocks
(`.kpi/.item/.actrow/svg/tr`) stay whole so charts/cards/rows never split, while
panels and tables flow to fill the page; deck rules gate on `body.mode-deck`.

**Verify** both: rasterize a few pages (`pdftoppm -png -r 80`) to confirm the
wordmark (not a broken image), multi-column layout, chart rendering, and — for the
deck — that each section fills its slide without clipping; nudge the deck block's
section `min-height`/`font-size` if a slide is sparse or overflows.

## 12. Known event-specific items (not standing rules)

These were true for July 4th 2026 and must be re-confirmed, not assumed:
- Padding the CY window with the Jun 30 BAU day to match LY's 6 days.
- The CMP migration (Consentmo → Pandectes) tracking caveat for Jun 29 – Jul 2.
- The specific offer drilled into (Mystery Style 2-Pack) and its ~$14.8K-in-Shopify reconciliation.
- App push being under-attributed in Polar (verify the current Tapcart attribution state each run).
