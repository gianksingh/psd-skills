# PSD Agent Run Protocol (shared)

Every PSD agent follows this protocol. The individual SKILL.md provides the
agent-specific analysis spec; this file provides the shared steps that wrap it:
where data comes from, how the report is scoped, how it's styled, and what to do
after the report is built (save it, log the run, then offer to log action items to Asana).

Read this file in full when any PSD agent skill fires, then execute the
agent-specific analysis, then run the delivery steps below in order.

---

## 1. Data sources

Use the **Polar Analytics MCP** as the primary source for all metrics. Polar
already aggregates Shopify, Meta, Google, TikTok, Klaviyo, Amazon and GA4, so a
single source covers nearly everything an agent needs. Begin by calling Polar's
`get_context` to get the conversation id and confirm the account is activated and
data is ready; if Polar returns a "book the setup call" or "connect data sources"
message, surface it to the user and stop.

Backfill from other connected MCPs only when an agent's spec explicitly allows it
or when Polar genuinely cannot answer (e.g. Klaviyo/Shopify for retention detail,
Microsoft Clarity or the live psd.com store for CRO qualitative input). Prefer
Polar for anything quantitative.

## 2. Scoping & filters (DTC by default)

**Sales-channel attribution — preferred dimension.** Whenever you need to decide
which sales channel an order belongs to — for DTC scoping, the Sales by Channel
breakdown, or any per-channel metric — **prefer the custom dimension "Sales
Channel (PSD Unified)"** (Polar custom dimension, gid `custom_5794`; it may
display in Polar as "Sales Channel (Unified)"). It applies PSD's own
consolidation rules and is more reliable for attribution than the raw
`sales_channel_name` / `sales_channel` fields. Only fall back to
`sales_channel_name` if the unified dimension isn't available for the chosen
metrics, and note it if you do.

Unless the agent's spec explicitly asks for TikTok Shop or Amazon data, every
metric must represent the **DTC business only**. Apply the DTC exclusion on the
preferred unified dimension, removing the values that represent the **TikTok
Shop** and **aftersell** channels. If you're unsure of the exact value labels,
inspect them first with Polar's `get_dimension_values`. Use a **nested array
(AND logic)** so every exclusion applies (a flat array is OR and will NOT exclude
correctly), e.g.:

    {"custom_5794":[[{"value":["TikTok Shop"],"operator":"ISNOT"},{"value":["aftersell"],"operator":"NOTCONTAINS"}]]}

If you must fall back to the raw field, apply the same nested-array shape to
`sales_channel_name` (e.g. NOTCONTAINS "tiktok" AND NOTCONTAINS "aftersell").
Amazon is a separate connector (not a Shopify sales channel), so Shopify metrics
already exclude it. Where an agent explicitly reports TikTok Shop or Amazon as
their own line items, pull those separately and label them clearly; keep DTC
figures clean everywhere else.

Prefer **Adjusted Net Sales** (`custom_60202`) as the headline revenue metric. If
you fall back to total sales or revenue, say so explicitly.

## 3. Comparison windows

Default to **last 7 complete days vs the prior 7 days** unless the agent's spec
says otherwise (some expand to 30-day or YoY). Use Polar's `comparisonPeriod:
previousPeriod`. Always state the exact date ranges compared in the report header,
anchored to today's date.

## 4. Build the report (unified house style — non-negotiable)

The report's look is FIXED by the shared template. You choose which sections appear
and their order for this agent; you do NOT choose the styling.

STEP 1 — Copy the stylesheet verbatim. Open
`${CLAUDE_PLUGIN_ROOT}/shared/report-template.html` and copy everything between
`<style>` and `</style>` verbatim into a single `<style>` in the report `<head>`.
Do NOT write, edit, "improve", or add any CSS. Do NOT introduce class names or CSS
variables that aren't already in that block. If you cannot open the file, STOP and
tell the user — never improvise a stylesheet.

STEP 2 — Build from the template's components. Copy component markup from the same
file's gallery and fill the {{...}} tokens, reusing its classes only: flagstrip,
hero + period-pills + headline, sechead, lead, kpi-grid/kpi + delta p|n|z, split +
panel, tables with ibar/cellbar, funnel/fstep, prod-grid, goalbar, cards2 + item
win|risk, act/actrow, callout, foot, and the map module (.psd-map-module). Add,
drop, or reorder SECTIONS to fit this agent — but never create new component styling.

STEP 3 — Self-check before finishing. Confirm the report contains, at minimum,
`.flagstrip`, `.hero`, `.sechead`, and `.kpi`. If any are missing you did not use
the template — redo Step 1. Then produce the PDF per the existing recipe.

Name the files `[agent-handle]-[YYYY-MM-DD].html` / `.pdf` using the report's end
date. **PDF — render the finished HTML with headless Chromium (not WeasyPrint),
honoring the template's `@media print` CSS:**

- **Primary document PDF = one continuous page** (no pagination gaps): render at
  1200px width, measure `document.documentElement.scrollHeight`, and emit a single
  page that tall — `page.pdf(width='1200px', height=f'{h}px', print_background=True,
  margin={'top':'0','right':'0','bottom':'0','left':'0'})`.
- **Optional 16:9 deck PDF** for screensharing: set `body.mode-deck`, then
  `page.pdf(width='13.333in', height='7.5in', landscape=True, print_background=True)`
  (one section per slide).

Verify each PDF is non-empty before moving on.

## 5. Save & index the reports

Save the finished HTML and PDF into the connected project folder at
`reports/[agent-handle]/` (create folders as needed). Then update a simple local
index at `reports/index.html` (in the same house style) that lists reports for
each agent type, **newest first**, each entry linking to its HTML file with a PDF
link alongside. If the project folder isn't accessible, note that in your
hand-back and still present the files in chat.

## 6. Log the run

Write a short `.md` file into the project `logs/` folder to help future runs:
which Polar metric keys/queries worked, any Asana field gids/enum values used, the
saved report path, data gaps/gotchas, and headline numbers for trend continuity.
Name it `[agent-handle]-[YYYY-MM-DD].md`. If the project folder isn't accessible,
note that in your final message instead.

## 7. Hand back to the user

Present the HTML and PDF reports with a 2-3 sentence summary: the headline result
and where the reports were saved. Keep it concise.

## 8. Offer to log action items to Asana (ask first)

Do **not** create Asana tasks automatically. After the report is presented, ask
the user, e.g.: *"Would you like me to log any of these action items to Asana?"*
Only if the user confirms — and they may pick a subset — create the tasks.

When creating tasks, use the **Asana MCP** in this project:
`https://app.asana.com/1/1205387473266253/project/1215253687291387/board/1215253640480726`
(project gid `1215253687291387`). First read the project (`asana_get_project` with
custom field opt_fields) to learn the exact custom-field gids and enum option gids,
because they may differ per workspace. This project's fields are: **Priority**
(High/Medium/Low), **AI Agent** (Manager / Ad Specialist / Retention Marketer /
Merchandiser / Price Analyst / CRO / Finance Analyst), **Business Unit** (CRO /
Retention / Finance / Paid Ads / Merch & Pricing / Other), and **Status** (set to
**Needs Human Review**).

For each action item set: **Name** (action title), **Priority** (map P0->High,
P1->Medium, P2->Low), **AI Agent** (this agent - each skill states its value),
**Business Unit** (closest match to the owner function), and **Status = Needs Human
Review**. The project has no Owner / Impact Metric / Review Notes fields, so put
**Owner**, **Impact Metric**, and **Review Notes** in the task **notes**.
