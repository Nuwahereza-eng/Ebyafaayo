"""Settings. Everything points at this laptop; nothing here talks to the internet."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("EBYAFAAYO_DATA", ROOT / "data"))
AUDIO_DIR = DATA_DIR / "audio"
PHOTO_DIR = DATA_DIR / "photos"
DB_PATH = DATA_DIR / "ebyafaayo.db"
PROMPTS_DIR = ROOT / "backend" / "prompts"
FRONTEND_DIST = ROOT / "frontend" / "dist"

# A public demo server (see render.yaml): sample data, a banner, no deleting, small limits.
DEMO = os.environ.get("EBYAFAAYO_DEMO") == "1"

# Speech to text: Sunbird's open Whisper model, converted once to CTranslate2 int8
# by scripts/convert_asr.py so it fits in laptop RAM.
ASR_MODEL_DIR = Path(os.environ.get("EBYAFAAYO_ASR_DIR", ROOT / "models" / "sunbird-asr-whisper-large-v3-salt-ct2-int8"))
ASR_THREADS = int(os.environ.get("EBYAFAAYO_ASR_THREADS", os.cpu_count() or 4))
CHUNK_SECONDS = 30

# Gemma 4 through a local Ollama server.
OLLAMA_URL = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
GEMMA_MODEL = os.environ.get("EBYAFAAYO_GEMMA", "gemma4:e2b")
GEMMA_CTX = int(os.environ.get("EBYAFAAYO_GEMMA_CTX", 8192))

# Languages the Sunbird model was trained on (codes from its model card).
LANGUAGES = {
    "lug": "Luganda",
    "eng": "English",
    "nyn": "Runyankole",
    "ttj": "Rutooro",
    "xog": "Lusoga",
    "ach": "Acholi",
    "lgg": "Lugbara",
    "teo": "Ateso",
    "myx": "Lumasaba",
    "swa": "Swahili",
    "kin": "Kinyarwanda",
}

for d in (AUDIO_DIR, PHOTO_DIR):
    d.mkdir(parents=True, exist_ok=True)
