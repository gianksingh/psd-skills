#!/usr/bin/env bash
# Copy canonical house-style assets from shared-assets/ into every plugin's shared/.
# Plugin-local files (e.g. each plugin's run-protocol.md) are left untouched.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
shopt -s nullglob
for asset in "$ROOT"/shared-assets/*; do
  base="$(basename "$asset")"
  [ "$base" = "README.md" ] && continue
  for plugdir in "$ROOT"/plugins/*/; do
    mkdir -p "$plugdir/shared"
    cp "$asset" "$plugdir/shared/$base"
    echo "synced $base -> $(basename "$plugdir")/shared/"
  done
done
echo "sync-shared complete."
