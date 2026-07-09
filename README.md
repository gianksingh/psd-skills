# PSD Skills

PSD's shared library of Claude skill "plugins," organized by business domain. This
repo is a **plugin marketplace**: add it once, then install the domain plugin(s)
your team needs. Maintainers push updates here; users pull them.

---

## How it's organized

One **plugin per domain**, and every command is prefixed by that domain so names
never collide as the library grows (type `/ecom` to see all ecommerce agents).

| Plugin          | Command prefix | Status   | Covers |
| --------------- | -------------- | -------- | ------ |
| `psd-ecommerce` | `/ecom-…`      | Active   | DTC ecommerce reporting agents |
| `psd-marketing` | `/mkt-…`       | Reserved | (future) |
| `psd-finance`   | `/fin-…`       | Reserved | (future) corporate/org finance |
| `psd-ops`       | `/ops-…`       | Reserved | (future) |
| `psd-retail`    | `/ret-…`       | Reserved | (future) retail / wholesale |

Prefixes are reserved in `PREFIX-REGISTRY.md`. Note `/ecom-finance` (ecommerce
P&L) is intentionally separate from a future `/fin-…` (corporate finance).

---

## The agents (psd-ecommerce)

| Command | Agent | What it does |
| ------- | ----- | ------------ |
| `/ecom-review` | Weekly Exec Review | Company-wide weekly rollup (Head of Growth): business-snapshot KPIs, % -to-forecast pacing, KPI scorecard, sales by method & channel, top-20 products, traffic mix, delivery times, 3 wins / 3 risks, and a prioritized action list. |
| `/ecom-ads` | Paid Ads | Weekly paid-media review across Meta, Google, and TikTok: per-platform snapshots, top/bottom campaigns, CPA/fatigue risk flags, and scale / cut / test recommendations. |
| `/ecom-retention` | Retention | Email/SMS + lifecycle review: revenue impact, top flows vs campaigns, deliverability/list health (7d), plus repeat-customer / LTV / cohort health (30d). |
| `/ecom-merch` | Merchandiser | Product performance: top sellers, biggest movers up/down, high-traffic/low-CVR PDP flags, and restock/velocity alerts. |
| `/ecom-pricing` | Pricing | Pricing & profitability: AOV, revenue per visitor, discount/promo impact, and top-revenue vs top-margin mismatches. |
| `/ecom-cro` | CRO | Onsite conversion funnel: KPI snapshot, view→cart→checkout→purchase funnel, source/device segments, page-type leaks, and prioritized A/B tests. |
| `/ecom-finance` | Finance | Weekly financial overview: topline, blended ROAS / MER / CAC, revenue mix, profitability, and a run-rate monthly projection. |
| `/ecom-forecast` | DC Forecast | Turns a net-sales target or growth rate into a **daily** DC labor plan (orders/units/net sales); outputs an Excel workbook + pacing dashboard. |
| `/ecom-sale-recap` | Sale Recap | Single-page executive recap of a specific sale/promo event; intake-first, **in-chat only** (HTML + continuous-page PDF + optional 16:9 deck). |

**Outputs & side effects:** the weekly reporting agents produce a styled HTML
report + PDF, save it to the project reports folder, and (if you opt in when
prompted) log action items to Asana.
`/ecom-forecast` produces an Excel workbook. `/ecom-sale-recap` is in-chat only
(in-chat only). All reports share one house style (`shared-assets/report-template.html`).

---

## Install (one-time, ~2 minutes)

1. **Use Claude Code or the Cowork desktop app** to install. (Once installed, the
   commands also surface in the claude.ai web/mobile chat via your account.)
2. **Add this repo as a plugin marketplace** — point Claude at this repository's
   URL.
3. **Install the plugin(s) you want**, e.g. `psd-ecommerce`.
4. **Connect the data sources** the agents use (see Requirements below).

You do **not** need to download, unzip, or build anything — installing pulls the
plugin straight from this repo.

> The exact install commands depend on your surface and can change between
> releases. For current syntax see the Claude Code docs
> (https://docs.anthropic.com/en/docs/claude-code/claude_code_docs_map.md) or, for
> the desktop app, https://support.claude.com. As a guide, the flow is generally:
> add the marketplace (this repo) → install `psd-ecommerce` from it.

---

## Use

- **Run an agent** by typing its command (`/ecom-review`) or asking in plain
  language ("run the weekly exec review", "give me the paid media report").
- Each agent runs **independently** — you never have to run them all.
- Reports save automatically per agent; after each report you're asked whether to
  log its action items to Asana; **`/ecom-sale-recap` is in-chat
  only** and will ask you a few setup questions before it pulls data.

---

## Update

- **Maintainers:** make changes in this repo and bump the affected plugin's
  `version` in its `plugin.json` (see `MAINTAINERS.md`).
- **Users:** pull the latest via your marketplace's **update** command. Same
  caveat as install — check the docs links above for the exact command on your
  surface. The flow is generally: update the marketplace → the newer plugin
  version installs.

---

## Requirements

- **Polar Analytics** — required (all report data).
- **Asana** — used by the weekly agents *only if you opt in* when they offer to
  log action items after a report.
- **Shopify / Klaviyo / Microsoft Clarity** — optional backfill (some agents).

Full detail — including the data sources that must be connected *inside Polar* and
the external inputs `/ecom-sale-recap` asks for — is in `DEPENDENCIES.md`.

A note on surfaces: installing makes commands **available** across your account
(desktop, Claude Code, and web). Whether an agent can actually **run** on a given
surface depends on those connectors being present in that session.

---

Maintainers and contributors: see `MAINTAINERS.md` (how to add a skill or a new
domain plugin, the shared-asset sync, and the release flow) and `PREFIX-REGISTRY.md`.
