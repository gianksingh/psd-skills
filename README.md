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

## Install — Cowork desktop (step by step)

Most people install from the **Cowork desktop app**. Once it's installed here, the
commands also appear in the claude.ai web/mobile chat via your account. You do
**not** download, unzip, or build anything — installing pulls straight from this repo.

*(Annotated screenshots for each step are in `docs/install/` — `1.png` through `8.png`.)*

1. In the left sidebar, click **Customize**. *(image 1)*
2. In Settings, under the **Customize** heading, click **Plugins**. *(image 2)*
3. Top right, click **Add**, then **Add marketplace**. *(image 3)*
4. In the **URL** field, type the repo and choose the **Use "…"** option that appears:
   `https://github.com/gianksingh/psd-skills` *(image 4)*
5. Click **Sync**. *(image 5)*
6. Open the **Personal** tab → under **Local uploads → psd-skills**, find
   **PSD ecommerce** and click the **+** to install it. *(image 6)*
7. You'll see the confirmation *"PSD ecommerce is installed and ready to use."* *(image 7)*
8. **Turn on auto-updates — don't skip this.** Next to `psd-skills` under **Local
   uploads**, click the **…** menu and switch **Sync automatically** ON. This is what
   makes future updates arrive on their own (the marketplace tracks the repo's latest
   commit). If it's left off you will **not** get new versions automatically — you'd
   have to reopen this menu and click **Check for updates** every time. *(image 8)*
9. **Connect the data sources** the agents need (see Requirements) — at minimum
   **Polar**, or the reports run empty.

**Verify:** type `/ecom` in a chat and confirm the commands appear (`/ecom-review`,
`/ecom-ads`, … `/ecom-sale-recap`).

> **Claude Code (technical users):** same two steps from the CLI — add the marketplace
> (`/plugin marketplace add gianksingh/psd-skills`), then install
> (`/plugin install psd-ecommerce@psd-skills`). Exact syntax can change between
> releases; see https://docs.anthropic.com/en/docs/claude-code/claude_code_docs_map.md.

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

- **Maintainers:** make changes in this repo, bump the affected plugin's `version`
  in its `plugin.json`, and push (see `MAINTAINERS.md`).
- **Users with Sync automatically ON** (install step 8): new commits pull in on
  their own — nothing to do.
- **To pull an update immediately:** click the **…** menu next to `psd-skills` under
  **Local uploads** and choose **Check for updates**. That menu also shows the
  currently synced commit and a **Remove** option.

> If a teammate's version looks stale, it's almost always because **Sync
> automatically was left off**. Have them open the **…** menu and either switch it on
> or click **Check for updates** — waiting won't help on its own.

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
