---
name: ecom-sale-recap
description: >
  Use this skill to produce PSD's single-page executive recap of a sale or promo
  event (the Sale Recap agent). Trigger when the user types /ecom-sale-recap or
  asks for a sale recap, sale event recap, event post-mortem, promo recap, or a
  wrap-up of a specific sale window versus a comparison period. Use this for the
  event-level recap dashboard, not the recurring weekly reviews.
metadata:
  version: "0.6.1"
  agent_handle: ecom-sale-recap
---

> **OUTPUT RULE (non-negotiable):** Write a BODY fragment from the module gallery in
> `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` (fill each `{{token}}`) plus a
> `tokens.json`, then run `${CLAUDE_PLUGIN_ROOT}/shared/assemble_report.py` per
> run-protocol §4. Never author CSS or the report header/footer. Sections and their
> order vary by agent; the design system does not.

# Agent: Sale-Event Recap

Produce a single-page executive recap of a PSD sale event, uniform in data rules,
comparison logic, structure, and styling. Output is an in-chat HTML dashboard
**plus** an A4-landscape PDF.

**Read first, every run:**
1. `${CLAUDE_PLUGIN_ROOT}/skills/ecom-sale-recap/references/build-spec.md` — the
   full data/section/QA bible. It is authoritative for metrics, dimensions,
   section order, comparison logic, integrity rules, and the PDF recipe. (Its
   note about "do not convert to a skill yet" is superseded — this IS the skill;
   everything else in it stands.)
2. `${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` — the unified house style.
   Copy its `<style>` block verbatim and its component markup from the gallery,
   replacing `{{PLACEHOLDER}}` tokens. Do not restyle from prose.

- **Agent handle:** `ecom-sale-recap`
- **Primary data source:** Polar Analytics MCP. Request external inputs
  (AfterSell, Rokt, Tapcart push) from the user per build-spec §1C.
- **View:** PSD Web — `views: ["31552-mpfv58vy"]`. Fresh `get_context` each run.
- **Leading metric:** Adjusted Demand $ (`custom_64021`); Adjusted Net Sales
  secondary. Verify keys via `get_metrics` each run (keys can move).

## This agent OVERRIDES the shared run protocol

Unlike the recurring `/ecom-*` agents, this one is **in-chat only**. Read the
shared `run-protocol.md` for house-style/data conventions, **but do NOT run its
save-index / log / Asana steps**:

- **No Asana** — never offer to log to Asana (skip §8). The "Key Learning"
  action table renders in the report only.
- **No `/logs` write** (skip §6).
- **No local `reports/` index requirement** — just present the two files in chat.

## Run phases (per build-spec)

1. **Intake — always ask first (build-spec §1).** Collect dates & comparison
   basis, which event mechanics ran (BYOB / AfterSell / Rokt / Order Protection /
   sale collection), and flag which sections need user-provided external data.
   Do not assume dates, comparison basis, or that a mechanic ran. Wait for
   answers before pulling data.
2. **Build (§2–§8).** Pull per the metric/dimension registry with DTC exclusions
   and `comparisonPeriod: "range"`; assemble sections `01…NN` (renumber when a
   conditional section is dropped); run the data-integrity rules.
3. **Deliver (§9–§11).** QA checklist, then generate the HTML dashboard and an
   **A4-landscape PDF** via headless Chromium (not wkhtmltopdf), and present both
   in chat. File naming: `ecom-sale-recap-{event-handle}-YYYY-MM-DD.html` / `.pdf`.

If a needed external input is missing, say what you need for which section and
offer to skip it — never silently omit a section.