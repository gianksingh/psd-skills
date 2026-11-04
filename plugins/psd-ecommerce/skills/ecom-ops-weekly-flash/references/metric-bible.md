# Ecom Ops Weekly Flash: Metric Bible

Version 1.0 (2026-11-04). Validated on the week of Mon 10/26/26 to Sun 11/1/26.
Every run follows this file. If a definition can't be produced, the run flags the slide (INPUT MISSING) and does not substitute another metric.

## 0. Global

| Setting | Value |
| --- | --- |
| Week | Monday–Sunday, America/Los_Angeles. Default: the most recent full week |
| Channels | **Web** = Polar `custom_5794` IN Online Store, Mobile App (Tapcart), Shop App, Fermat, Facebook. **TikTok Shop** = `custom_5794` IS TikTok Shop. Exclude Loop exchanges, Gorgias, Draft Order, Other, POS |
| Orders metric | `shopify_sales_main.raw.total_orders`, no view, filtered by `custom_5794` |
| LY | 364 days back (same weekday). "Same 4 weeks LY" = the 4 Mon–Sun weeks 364 days back |
| Last 4 weeks | This week plus the 3 before it |
| Rates | Always % of orders, two decimals for delivery reasons (1.48%), one for contact rates (13.6%). Never "per 1,000" |
| Low confidence | Survey cuts under 30 responses are "directional" |

## 1. Volume vs plan
- **Plan** = Q4 Staffing Forecast, `Daily Forecast` tab: Web orders, TikTok orders, Web tickets, TikTok tickets by day, summed Mon–Sun.
- **Tickets** = Polar Gorgias connector `generated_root_gorgias.raw.tickets_created` by `channel`; TikTok Shop = `tiktok-shop`, Web = every other channel. Full Mon–Sun (the ticket export may stop short; Polar does not).
- **Order contact rate** = tickets ÷ orders, per channel. Compare to the same week LY.
- **Outlook** (next 4 weeks): orders = forecast × last 2 weeks' actual-to-plan ratio per channel; tickets = forecast × last 4 weeks' actual-to-plan ratio (all channels). Same-week-LY dots from Polar.

## 2. Fulfillment and delivery (ShopifyQL `FROM fulfillments`)
- **Order to fulfillment** = `median_hours_order_to_fulfillment`; **order to delivery** = `median_days_order_to_delivery`, weekly, this year and LY.
- **Unfulfilled 2+ business days** = Shopify `ordersCount` with `fulfillment_status:unfulfilled status:open` and `created_at` between 35 days ago and 2 business days before run date. Never use an open-ended created_at filter (legacy open orders inflate it).
- **Shipping service chosen** = Polar `shipping_method` grouped by `custom_5902` (Standard, Express, Next-Day, International), with % of orders. "Ships as", ship and deliver medians come from ShopifyQL `GROUP BY shipping_service`. Keep this table format.
- Shopify leaves the service blank on ~40% of fulfillments (TikTok Shop, Express shipped on the second UPS account `85208F`, international, exchanges). This is a labeling gap, not missing tracking. Report the count; do not infer services into the table.

## 3. Delivery contacts (Gorgias ticket export, `Ticket Field: Ticket Reason`)
| Category | Reason contains |
| --- | --- |
| Where is my order | TRACKING INFORMATION, STATUS OF ORDER, DELAY:: |
| Delivered, not received | DELIVERED::NOT RECEIVED, ORDER PROTECTION::CLAIM::DELIVERED NOT RECEIVED |
| Lost in transit | LOST IN TRANSIT (incl. OP claim) |
| Missing items | MISSING, PARTIAL SHIPMENT |
| Wrong item / size | WRONG |
| Damaged | DAMAGED |
Order Protection claim codes are new in 2026 and are folded into the matching reason. Rates = tickets ÷ all orders (web + TikTok Shop) over the last 4 weeks vs the same 4 weeks LY.

**Like-for-like where-is-my-order (tripwire):** web channels only, scaled by the share of web tickets that carry a reason, each year: `WISMO_web ÷ labeled_share ÷ web_orders`. Reason: LY tickets were less often labeled (≈20% unlabeled vs ≈7%), and TikTok Shop ticket intake into Gorgias roughly doubled, which inflates the all-channel rate. When all-channel change exceeds like-for-like by 25+ pts, the slide carries a "Read with care" callout automatically.

**Delivered-not-received outcomes:** Order Protection claim (reason under ORDER PROTECTION), Reshipped (tag `Reshipment Order Placed`), Still open, else "Closed, outcome not recorded". The Gorgias `Resolution` field is empty today; list it as an issue until it is filled.

## 4. Customer service (Gorgias ticket export + Retently)
- **SLA**: first reply within 8 business hours for email/chat/help center/contact form/TikTok Shop; SMS within 2. Business hours Mon–Fri 7am–3pm PT. Phone excluded. Spam / no-reply-needed / auto-close excluded. Unanswered tickets count against SLA once they pass the limit. "All" includes AI agent replies; **human-only** = tickets the AI agent never touched (no `AI Agent Outcome`).
- **AI vs human**: `AI Agent Outcome` Close = AI resolved; Handover = AI then human; blank = human only.
- **CSAT** = Retently `CSAT: Ticket Solved - Email`, rating 4–5 of 5, joined to Gorgias on ticket id. TikTok Shop tickets get no survey.
- SLA and AI rows cover the days in the export (`Mon–Sat` if it stops short); the slide says so.

## 5. Voice of the customer (Retently)
- NPS = % 9–10 minus % 0–6 (Metric NPS). Delivery satisfaction = % rating 3 of 3 on `DSAT: US Delivery Service Experience`. Rolling 4 weeks, 13-week trend, vs same 4 weeks LY.
- **NPS cuts**: each response joined to the order it rated (`nps_join.py`: customer's latest order fulfilled 5+ days before the response, matched by email via Shopify customer search). Cuts: channel (Online store = `sourceName` web; app = everything else), first-time vs repeat (customer `numberOfOrders` > 1), delivered within 7 days, contacted CS about the order (Gorgias ticket from the same email between order and response). Prior = 4 weeks before the last 4.

## 6. Returns (Loop)
- Pipeline stages from Loop MCP `list-returns-tool` totals (`status: open` × `label_status`, `day_limit: 35`): label created not shipped (new, pre_transit), in transit (in_transit, out_for_delivery), delivered not processed (delivered), no label (no_label, failure); expired = `status: expired`, `day_limit: 35`.
- Submitted, processed, days to process (median submitted→processed), exchange share and $, refunds $ from the Loop export, last 4 weeks vs same 4 weeks LY. Unprocessed age buckets from submissions in the last 30 days with no processed date.
- Reasons and products from Polar's Loop connector: `generated_root_loop_returns.raw.return_amount` by `parent_return_reason` (by return date); `unit_return_rate`, `units_returned`, `units_sold` by `product_title` (orders placed 8–5 weeks ago, 300+ units sold). Product × reason: `product_title` + `parent_return_reason`.

## 7. Tripwires
Thresholds live in `scripts/config.json` (`thresholds`), as [amber, red]. Change them there only, after ops sign-off. Order to delivery stays a day-difference vs LY rule.
