#!/usr/bin/env bash
# Build a .plugin zip for each plugin (for manual / web-upload install paths).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/dist"
for plugdir in "$ROOT"/plugins/*/; do
  name="$(basename "$plugdir")"
  ( cd "$plugdir" && zip -qr "/tmp/$name.plugin" . -x "*.DS_Store" )
  cp "/tmp/$name.plugin" "$ROOT/dist/$name.plugin"
  echo "packaged dist/$name.plugin"
done
