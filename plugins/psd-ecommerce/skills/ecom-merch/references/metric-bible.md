# Ecom Merch Weekly: Metric Bible

Version 1.4 (2026-10-07). Validated against Polar using the week of Mon 9/28/26 to Sun 10/4/26.
Changes in 1.1: bot sessions are included to match the Daily Flash, every page shows landed and visited sessions, featured collections are inferred from traffic unless Jamie lists them, and post-purchase uses the AfterSell order browser.
Changes in 1.2: post-purchase eligibility is measured against Online Store orders (TikTok Shop, Tapcart and Shop App shown as a separate step); per-funnel AfterSell results are a manual input.
Changes in 1.3: top products (M19), onsite search (M20), app line on the summary (M21) and the conditional new-drop slide (M22).
Changes in 1.4: top products shown as a visual grid with thumbnails and cells highlighted against the pool median; product signals slide (M19b); zero-result search terms on the search slide.
Every run follows this file exactly. If a definition below can't be produced, the run flags the slide. It does not substitute another metric.

## 0. Global settings (apply to every Polar query unless a row says otherwise)

| Setting | Value |
| --- | --- |
| Workspace | PSD (timezone America/Los_Angeles, week starts Monday) |
| View | `31552-mpfv58vy` **Business Channel – PSD Web** (excludes TikTok Shop and POS via `custom_5794`, plus CampMystery discount codes). Wholesale is not a sales channel in this store, so nothing more needs excluding |
| Bot sessions | **Included**, with no `is_bot_session` filter, so sitewide sessions match the Daily Flash. Bots were 5.9% of pixel sessions in the test week, they never convert, and they show up mostly in Direct and Unassigned |
| Comparison windows | WoW = prior Mon–Sun. YoY = 52 weeks back (364 days), Mon–Sun. Pass both as `comparisonPeriod: "range"` with explicit dates. Never use `previousYear` |
| Pixel history | Polar pixel data starts April 2026. Any comparison window before 2026-04-01 uses GA4 on **both** sides (see §4) |
| Change notation | Rates in percentage points ("+2.1 pts"). Counts and dollars in % change ("+14%"). The label always says which |
| Low-confidence | Any rate with a denominator under 100 sessions, or with fewer than 30 conversions in the numerator, is marked "low confidence" |

## 1. Page matching rules (validated, read before any page metric)

Polar pixel has three page fields. They behave differently, and two of them are traps.

| Field | What it does | Use it for |
| --- | --- | --- |
| `page_path` (filter **or** breakdown) | Event-level. Counts sessions correctly (exact path), but **funnel and bounce metrics ignore it** and return sitewide totals | **Session counts and the PLP ranking only.** Never combine it with ATC, product-viewed, checkout or bounce metrics |
| `page_paths_in_session` (filter) | The session's whole path list as one string, separated by `" ; "`. All session-scoped metrics respect it | **Every page-level rate** (ATC rate, PLP→PDP, CVR). Use the exact-match pattern below. A bare `CONTAINS` over-counts: `/collections/mens` matched 35,560 sessions against an exact 22,621 (+57%) because it also catches `mens-packs`, `mens-new-arrival` and the rest |
| `landing_page_path` (filter or breakdown) | First page of the session. Session and funnel metrics respect it; `polar_pixel_pageviews` does not | Landing sessions, bounce, landing-page funnel and CVR |

**Exact-match pattern for `page_paths_in_session`** (path `X`, e.g. `/collections/mens`):

```json
"page_paths_in_session": [
  {"value":["X"],"operator":"IS"},
  {"value":["X ; "],"operator":"CONTAINS"},
  [ {"value":[" ; X"],"operator":"CONTAINS"},
    {"value":[" ; X-"],"operator":"NOTCONTAINS"},
    {"value":[" ; X/"],"operator":"NOTCONTAINS"} ]
]
```

Validated: 22,444 sessions against 22,621 from `page_path IS X` (−0.8%, measured with bots excluded; the pattern behaves the same with bots included). **Reconciliation check every run:** for each page, compare the pattern's session count with `page_path IS X` sessions. If they differ by more than 3%, footnote the row as "approximate page match".

**Landed vs visited (every page slide shows both).** *Landed* = `landing_page_path IS X`: the session started on the page, and it's the only scope with bounce. *Visited* = the exact-match pattern above: the page was viewed at any point in the session. Show sessions, add-to-cart rate and conversion rate for both, side by side.

Homepage: use custom dimension `custom_6843` = "Viewed Homepage" (the same exact-match logic for `/`).

