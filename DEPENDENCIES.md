# Dependencies

What to connect to get the most out of these agents. Two layers matter: the
**Claude connectors (MCPs)** you enable in your Claude app, and the **data sources
connected inside Polar** (Polar is the aggregation layer the agents read from).

---

## 1. Claude connectors (MCPs)

Enable these in your Claude app (Settings → Connectors).

| Connector | Required? | What it powers |
| --------- | --------- | -------------- |
| **Polar Analytics** | **Required** | All quantitative report data for every agent. If Polar isn't connected/activated, the agents can't run. |
| **Asana** | Optional (opt-in) | After a weekly report, the agent *asks* whether to log its action items as "Needs Human Review" tasks — only creates them if you say yes. Never used by `/ecom-sale-recap` or `/ecom-forecast`. |
| **Loop Returns** | Required for `/ecom-returns` §5 | The in-flight / open-returns lens (created-date): requested / open / completed counts, backlog location, quality queue, and policy. §5 is **skipped with a note** if it isn't connected; §1–4 still run from Polar's `loop-returns` connector. |
| **Shopify** | Optional; **required for the `/ecom-*-audit` agents** | Config / product / inventory ground truth for the audits (Okendo review metafields, compare-at price, stock, payment & shipping config). Also backfill for `/ecom-review` and `/ecom-cro`. |
| **Klaviyo** | Optional | Backfill for `/ecom-retention` (flow/campaign detail). |
| **Microsoft Clarity** | Optional; **required for the `/ecom-*-audit` agents** | Real-user behavioral + field-performance data (dead/rage/quickback clicks, scroll depth, session recordings, field LCP/CLS) that grounds the audits. Also qualitative input for `/ecom-cro`. |
| **Chrome** (claude-in-chrome) | **Required for the `/ecom-*-audit` agents** | Live-render observation of psd.com — above-the-fold/layout and tap-target checks, and the network waterfall / render-blocking / image-weight read for `/ecom-site-speed-audit`. |
| **Mounted project folder** | Required for local saves/logs | Not a connector, but the weekly agents save report copies and run-logs here. |

---

## 2. Data sources connected *inside Polar*

Polar aggregates these; each must be connected in Polar for the corresponding
metrics to exist. If one is missing, the related section shows **N/A**.

| Source in Polar | Powers |
| --------------- | ------ |
| **Shopify** | Core sales, orders, AOV, units, margin, customers; top products. |
| **Meta / Google / TikTok Ads** | `/ecom-ads`; blended MER / ROAS / CAC in `/ecom-finance` and `/ecom-review`. |
| **Klaviyo** | Email/SMS revenue and share for `/ecom-retention` and the email line in `/ecom-review`. |
| **Amazon Selling Partner** | The Amazon line in `/ecom-review` (shows N/A until the connector finishes syncing). |
| **GA4** | YoY traffic/funnel where Polar Pixel has no history. |
| **Polar Pixel** | Onsite funnel (2026-on) for `/ecom-cro` and sale-recap. |
| **"PSD - Polar Targets" Google Sheet** | The %-to-forecast goal bar in `/ecom-review` and pacing reads. |
| **Loop Returns** (`loop-returns` connector) | The settled returns economics (§1–4) for `/ecom-returns`: return rate, refund / exchange / fees / shipping, net return cost, and dollar retention. |

> **DTC scope:** by default the agents exclude TikTok Shop and Amazon from DTC
> figures; those are reported only when an agent asks for them explicitly.

---

## 3. External / user-supplied inputs

A few `/ecom-sale-recap` sections rely on data **not in Polar**. The agent asks you
to upload them (screenshot or export) and skips the section if you don't have them:

- **AfterSell** dashboard — post-purchase upsell performance.
- **Rokt** Network Analytics — thanks-network ad revenue.
- **Tapcart** push campaign screenshot — app push (under-attributed in Polar).

---

## Quick per-agent view

- **Every agent:** Polar (required).
- **Weekly agents** (`/ecom-review`, `/ecom-ads`, `/ecom-retention`, `/ecom-merch`,
  `/ecom-pricing`, `/ecom-cro`, `/ecom-finance`): a mounted folder for saves/logs;
  Asana only if you opt in when offered.
- **`/ecom-returns`:** Polar (`loop-returns` connector) for the settled economics (§1–4)
  + the **Loop Returns MCP** for the in-flight/open lens (§5, skipped with a note if it
  isn't connected); a mounted folder for saves/logs; Asana only if there are actionable
  ops items. Monthly/MTD, not weekly.
- **`/ecom-*-audit` (ad-hoc deep dives — page, cart, PDP merchandising, site speed):**
  Polar + **Microsoft Clarity** (behavioral / field CWV), **Shopify** (config / product /
  inventory ground truth), and **Chrome** (live render) — all required. Each source
  **degrades to labeled heuristics** if it's absent: the audit still runs, but every
  affected finding is marked an inference and the report says what to connect. Output is
  the unified HTML + PDF report.
- **`/ecom-web-daily-flash`:** Polar + **Shopify** (incl. **ShopifyQL** for the freshness
  cross-check) + **GA4 via Polar** (for the onsite YoY, since the Polar Pixel has no last
  year) — **no new connector beyond what's already listed**. Daily (T-1), **files-only**:
  it hands back HTML + PDF into the chat and never pushes, publishes, or emails; no Asana.
- **`/ecom-forecast`:** Polar + the "PSD - Polar Targets" sheet; outputs Excel (no Asana).
- **`/ecom-sale-recap`:** Polar + user-supplied AfterSell/Rokt/Tapcart; in-chat only
  (no Asana).
