# Polar pulls for mix-match-report

Run every pull below **twice**: once for the report period and once for the comparison period, each with fixed `dateRangeFrom` / `dateRangeTo`. Don't use `comparisonPeriod`. Save each response's `tableData` and `totalData` verbatim under `raw.cur.<key>` or `raw.prev.<key>` (shape: `references/raw_schema_example.json`). Don't rename, round or filter the rows. `compute.py` does all the math.

Shared settings for every pull:

- `views`: `31552-mpfv58vy` (PSD Web)
- `settings`: `{}`
- `metricRules`: `{}`
- No `is_bot_session` filter. Bot sessions stay in, to match the Daily Flash and the merch deck.

Metric keys used below:

| Short | Key |
|---|---|
| gross | `shopify_sales_main.raw.gross_sales` |
| disc | `shopify_sales_main.raw.discounts` |
| net | `shopify_sales_main.computed.net_sales` |
| orders | `shopify_sales_main.raw.total_orders` |
| units | `custom_60206` |
| sess | `shopify_attribution_pixel.raw.polar_pixel_sessions` |
| atc | `shopify_attribution_pixel.raw.polar_pixel_funnel_product_added_to_cart_sessions` |
| chk | `shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_started_sessions` |
| conv | `shopify_attribution_pixel.raw.polar_pixel_funnel_checkout_completed_sessions` |

## 1. `lines`: every Gift Builder line

| Param | Value |
|---|---|
| metrics | gross, disc, net, units |
| dimensions | `order_line_properties,order_id,product_title,purchase_type` |
| granularity | `day` |
| rules | `{"order_line_properties":[{"value":["\"key\":\"_fit_id\""],"operator":"CONTAINS"}]}` |
| ordering | `order_id:ASC` |
| limit | `5000` |

One row per builder line. `order_line_properties` comes back as a JSON string holding all 7 `_fit*` properties, and `compute.py` parses it. **Paginate:** if the response has `rowLimitReached` or `truncated`, call again with `offsetPage` 1, 2, … and append the `tableData` until a page comes back short. A week is about 1,500 rows, so a month can pass 5,000.

## 2. `orders`: full Gift Builder orders, including add-on items

| Param | Value |
|---|---|
| metrics | orders, gross, disc, net |
| dimensions | `order_id` |
| granularity | `day` |
| rules | `{"order_discount_code":[{"value":["Build Your Outfit"],"operator":"IS"}]}` |
| ordering | `order_id:ASC` |
| limit | `5000` (paginate the same way) |

The discount code is order-level, so these rows carry every line in the order. Add-on sales = order net minus builder-line net.

## 3. `web`: PSD Web totals (the share-of-web denominator)

metrics: orders, net. No dimensions, granularity `none`, rules `{}`. Keep `totalData`.

## 4. `traffic_daily`: sessions that viewed the builder

| Param | Value |
|---|---|
| metrics | sess, atc, chk, conv |
| dimensions | none |
| granularity | `day` |
| rules | `{"page_paths_in_session":[{"value":["/pages/gift-builder"],"operator":"CONTAINS"}]}` |

Keep `tableData` (the daily rows) and `totalData` (the period totals that `compute.py` uses).

## 5. `traffic_landers`: sessions that landed on the builder

Same metrics as pull 4, granularity `none`, rules `{"landing_page_path":[{"value":["/pages/gift-builder"],"operator":"IS"}]}`. Keep `totalData`.

## 6. `traffic_channel`

Same as pull 4, with dimension `custom_5984` (PSD Custom Channel Grouping), granularity `none`, ordering `<sess>:DESC`, limit `25`.

## 7. `traffic_device`

Same as pull 4, with dimension `session_device_type`, granularity `none`.

## Checks before computing

- `lines` row count is more than 0 for the report period. If it's 0, stop and tell the user. Don't build an empty report.
- Every response used the PSD Web view (`views_applied[0].title` contains "PSD Web").
- If a metric has `dataThrough` before the end of the period, write it in `raw.meta.notes` and tell the user in the hand-back.

These pulls were checked against live Polar on 2026-11-18 with test order 7318632431813 (two lines, $110 gross, $22 discount, $88 net, with `_fit*` properties parsed and `purchase_type` returned).