Path hygiene: paths are case-sensitive (`/collections/halloween/Men` and `/collections/halloween/mens` are separate rows). A trailing slash is a separate path (`/pages/bundle-builder/`). Exclude `/products/` from PLP lists (`page_path NOTCONTAINS /products/`). If a page has variant spellings that each carry ≥1% of its sessions, list them in the run log and footnote the row. Don't merge them silently.

## 2. Metric dictionary

Polar metric keys are prefixed `shopify_attribution_pixel.raw.` (pp.raw) or `.computed.` (pp.computed) unless shown in full.

| # | Metric | Deck definition | Source & exact key | Filters | Dimensions | Status / notes |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Sessions (sitewide) | All web storefront sessions (bots included) | Polar `pp.raw.polar_pixel_sessions` | view | none | ✅ Validated. Excludes the Tapcart app (the pixel is web-only) |
| M2 | Sessions (page) | Sessions that viewed the page at any point | Polar `pp.raw.polar_pixel_sessions` | `page_path IS X` (counts) or exact-match pattern (§1) when it sits next to a rate | none | ✅ Validated. Only call it "landing sessions" when the session started on the page |
| M3 | Landing sessions | Sessions whose first page was this page | Polar `pp.raw.polar_pixel_sessions` | `landing_page_path IS X` | none | ✅ Validated |
| M4 | Bounce rate | Landing sessions with a single pageview and no engagement ÷ landing sessions | Polar `pp.raw.polar_pixel_bounced_sessions` ÷ M3 | `landing_page_path IS X` | none | ✅ Landing pages only. Sitewide bounce = `pp.computed.polar_pixel_session_bounce_rate`, labeled "all entry pages" |
| M5 | ATC rate (page) | Share of the page's sessions with an add to cart in the same session | `pp.raw.polar_pixel_funnel_product_added_to_cart_sessions` ÷ M2 | exact-match pattern (§1) | none | ✅ Session-scoped. The ATC can happen before or after the page view (Polar doesn't enforce order). Raw ATC counts are inputs only, never a headline |
| M6 | ATC rate (sitewide) | ATC sessions ÷ sessions | `pp.computed.polar_pixel_funnel_product_added_to_cart_sessions_rate` | view | none | ✅ |
| M7 | Funnel step rate | Step N+1 sessions ÷ step N sessions | Steps: M2 or M3 → `polar_pixel_funnel_product_viewed_sessions` → `…product_added_to_cart_sessions` → `…checkout_started_sessions` → `…checkout_completed_sessions` | same filter at every step | none | ✅ Always drawn as a funnel. Steps are session-scoped and not sequence-enforced, so a later step can occasionally exceed an earlier one (e.g. a quick-add ATC with no PDP view). If that happens, show it and footnote it |
| M8 | Funnel reach | Step N sessions ÷ step 1 sessions | as M7 | as M7 | none | ✅ Labeled "reach" |
| M9 | PLP→PDP | PLP sessions that also viewed any PDP ÷ PLP sessions | `…product_viewed_sessions` ÷ M2 | exact-match pattern | none | ✅ Session-scoped, order not enforced |
| M10 | PDP→ATC (collection) | ATC sessions ÷ product-viewed sessions, within PLP sessions | `…product_added_to_cart_sessions` ÷ `…product_viewed_sessions` | exact-match pattern | none | ✅ Not limited to that collection's products |
| M11 | CVR | Checkout-completed sessions ÷ sessions, same scope | Sitewide `pp.computed.polar_pixel_conversion_rate`; page = `…checkout_completed_sessions` ÷ M2/M3 | scope filter | none | ✅ **Redefined:** "orders ÷ sessions" mixes app and Shop App orders (no pixel sessions) into a web-session denominator. In the test week Shopify had 6,649 PSD Web orders against 3,850 pixel checkout sessions. The deck's CVR is the pixel-to-pixel ratio, scope "web storefront" |
| M12 | Top-10 PLPs | The 10 `/collections/` paths with the most visited sessions, plus landed sessions and landed bounce | `pp.raw.polar_pixel_sessions` by `page_path`; landed from `landing_page_path IS <path>` | `page_path CONTAINS /collections/`, `NOTCONTAINS /products/` | `page_path` | ✅ New entrant = not in the prior week's top 10 (same query, prior week). Names: Shopify collection title when known, otherwise the handle in title case |
| M12b | Featured collections | Top 5 non-core collections by visited sessions, unless Jamie supplies a list | M12 ranking filtered by `config.json` | Excludes the evergreen list, campaign pages and child pages of a picked collection; minimum 1,000 sessions | — | ✅ Rule lives in `config.json`. The slide pill says "Inferred from traffic" or "Jamie's list" |
| M13 | Category engagement (filter) | Sessions on a campaign/shop PLP's category view, shown next to shop-all sessions | M2 on each category path | `page_path IS /collections/<parent>/<tag>` | none | ✅ **Confirm resolved:** PSD category "filters" are **URL path tag segments** (e.g. `/collections/halloween/killer-fits`), not query parameters or events. They're measurable cleanly as pages. Watch for case variants (`/Men` vs `/mens`) |
| M14 | Traffic by source | Sessions by PSD channel group | `pp.raw.polar_pixel_sessions` (+ ATC sessions, checkout sessions) | scope filter | `custom_5984` (PSD Custom Channel Grouping) | ✅ See §3 for email/SMS sends |
| M15 | Module click share | Clicks on a module ÷ total clicks on the page | Clarity Area export (manual): `No. of clicks` ÷ sum of `No. of clicks` | Clarity URL filter as exported | Area | ✅ **Don't use Clarity's "CTR" column**: it's clicks ÷ page views, not click share. The export is mobile only. Unlabeled areas are named from the heat map image in top-to-bottom order |
| M16 | Post-purchase eligibility | Eligible orders ÷ Online Store orders. Funnel steps: all orders (order browser) → Online Store orders → eligible → shown → accepted | Eligible = AfterSell order browser `Eligible`; Online Store orders = Polar `shopify_sales_main.raw.total_orders` by `custom_5794`, **no view** (TikTok Shop sits outside PSD Web) | none (all channels) | `custom_5794` | The order browser total (all channels, incl. TikTok Shop) should match Shopify all-channel orders within ~1%. AfterSell's "Unsupported channel" count matches TikTok Shop only, so Tapcart and Shop App ineligibility is assumed, not shown by AfterSell. The right-hand reasons chart drops "Unsupported channel" and groups reasons under 100 orders. An order can carry several reasons |
| M16b | Per-funnel results | Shown, accepted, revenue per AfterSell funnel | AfterSell analytics export filtered per funnel (manual) | — | funnel | ⚠️ Not in the current export (all funnels combined). Requested at intake; the slide flags it when missing |
| M17 | Acceptance rate | Accepted offers ÷ offers shown | Accepted = AfterSell analytics export (sum of daily `Accepted offers`); shown = order browser `Total offers shown` | — | — | ⚠️ Two AfterSell views. If the order browser revenue differs from the export revenue for the same dates, the run notes it as a contradiction. Never use *Impressions* as offers shown |
| M18 | AfterSell revenue / accepted / avg upsell value | As AfterSell defines them | AfterSell export sheets `Revenue`, `Accepted offers`, `Average upsell value` | — | date | ✅ Week = sum of daily (AUV = revenue ÷ accepted) |
| S1 | Net sales (context) | Adjusted Net Sales | Polar `custom_60202` | view | none | ✅ Same key as the Daily Flash |
| S2 | Orders | Shopify orders | `shopify_sales_main.raw.total_orders` | view | none | ✅ |
| S3 | Units | Adjusted units | `custom_60206` | view | none | ✅ |
| S4 | AOV | Adjusted AOV | `custom_60207` | view | none | ✅ |
| S5 | Collection net sales (secondary column) | Adjusted Net Sales of products that are members of the collection | `custom_60202` | `collection_handle IS <handle>` | none | ✅ Membership-based and not additive across collections. Tag sub-views (`/halloween/killer-fits`) have no handle, so sales are shown at the parent-collection level only |


