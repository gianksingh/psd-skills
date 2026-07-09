# Command Prefix Registry

Every skill's command is `<prefix>-<skill>`. The prefix maps 1:1 to a plugin/domain
so commands never collide as the library grows. Claim a prefix here before adding a
new domain plugin.

| Prefix  | Domain              | Plugin           | Status   |
| ------- | ------------------- | ---------------- | -------- |
| `ecom`  | Ecommerce / DTC     | `psd-ecommerce`  | Active   |
| `mkt`   | Marketing           | `psd-marketing`  | Reserved |
| `fin`   | Org / corp finance  | `psd-finance`    | Reserved |
| `ops`   | Operations          | `psd-ops`        | Reserved |
| `ret`   | Retail / wholesale  | `psd-retail`     | Reserved |

Rules:
- Prefixes are 2-4 lowercase letters, no numbers.
- One prefix per plugin. Do not reuse a prefix across plugins.
- Keep skill names short and typeable: `<prefix>-<verb-or-noun>` (e.g. `ecom-ads`).
- `fin` (corp finance) is deliberately distinct from `ecom-finance` (ecommerce P&L).
