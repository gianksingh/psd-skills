# Agent / maintainer instructions (PSD Skills)

This repo is a **Claude plugin marketplace**. Follow this checklist on **every** plugin
change so Cowork accepts the build and users get updates.

See also `MAINTAINERS.md` (layout, sync-shared, prefixes).

---

## Cowork description limits (hard failures)

Enforced by `scripts/validate.py` — run before every commit.

| Field | File | Max chars |
| ----- | ---- | --------- |
| Plugin `description` | `plugins/<plugin>/.claude-plugin/plugin.json` | **500** |
| Skill `description` | `plugins/<plugin>/skills/*/SKILL.md` frontmatter | **1024** |

- Skill `description` may be one line or a folded block (`description: >`). The limit
  applies to the **full text** (spaces joined), not YAML line length.
- Long triggers and routing belong in the skill **body**, not the frontmatter
  `description`.
- `README.md` and `marketplace.json` command lists are not validated by Cowork but should
  stay in sync when you add or rename a skill.

---

## Release checklist (required)

Do all of this **in one push** when shipping a plugin update:

1. **Change** — skills, shared assets, indexes (`README.md`,
   `.claude-plugin/marketplace.json` command list, `plugin.json` description if needed).
2. **Sync** — if `shared-assets/` changed: `bash scripts/sync-shared.sh`.
3. **Validate** — `python3 scripts/validate.py` (must PASS).
4. **Bump versions**
   - `plugins/<plugin>/.claude-plugin/plugin.json` → semver (`patch` fixes, `minor` new
     skill or meaningful capability, `major` breaking).
   - `.claude-plugin/marketplace.json` → `metadata.version` (bump **patch** with each
     plugin release, e.g. `1.1.1` → `1.1.2`).
5. **Commit** on `main` with a clear message (`feat`, `fix`, `chore`, etc.).
6. **Tag** (annotated, name must match plugin version):
   ```bash
   VER=1.9.1  # same as plugin.json
   PLUGIN=psd-ecommerce
   git tag -a "${PLUGIN}-v${VER}" -m "${PLUGIN} v${VER} — <one-line summary>"
   git push origin main
   git push origin "${PLUGIN}-v${VER}"
   ```

Pushing **only** `main` without the matching **`psd-ecommerce-vX.Y.Z`** tag often means
Cowork never surfaces the update (even when the commit is on GitHub). Tags are required,
not optional.

Do **not** commit `dist/*.plugin` unless you intentionally ship a manual zip; the
marketplace installs from the repo tree.

---

## Add or update a skill (quick)

1. Skill folder under `plugins/<plugin>/skills/<name>/` with `SKILL.md` (`name:` = slash
   command).
2. Register in README agents table + `marketplace.json` description command list.
3. Run validate → bump `plugin.json` (+ `metadata.version`) → commit → **tag** → push.

---

## Version / tag examples

| Change | plugin.json | Tag |
| ------ | ----------- | --- |
| New skill (`mix-match-report`) | minor → `1.9.0` | `psd-ecommerce-v1.9.0` |
| Validation / copy trim | patch → `1.9.1` | `psd-ecommerce-v1.9.1` |
| Ops flash harness refresh | minor → `1.8.0` | `psd-ecommerce-v1.8.0` |