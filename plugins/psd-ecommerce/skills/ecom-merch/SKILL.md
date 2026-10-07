---
name: ecom-merch
description: >
  This skill should be used to build PSD's weekly Ecom Merch Weekly deck — the
  "Merchandiser" agent that replaces the old product performance report. Trigger
  when the user says "/ecom-merch", "merch weekly", "ecom merch weekly", "build the
  merch deck", "weekly merch deck", "run the merchandiser report", "merch report",
  or asks for the weekly site-merchandising review (homepage, PLPs, campaign pages,
  top products, product signals, onsite search, post-purchase, next two weeks) for
  a Monday–Sunday week. Produces a .pptx (opens in Google Slides) with three blank
  What changed / Why / Next steps boxes per slide for the merch manager to fill.
metadata:
  version: "1.0.0"
  agent_handle: ecom-merch
---

> **OUTPUT RULE (non-negotiable):** This agent's output is a PowerPoint deck, not the
> HTML report. Build it only with the bundled, fail-closed harness:
> `scripts/compute.py` → `scripts/build_deck.js`. Never hand-build slides, never edit
> layouts, colors, fonts or slide order in a run, and never write speaker notes.
> When a script stops, fix the input, not the harness.

# Agent: Merchandiser (Ecom Merch Weekly deck)

- **Agent handle:** `ecom-merch`
- **Who runs it:** the site merchandising manager (Jamie), usually on Monday, for the last full Mon–Sun week. Not scheduled.
- **Primary data:** Polar MCP (view `31552-mpfv58vy`, PSD Web, bots included). Also Shopify MCP (titles, product images, inventory), Klaviyo MCP (email sends), and the manual exports collected at intake.
- **What the run writes:** numbers, charts, one headline per slide, run notes. **What it never writes:** recommendations, so-whats, action items or speaker notes. Those belong to the presenter.
- **Shared protocol:** follow `${CLAUDE_PLUGIN_ROOT}/shared/run-protocol.md` §5 (save), §6 (log) and §7 (hand back), adapted to a .pptx below. Skip its §4 (HTML assembly) and §8 (Asana): this deck has no action items.

`${SKILL}` below means this skill's folder: `${CLAUDE_PLUGIN_ROOT}/skills/ecom-merch`.

## 0. Set up the run folder

Work in the connected project folder at `reports/ecom-merch/<week_start>/` (create it). If no project folder is connected, use a folder in the session workspace and say so in the hand-back. Inside it:

```bash
export SKILL="${CLAUDE_PLUGIN_ROOT}/skills/ecom-merch" MERCH_WORK="$PWD"
mkdir -p data inputs build assets/products
cd "$SKILL/scripts" && [ -d node_modules/pptxgenjs ] || npm install --silent --no-audit --no-fund || npm install --prefix "$MERCH_WORK" pptxgenjs@4.0.1
cd "$MERCH_WORK"
```

Save every file Jamie uploads into `inputs/` (Clarity CSVs and click maps, AfterSell export and screenshots, Searchspring exports, the Asana calendar screenshot, homepage screenshots). Paths in `raw_<week>.json` are relative to the run folder (e.g. `inputs/clarity_homepage.csv`).

## 1. Intake (always the first step)

Before pulling any data, ask Jamie for everything below in one message, as a checklist. Wait for her answers, then confirm back what you received and what's missing.

1. **Reporting week** (Mon–Sun). Default: the most recent full week. Confirm the dates.
2. **Campaigns:** name as spelled on site, landing page URL, start date, notable dates in the week, and last year's equivalent campaign with its start date.
3. **What's live:** homepage, campaign landing page(s) and top PLPs, with each change and its date. Ask for a homepage screenshot for each refresh (4:5 mobile crop).
4. **Microsoft Clarity:** the area export (CSV) and click-map image for the homepage and each campaign landing page, using the same saved view every week.
5. **AfterSell:** the analytics export (xlsx), an order browser screenshot for the same dates, a per-funnel export if funnel results are wanted (the default export combines all funnels), and for each active test a screenshot of its stats (sample, lift, confidence, decision date). In the first deck of each month, also the prior month's export.
6. **Calendar for the next two weeks:** a screenshot of the Asana marketing calendar (homepage refreshes, email, SMS, push). Klaviyo fills in any email the calendar doesn't show.
7. **Last week's open follow-ups** (an empty list is a fine answer).
8. **Searchspring:** with the dashboard date range set to the same Mon–Sun, export (CSV preferred, screenshot if not): popular searches with search counts, the Zero Results Searches Breakdown table (term + total searches), and the search summary (total and unique searches, zero-result searches, click-through and conversion if shown). Also the prior week for WoW.
9. **New drop (only if a product release launched in the last 14 days):** drop name, launch date, collection handle, and one or two past drops to compare against. If there was no drop, the slide is skipped.
10. **Featured collections (optional).** If Jamie doesn't list any, they're inferred from traffic (the `featured_collections` rule in `config.json`).

If an item is still missing after intake, carry on. Record it in `inputs.*_missing`, and the deck flags it on the cover line, in the run notes and as a red INPUT MISSING pill on the affected slide. **Never guess or fill in a number.**

