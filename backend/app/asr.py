"""Speech to text with Sunbird's open Whisper model (asr-whisper-large-v3-salt).

The model is converted once to CTranslate2 int8 (scripts/convert_asr.py) and run with
faster-whisper, so it fits in about 1.5 GB of RAM on a laptop CPU. Long audio is cut into
pieces of at most 30 seconds, at the quietest moment near each cut, so words are not split.
"""

import gc
import json
from typing import Callable, Optional

import numpy as np

from .config import ASR_MODEL_DIR, ASR_THREADS, CHUNK_SECONDS

SAMPLE_RATE = 16000
_model = None


def asr_status() -> dict:
    ready = (ASR_MODEL_DIR / "model.bin").exists()
    return {"model": "Sunbird/asr-whisper-large-v3-salt (CTranslate2 int8)", "ready": ready, "path": str(ASR_MODEL_DIR)}


def language_codes() -> dict[str, str]:
    """SALT language code -> the Whisper language token the Sunbird model uses for it.

    Written by the conversion script from the model's own tokenizer and the token ids on the
    Sunbird model card (Luganda is token 50355), so nothing here is guessed.
    """
    return json.loads((ASR_MODEL_DIR / "salt_languages.json").read_text())


def _load():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(str(ASR_MODEL_DIR), device="cpu", compute_type="int8", cpu_threads=ASR_THREADS)
    return _model


def release() -> None:
    """Drop the model so Gemma has room in RAM."""
    global _model
    _model = None
    gc.collect()


def split_chunks(audio: np.ndarray, max_s: int = CHUNK_SECONDS, search_s: int = 5) -> list[np.ndarray]:
    max_len, search = max_s * SAMPLE_RATE, search_s * SAMPLE_RATE
    frame = SAMPLE_RATE // 50  # 20 ms
    chunks, start = [], 0
    while len(audio) - start > max_len:
        window = audio[start + max_len - search : start + max_len]
        n = len(window) // frame
        energy = (window[: n * frame].reshape(n, frame) ** 2).mean(axis=1)
        cut = start + max_len - search + int(np.argmin(energy)) * frame
        chunks.append(audio[start:cut])
        start = cut
    chunks.append(audio[start:])
    return [c for c in chunks if len(c) > SAMPLE_RATE // 4]


def load_chunks(wav_path: str) -> list[np.ndarray]:
    from faster_whisper.audio import decode_audio

    return split_chunks(decode_audio(wav_path, sampling_rate=SAMPLE_RATE))


def transcribe_chunk(chunk: np.ndarray, language: str = "lug", on_segment: Optional[Callable[[], None]] = None) -> str:
    """One piece of at most 30 seconds. `on_segment` is called after each sentence the model hears."""
    segments, _ = _load().transcribe(
        chunk,
        language=language_codes()[language],
        beam_size=5,
        condition_on_previous_text=False,
        vad_filter=False,
    )
    texts = []
    for s in segments:  # a generator: the model works as we read it
        texts.append(s.text.strip())
        if on_segment:
            on_segment()
    return " ".join(texts).strip()


def transcribe(wav_path: str, language: str = "lug", on_progress: Optional[Callable[[float], None]] = None) -> str:
    chunks = load_chunks(wav_path)
    texts = []
    for i, chunk in enumerate(chunks):
        texts.append(transcribe_chunk(chunk, language))
        if on_progress:
            on_progress((i + 1) / len(chunks))
    return "\n".join(t for t in texts if t)
