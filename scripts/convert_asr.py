"""One-time setup: convert Sunbird/asr-whisper-large-v3-salt to CTranslate2 int8 for faster-whisper.

Why: the original model is 6.2 GB of float32 weights and needs about 6 GB of RAM in transformers.
The int8 conversion is about 1.6 GB, runs several times faster on a laptop CPU, and keeps the same
Sunbird weights (quantised). The model is gated on Hugging Face: accept its terms and run
`hf auth login` first.

Needs: pip install -r scripts/requirements-convert.txt
Usage: python scripts/convert_asr.py [--keep-download]
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import ASR_MODEL_DIR  # noqa: E402

MODEL_ID = "Sunbird/asr-whisper-large-v3-salt"

# Token ids copied from the Sunbird model card (https://salt.sunbird.ai/models/asr-whisper-large-v3-salt/).
SALT_LANGUAGE_TOKENS_WHISPER = {
    "eng": 50259,  # English (Ugandan)
    "swa": 50318,  # Swahili
    "ach": 50357,  # Acholi
    "lgg": 50356,  # Lugbara
    "lug": 50355,  # Luganda
    "nyn": 50354,  # Runyankole
    "teo": 50353,  # Ateso
    "xog": 50352,  # Lusoga
    "ttj": 50351,  # Rutooro
    "kin": 50350,  # Kinyarwanda
    "myx": 50349,  # Lumasaba
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-download", action="store_true", help="keep the 6.2 GB original in the HF cache")
    args = parser.parse_args()

    from ctranslate2.converters import TransformersConverter
    from huggingface_hub import scan_cache_dir, snapshot_download
    from transformers import WhisperProcessor

    if (ASR_MODEL_DIR / "model.bin").exists():
        print(f"Already converted: {ASR_MODEL_DIR}")
        return

    free_gb = shutil.disk_usage(ROOT).free / 1e9
    print(f"Free disk: {free_gb:.1f} GB (the download needs 6.2 GB, the result 1.6 GB)")

    print(f"Downloading {MODEL_ID} ...")
    src = snapshot_download(MODEL_ID, allow_patterns=["*.json", "*.txt", "*.safetensors"])

    print("Converting to CTranslate2 int8 (loads the weights as float16 to save RAM) ...")
    tmp = ASR_MODEL_DIR.with_name(ASR_MODEL_DIR.name + ".partial")
    shutil.rmtree(tmp, ignore_errors=True)
    TransformersConverter(src, copy_files=["preprocessor_config.json"], load_as_float16=True, low_cpu_mem_usage=True).convert(
        str(tmp), quantization="int8", force=True
    )

    # faster-whisper needs tokenizer.json; without it, it would fetch a different tokenizer from the internet.
    processor = WhisperProcessor.from_pretrained(src)
    processor.tokenizer.backend_tokenizer.save(str(tmp / "tokenizer.json"))

    # Map each SALT language to the Whisper language code whose token the Sunbird model uses for it.
    languages = {}
    for code, token_id in SALT_LANGUAGE_TOKENS_WHISPER.items():
        token = processor.tokenizer.convert_ids_to_tokens(token_id)  # e.g. "<|xx|>"
        languages[code] = token.strip("<|>")
    (tmp / "salt_languages.json").write_text(json.dumps(languages, indent=2))
    print("Language tokens:", languages)

    tmp.rename(ASR_MODEL_DIR)
    print(f"Done: {ASR_MODEL_DIR}")

    if not args.keep_download:
        for repo in scan_cache_dir().repos:
            if repo.repo_id == MODEL_ID:
                scan_cache_dir().delete_revisions(*[r.commit_hash for r in repo.revisions]).execute()
                print("Removed the original download from the Hugging Face cache.")


if __name__ == "__main__":
    main()