## 2. Read the rules

Read `${SKILL}/references/metric-bible.md` and `${SKILL}/scripts/config.json` in full before the first query. The rules people most often get wrong:
- View `31552-mpfv58vy` (PSD Web) on every Polar query. **Bot sessions are included** (no `is_bot_session` filter), so sitewide numbers match the Daily Flash.
- **Every page slide shows landed and visited sessions.** Landed = `landing_page_path IS X`. Visited = the exact-match `page_paths_in_session` pattern (bible §1).
- Never combine a `page_path` filter with funnel, bounce or checkout metrics. They return sitewide totals.
- YoY for anything before April 2026 uses GA4 on both sides. Never put GA4 and pixel numbers in one delta.

## 3. Pull the data (Polar MCP first)

Call `get_context` first. Use `comparisonPeriod: "range"` with explicit WoW and YoY dates (bible §5). Write every result into `data/raw_<week_start>.json` with the same keys and nesting as `${SKILL}/references/raw_schema_example.json`.

| Raw key | Pull |
| --- | --- |
| `pixel.sitewide` | sessions, bounced, product viewed, ATC, checkout started and completed sessions: CY + WoW, daily, and by `custom_5984` |
| `ga4.sitewide` (+ `paid_social_*`) | `ga_main.raw.sessions`, `engaged_sessions`, `ga4_adds_to_cart`, `ecommerce_purchases`, CY vs YoY week |
| `sales` | `custom_60202`, `total_orders`, `custom_60206`, `custom_60207`: CY, WoW, YoY |
| `homepage.viewed` / `landing` / `landing_daily` / `landing_by_channel` / `before_after_sources` | `custom_6843` (visited) and `landing_page_path IS /` (landed). Daily data has to cover N days before the first listed homepage change |
| `plps.top_cy`, `top_prior`, `prior_lookup`, `landing_cy`, `landing_wow` | visited ranking by `page_path` (top 10, this week and prior week), then landed sessions and bounce for each ranked page |
| `inputs.featured` | Jamie's list, or the `config.json` rule: top 5 by visited sessions after the exclusions |
| `collections.<path>` | per featured collection: visited funnel (exact match), `page_path_sessions` for reconciliation, `custom_60202` by `collection_handle`, top `custom_5984` source. Landed rows come from `plps.landing_*` |
| `titles` | Shopify collection titles for every page shown (`search_collections`). If a title isn't found, the page is shown by its handle in title case |
| `campaign.lp_landing` / `lp_page` / `lp_by_channel` / `categories` | landing funnel, visited funnel, sources, and category tag pages under the campaign's shop-all collection, CY + WoW |
| `ga4.campaign_lp_landing`, `campaign_all_landing` | GA4 direct (`fetch_live_connector_data`, `report`, dims `landingPage`), CY vs YoY week |
| `sends.sms` | pixel sessions where `custom_5984 IS SMS`, by `utm_campaign`, for campaigns dated in the week. Add up each send's audience segments |
| `sends.email`, `ahead.email` | Klaviyo `get_campaigns` (email, Sent or Scheduled), in PT |
| `aftersell.orders_by_channel` | `shopify_sales_main.raw.total_orders` by `custom_5794` with **no view** (all channels, so TikTok Shop is included). Rows: Online Store, TikTok Shop, Tapcart app (Mobile App), Shop App, Other channels |
| `products.top` | top products by `custom_60206` (units) with dims `product_title`, `product_type`, filter `custom_5794 IS Online Store` and `product_title NOTCONTAINS Mystery`, CY + WoW; plus `custom_60202`, `total_orders`. Pixel for the same rows: `polar_pixel_product_pageviews`, `polar_pixel_add_to_cart`, `polar_pixel_sessions` by `product_title` × `product_type`. `collection` = campaign or featured handle the product sits in (`collection_handle` breakdown). `campaign_units` = units with `collection_handle IS <campaign shop-all>` |
| `app` | `total_orders`, `custom_60202`, `custom_60207` where `custom_5794 IS Mobile App`, CY + WoW |
| `search.pixel` | sessions and funnel (product viewed, ATC, checkout completed) for the exact-match `page_paths_in_session` pattern on `/search`, CY + WoW |
| `products.pool` | top 40 product × style rows by `polar_pixel_product_pageviews` (pixel), joined to Online Store units, prior-week units, orders and net sales; `inventory_today` = `shopify_sales_main.raw.inventory_quantity` (snapshot, no view) for any row flagged low ATC. Rows with 0 units (virtual bundles) drop out and go in `issues` |
| `products.entry` | for each product flagged on the signals slide: pixel sessions by `landing_page_path` where `page_paths_in_session` CONTAINS `/products/<handle>` and NOTCONTAINS `/products/<handle>-` (top 2 entry pages + total), and PDP views by `custom_5984` for the product (top source). Polar can't attribute PDP views to the page viewed just before, so entry page and source stand in for "where the views came from" |
| `products.image_urls` | Shopify GraphQL `products(query: "title:'<title>'")` → `featuredMedia.preview.image.url`, matched on `productType`, keyed `"title|type"`, for every top and pool row. Then run `fetch_thumbs.py` (§5) (needs cdn.shopify.com; missing images render as placeholder tiles) |
| `search.searchspring` | values read off the Searchspring export. Rank-only lists when counts aren't given; anything missing goes in `missing` |
| `drop` | only when intake lists a drop: launch-to-date units, net sales, sessions, PDP views, ATC, orders for the drop collection, and the same for each comparison drop over the same number of days from its launch; top products in the drop |
| `inputs.ahead_items` | one row per calendar entry: `date`, `tags` (any of Site, Email, SMS, Push), `text` as written on the calendar |
| `aftersell.daily_cy/daily_wow`, `aftersell.order_browser` | from the export, and read off the order browser screenshot (total orders, eligible, shown, not shown, ineligible reasons, opportunities, revenue) |
| `issues` | site, tracking or data problems found while pulling. State the fact, not the fix. **They never go in the deck.** `compute.py` writes them to `data/issues_<week>.md` for the chat reply, so Jamie can validate them first |