## 2b. Products, search, app and drops (v1.3)

| # | Metric | Definition | Source / key | Filters | Dims | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| M19 | Top products | Top 10 product × style rows by net units, web only | Units `custom_60206`, net sales `custom_60202`, orders `total_orders` (Shopify via Polar); PDP views `polar_pixel_product_pageviews`, ATC `polar_pixel_add_to_cart`, sessions `polar_pixel_sessions` (pixel) | PSD Web view; `custom_5794 IS Online Store`; `product_title NOTCONTAINS Mystery` | `product_title`, `product_type` | ATC rate = ATC events ÷ PDP views (adds made outside the PDP count, so it can run high). CVR = orders containing the product ÷ sessions with the product. Units WoW shows "new" under 10 prior units. Sell-through and inventory stay in the buyer planner |
| M19b | Product signals | Rule-based flags across the top 40 product × style rows by PDP views (web): HIGH VIEWS · LOW CVR (views ≥ 3× pool median and CVR ≤ 0.5× median), HIGH VIEWS · LOW ATC (500+ views and ATC < 3%), RISER (units ≥ 2× last week, ≥ 30 units, ≥ 10 prior), FALLER (units ≤ 0.6× last week, ≥ 30 prior). Top 8 shown | Polar pixel + Shopify via Polar; inventory = `inventory_quantity` snapshot | Online Store; Mystery and 0-unit virtual bundles excluded | `product_title`, `product_type` | Thresholds live in `config.json` `product_signals`. Inventory is a same-day snapshot, labeled "today". A top-search term in the product title is noted on the card. Each card shows the top 2 entry pages (landing page of sessions that viewed the PDP) and the top traffic source of its PDP views; the page viewed just before the PDP isn't available in Polar |
| M20 | Onsite search | Sessions that viewed /search, their conversion, and non-searcher conversion | Polar pixel sessions + funnel; Searchspring export for terms and zero-result searches | Exact-match `page_paths_in_session` on `/search` | — | Searchspring counts queries and the pixel counts sessions, so the two are never put in one ratio. Top searches show rank only when counts aren't exported. No-results terms come from the Zero Results Searches Breakdown table |
| M21 | App line (summary) | Tapcart orders, share of PSD Web orders, net sales, AOV, WoW | Shopify via Polar | PSD Web view; `custom_5794 IS Mobile App` | — | App orders have no pixel sessions, so no app conversion rate |
| M22 | New drop | Launch-to-date units, net sales, sessions, ATC rate, CVR vs past drops over the same days since launch | Shopify via Polar + Polar pixel | `collection_handle IS <drop>` | — | Runs only when intake lists a drop in the last 14 days |

