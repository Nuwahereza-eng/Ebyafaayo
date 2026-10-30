#!/usr/bin/env bash
# One-command setup for Ebyafaayo. Installs the app; the models are separate steps
# (make gemma, make asr-model) because they are large downloads.
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null || { echo "Please install $1 first. $2"; exit 1; }; }
need python3 "Python 3.11 or newer."
need ffmpeg "On Ubuntu: sudo apt install ffmpeg"
need npm "Node.js 20 or newer: https://nodejs.org (or nvm)."

echo "==> Python environment"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r backend/requirements.txt pytest

echo "==> Web app"
(cd frontend && npm ci --silent && npm run build --silent)

echo
if command -v ollama >/dev/null; then
  echo "Ollama found. Next: make gemma"
else
  echo "Next: install Ollama (https://ollama.com/download), then: make gemma"
fi
echo "Then accept the terms at https://huggingface.co/Sunbird/asr-whisper-large-v3-salt,"
echo "run: .venv/bin/hf auth login   and: make asr-model"
echo "Finally: make run   and open http://127.0.0.1:8000"