`clarity_labels` needs one label per Clarity area row, in export order. Name the unlabeled areas from the click-map image, top to bottom.

## 4. Write the headlines (`data/observations_<week_start>.json`)

For every slide id, write a `headline`. Observations are optional working notes: they never print on a slide or in the speaker notes, but are useful for the chat reply. Also write `cover.headline` (optional, one line under 100 characters; Jamie elaborates in the deck) and `run_notes` (contradictions, assumptions).

The headline prints on the slide under the section title. Below the chart sit three empty boxes for Jamie: What changed, Why, Next steps.

**What to write**
- The headline is the slide's one takeaway, with its number, in under 120 characters. A reader should get the point from the headline alone.
- Observations are facts: what changed and by how much. No recommendations, no so-what, no actions. Those are Jamie's.
- Before writing, check the guardrails and name any that apply: the traffic source and that week's sends before crediting a lift; landing pages compared with landing pages; structure changes; event weeks; contradictions (flag them, don't explain them away); low confidence (under 100 sessions or 30 conversions); one style, division and gender per row; one name per campaign.

**How to write it (baked in from the no-AI-slop rules)**
- Lead with the number and the thing. Write "Spooky Staples visits more than tripled to 2,837", not "There was a notable increase in engagement".
- Use concrete names, dates and counts. If a sentence could sit in any other week's deck unchanged, cut it.
- Use plain verbs and active voice. Write "rose", "fell", "drew", "converted", never "saw growth" or "experienced a decline".
- Don't use these: delve, leverage, utilize, robust, crucial, pivotal, testament, underscore, highlighting, showcasing, notably, importantly, significantly, seamless.
- No "not X, it's Y" contrasts, no colon reveals ("The catch: …"), no rhetorical questions, no closing kickers.
- Don't tell the reader what matters ("this is important", "worth noting"). The number shows it.
- No em dashes in headlines or observations. Use a comma, a period or parentheses.
- Keep each observation to 1–2 lines (under 230 characters). The build fails on longer text, banned words or recommendation verbs (should, recommend, consider, suggest, must).

## 5. Build

```bash
python3 "$SKILL/scripts/fetch_thumbs.py" <week_start>     # product thumbnails -> assets/products/ (fails soft)
python3 "$SKILL/scripts/compute.py" <week_start>          # -> data/deck_<week_start>.json, data/issues_<week_start>.md
NODE_PATH="$SKILL/scripts/node_modules:$MERCH_WORK/node_modules" \
  node "$SKILL/scripts/build_deck.js" data/deck_<week_start>.json "build/PSD_Ecom_Merch_Weekly_<week_start>_to_<week_end>.pptx"
```

If the pptx skill is available, also run its `scripts/office/validate.py` on the deck. Thumbnails need network access to `cdn.shopify.com`; when it's blocked the slides show placeholder tiles and the run lists it as an issue. The new-drop slide is built only when intake lists a drop.

## 6. Check, then deliver

1. Render every slide to an image (LibreOffice → `pdftoppm`) and look at each one. Nothing overflows a card, no text overlaps, every footer shows the same week, every missing input shows as a red INPUT MISSING pill on its slide.
2. Spot-check 5 numbers against the raw pulls: sitewide sessions, sitewide CVR, homepage landed CVR, one featured-collection ATC rate, campaign landed sessions.
3. Confirm the three boxes are empty on every finding slide and no slide has speaker notes.
4. Save the .pptx in the run folder (`reports/ecom-merch/<week_start>/build/`) and add it to `reports/index.html` per run-protocol §5. Write the run log per §6, including the Polar keys used and any contradictions.
5. Hand back: send the .pptx into the conversation, then reply with the week, the missing inputs, any contradictions, and the issues list from `data/issues_<week_start>.md` for Jamie to validate. Issues never go in the deck.

## Template

`${SKILL}/assets/PSD_Ecom_Merch_Weekly_TEMPLATE.pptx` shows every layout with numbers masked. To regenerate it after a harness change: `python3 "$SKILL/scripts/make_template.py" data/deck_<week>.json data/template_spec.json`, then `build_deck.js data/template_spec.json <out>.pptx --template`.
