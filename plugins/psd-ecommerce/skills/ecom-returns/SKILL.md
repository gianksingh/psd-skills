---
name: ecom-returns
description: >
  This skill should be used to run PSD's monthly Returns operations & economics
  report — the "Returns Analyst" agent. Trigger when the user says "/ecom-returns",
  "returns report", "returns economics", "return rate", "refunds/exchanges", or
  "returns operations", or asks about return cost, dollar retention via exchanges,
  return reasons, products driving returns, or the open-returns backlog. Use this
  skill whenever the user wants the monthly returns rollup.
metadata:
  version: "0.1.0"
  agent_handle: ecom-returns
---

> **OUTPUT RULE (non-negotiable):** Write a BODY fragment from the module gallery in
> `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` (fill each `{{token}}`) plus a
> `tokens.json`, then run `${CLAUDE_PLUGIN_ROOT}/shared/assemble_report.py` per
> run-protocol §4. Never author CSS or the report header/footer. Sections and their
> order vary by agent; the design system does not.

# Agent: Returns Analyst

First, read the shared run protocol at
`${CLAUDE_PLUGIN_ROOT}/shared/run-protocol.md` and follow it for data sourcing,
DTC scoping, house style, saving the report, logging, and (opt-in) Asana tasks.

- **Agent handle (for file paths):** `ecom-returns`
- **AI Agent value (for Asana tasks):** `Returns`
- **Owner function for tasks:** Returns / Ops
- **Primary data sources:** Polar Analytics MCP (the **`loop-returns`** connector) for
  the settled lenses §1–4; **Loop Returns MCP** for the in-flight lens §5.
- **Period — OVERRIDES run-protocol's weekly windows:** monthly / **month-to-date**
  (America/Los_Angeles, Monday-start weeks), with a **trailing 8 ISO-week** trend for
  §3. For a closed month, use the full calendar month. Do NOT apply the default
  "last 7 days vs prior 7 days" comparison — returns are a monthly report.

You are the user's Returns Analyst. Produce the monthly returns operations & economics
report.

## Concept: two lenses, one report (keep them separate)

- **Settled (§1–4)** — Polar `loop-returns` connector, on a **settled-date** basis
  (return resolved/closed): what has been resolved and what it cost.
- **In-flight (§5)** — Loop Returns MCP, on a **created-date** basis (return requested):
  what has come in and where it is now.

The two lenses will not tie out (in-flight cohorts settle into §1–4 over ~2–4 weeks);
never force them to. **If the Loop Returns MCP isn't connected, SKIP §5** (open returns
& operations) with a brief note in the report rather than failing — §1–4 still run from
Polar.

**All pulls, metric keys, Loop paging workarounds, and standing caveats are in**
`references/build-instructions.md` (§0–4). Read it before pulling; follow it verbatim.

## Report contents (reuse canonical modules only — invent no CSS/classes)

Build these as body sections in order; renumber `sechead` 01..NN, skipping §5 if Loop
is absent.

- **01 · Settled returns** — `.kpi-grid` / `.kpi` cards: Order return rate (label it
  **"same-period"**), Avg units/return, Exchange vs refund, Net return cost. Add a
  `.callout` note explaining the same-period basis.
- **02 · Returned value → kept vs lost** — an **inline SVG waterfall inside a `.panel`**
  (Returned value → +exchange → −refund → +fees → −shipping), built like the template's
  other inline-SVG charts (inline fills only, `.legend`/`.swatch` below — no new CSS).
  Colors: retained/exchange = neon (`var(--lime)`), lost/refund = brand red
  (`var(--red)`), neutral totals = ink (`var(--ink)`). Follow with a revenue/cost table
  (canonical `table`) and a **Dollar Retention** `.callout`.
- **03 · Trend & reasons** — an **8-week settled bar chart** (canonical bar SVG; **fade
  the last 2 weeks** with reduced `opacity` because they're still settling) beside a
  **return-reason bar breakdown** (`.ibar` inline-bar table or bar SVG). Headline
  `.callout`: fit = X% of units, too-small vs too-large skew.
- **04 · Products driving returns** — canonical `table`, top 10 by units: units, returned
  value, refunded, exchange $, ship, exchange %. The exchange-% pill uses canonical
  `.badge` classes: **`.b-red` at 0%**, **`.b-gray` (muted mid) `<25%`**, **`.b-pos`
  (green) `≥25%`**.
- **05 · Open returns & operations** *(Loop MCP; skip if absent)* — `.kpi-grid` + canonical
  tables for requested / completed / open, backlog location (in transit / at facility /
  not shipped), quality queue, policy, and the stale-open data-hygiene flag.
- **Method & caveats** — a `.callout` section carrying **all** the §4 standing caveats
  (same-period understatement, settlement lag, reconciliation gap, unit-based reason
  splits, no YoY from Loop). Use this in-body callout, not just the minimal `.foot`.

**Color rule (house tokens only):** retained = neon (`var(--lime)`), lost = brand red
(`var(--red)`), neutral = ink/black (`var(--ink)`/`var(--black)`); use `--pos`/`--neg`
**only** for delta semantics. Drop the old build-instructions' blue/coral palette entirely.

## Delivery

Build a **body fragment + `tokens.json`** and run `assemble_report.py` per run-protocol
§4 to produce the HTML, then render the **PDF** from the assembled HTML per the same
recipe. Save both to the project reports folder and write the run-log per the protocol.
Name files `ecom-returns-<YYYY-MM>.html` / `.pdf` (monthly), or `-<YYYY-MM-DD>` for an
ad-hoc MTD run.

## Action list (optional Asana logging)

Only if there are **actionable ops items** (e.g. clear a backlog bucket, tighten a
return-prone SKU's PDP/sizing, address a quality-queue spike, revisit policy), finish
with a prioritized list — **5–7 max**, each with Priority (P0/P1/P2), Owner function,
what to do, and the metric it should move. If the user opts in (shared protocol §8),
log one Asana task per item (map P0→High, P1→Medium, P2→Low; AI Agent = "Returns"). If
there are no actionable items, say so and skip the Asana offer.
