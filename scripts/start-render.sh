#!/usr/bin/env bash
# Starts the public demo in one container: Ollama with Gemma 4, a Temporal dev server, and the app.
# Everything talks over 127.0.0.1; only the app's port is public. /data is Render's persistent disk.
set -euo pipefail
mkdir -p "$EBYAFAAYO_DATA" "$OLLAMA_MODELS"

if command -v ollama >/dev/null; then
  OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 ollama serve > /tmp/ollama.log 2>&1 &
  # Gemma is a 4.6 GB download. Fetch it in the background on the first start, so the site comes
  # up at once; the app shows "Gemma not ready" until it is there. Later starts find it on the disk.
  (
    until curl -sf 127.0.0.1:11434/api/version > /dev/null; do sleep 1; done
    ollama pull "$EBYAFAAYO_GEMMA" > /tmp/ollama-pull.log 2>&1 && echo "Gemma is ready: $EBYAFAAYO_GEMMA"
  ) &
fi

temporal server start-dev --ip 127.0.0.1 --port 7233 --headless \
  --db-filename /data/temporal.db --log-level warn &
for _ in $(seq 1 30); do (echo > /dev/tcp/127.0.0.1/7233) 2> /dev/null && break; sleep 1; done

cd /app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
