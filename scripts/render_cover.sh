#!/usr/bin/env bash
# Render the DEV cover image (1000×420, saved at 2× for sharpness) with headless Chrome.
set -euo pipefail
cd "$(dirname "$0")/.."
${CHROME:-google-chrome} --headless=new --disable-gpu --hide-scrollbars --no-first-run \
  --allow-file-access-from-files --user-data-dir="$(mktemp -d)" \
  --window-size=1000,420 --force-device-scale-factor=2 --virtual-time-budget=3000 \
  --screenshot="$PWD/docs/cover/cover.png" "file://$PWD/docs/cover/cover.html" 2>/dev/null
echo docs/cover/cover.png
