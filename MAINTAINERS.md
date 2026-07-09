# Maintaining the PSD Skills Library

This repo is a **plugin marketplace**: one source of truth that serves multiple
domain plugins. Users add the marketplace once and install/update the plugins they
need. Maintainers edit here and push; users pull updates.

## Layout

- `plugins/<psd-domain>/` — one self-contained plugin per domain (its own
  `plugin.json`, `skills/`, and `shared/`).
- `shared-assets/` — the ONE canonical copy of cross-plugin house-style assets
  (e.g. `report-template.html`). Never hand-edit the copies inside a plugin's
  `shared/`; edit here and run the sync.
- `scripts/` — `sync-shared`, `validate`, `package`.
- `.claude-plugin/marketplace.json` — lists every plugin. Add new plugins here.
- `PREFIX-REGISTRY.md` — reserved command prefixes.

## House-style assets (avoid drift)

Plugins must be self-contained, so each carries its own copy of shared assets.
To avoid maintaining N copies:

1. Edit the canonical file in `shared-assets/`.
2. Run `scripts/sync-shared` — it copies `shared-assets/*` into every
   `plugins/*/shared/`.
3. Commit. Plugin-local files (like each plugin's own `run-protocol.md`) are left
   untouched by the sync.

## Add a skill to an existing plugin

1. Create `plugins/<plugin>/skills/<prefix>-<name>/SKILL.md` (copy an existing
   skill as a template; keep the shared-run-protocol reference).
2. Its `name:` frontmatter IS the slash command — use the plugin's prefix.
3. Run `scripts/validate`, then bump the plugin's `version` in its `plugin.json`.

## Add a new domain plugin

1. Claim a prefix in `PREFIX-REGISTRY.md`.
2. Create `plugins/psd-<domain>/` with `.claude-plugin/plugin.json`, `README.md`,
   `shared/`, and `skills/`.
3. Register it in `.claude-plugin/marketplace.json`.
4. Run `scripts/sync-shared` and `scripts/validate`.

## Release / update flow

- Each plugin is versioned independently (semver in its `plugin.json`).
- Tag releases in git, e.g. `psd-ecommerce-v0.5.0`.
- Users update through the marketplace update command. The exact commands to add a
  marketplace and install/update from it are a Claude Code / Cowork product detail
  that changes between releases — confirm current syntax at
  https://docs.anthropic.com/en/docs/claude-code/claude_code_docs_map.md and, for
  the desktop app, https://support.claude.com.

## Surfaces

Installing a plugin (desktop or Claude Code) makes its skills available and, in
testing, they also surface in the claude.ai web/mobile chat via the same account.
Note availability != executability: a skill can appear on web yet run thin unless
the needed connectors (Polar, Asana) are connected in that session.
