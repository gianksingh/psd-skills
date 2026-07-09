# Shared Assets (canonical)

The single source of truth for cross-plugin house-style assets. Edit files HERE,
then run `../scripts/sync-shared` to propagate copies into every plugin's
`shared/` folder. Never hand-edit the copies inside plugins.

- `report-template.html` — the unified stylesheet + component library for ALL PSD
  reports (sale-recap and the weekly agents). Copy its `<style>` verbatim and its
  component markup per run.