## 3. Email and SMS sends (Confirm resolved)

- **SMS (Postscript):** Polar carries it. `custom_5984 = SMS` and `utm_campaign` hold the send name and date (e.g. "10.1 - BCA - Keep a Breast 2026 - Engaged Prospects - PS+"). Send list = distinct `utm_campaign` values starting with a date in the window. Postscript isn't connected, so **future** SMS sends must come from Jamie.
- **Email (Klaviyo):** Polar has the channel but **not the send**. Klaviyo `utm_campaign` arrives as the generic "campaign" or "flow". Send list = Klaviyo MCP `get_campaigns` (channel email, status Sent, send_time in the window, converted to PT). Session attribution to a specific email is by landing page + send date only, and is labeled that way.
- Klaviyo transactional flow traffic (e.g. landing on `/pages/track-your-order`) sits in the Email group. Show "Email (campaign landings)" and exclude utility pages from email-driven lift.

## 4. Fallbacks (YoY before April 2026)

| Need | Fallback | Rule |
| --- | --- | --- |
| Sitewide sessions / CVR / ATC YoY | Polar warehoused GA4: `ga_main.raw.sessions`, `ga_main.computed.session_conversion_rate`, `ga_main.raw.ga4_adds_to_cart`, `ga_main.raw.engaged_sessions` | GA4 current week vs GA4 LY week. The Polar pixel current-week value is shown alongside "for reference" |
| Page or landing-page YoY | GA4 direct via Polar `fetch_live_connector_data` (`google-analytics-four`, `report`, dims `landingPage` or `pagePath`) | Polar's warehoused GA4 returns 0 for page-level filters (validated), so go direct. GA4 property timezone is **America/Juneau** (1 h off PT). Note it in the footer |
| GA4 bounce | `bounceRate` = 1 − engagement rate | Labeled "GA4 bounce (non-engaged sessions)". It's not the same definition as M4, so it's never compared with M4 |
| GA4 ATC | `addToCarts` is an **event count**, not sessions | Label "GA4 add-to-cart events per session". Never call it the ATC rate |
| Splits Polar can't produce | Shopify | Footer says "Shopify fallback" |

Never place a GA4 number and a Polar number in the same delta.

## 5. Week math (cheat sheet for the scheduled run)

Given run date R (a Monday): reporting week = R−7 … R−1. WoW = R−14 … R−8. YoY = (R−7)−364 … (R−1)−364.
Before/after a listed site change on date D: N = min(days from D to the week end inclusive, days since the previous listed change, 7). After = D … D+N−1; before = D−N … D−1. Flag a day-of-week mix difference whenever N < 7.
First deck of the month = R is the first Monday of the month. It adds the monthly post-purchase section for the prior calendar month vs the month before and the same month last year. August (National Underwear Day) is flagged as not comparable.
