#!/usr/bin/env bash
# Take README screenshots of a running app (make run) with headless Chrome.
# Usage: scripts/screenshots.sh <person_id> <recording_id> <memory_id>
set -euo pipefail
cd "$(dirname "$0")/.."
BASE=${BASE:-http://127.0.0.1:8000}
OUT=docs/screenshots
mkdir -p "$OUT"
CHROME=${CHROME:-google-chrome}
person=$1 recording=$2 memory=$3

shot() { # name path width height
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check \
    --user-data-dir="$(mktemp -d)" --window-size="$3,$4" --virtual-time-budget=4000 \
    --screenshot="$OUT/$1.png" "$BASE$2" 2>/dev/null
  echo "$OUT/$1.png"
}

shot home / 1280 900
shot record "/record?person=$person" 1280 1300
shot review "/recordings/$recording" 1280 1200
shot memory "/memories/$memory" 1280 2600
shot remembrance "/people/$person" 1280 2200
shot book "/book?person=$person" 1280 2000
shot memory-mobile "/memories/$memory" 390 2400
