"""Gemma 4 through the local Ollama HTTP API."""

import json
import time
from typing import Callable, Optional

import httpx
from pydantic import BaseModel, ValidationError

from .config import GEMMA_CTX, GEMMA_MODEL, LANGUAGES, OLLAMA_URL, PROMPTS_DIR
from .schemas import ExtractPart, StructuredMemory, TextPart, gemma_json_schema

TIMEOUT = httpx.Timeout(connect=10, read=1800, write=60, pool=10)


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def ollama_status() -> dict:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        return {"running": True, "model": GEMMA_MODEL, "model_ready": GEMMA_MODEL in models, "models": models}
    except httpx.HTTPError:
        return {"running": False, "model": GEMMA_MODEL, "model_ready": False, "models": []}


def unload() -> None:
    """Free Gemma's RAM so speech recognition has room (this laptop has 8 GB)."""
    try:
        httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": GEMMA_MODEL, "keep_alive": 0}, timeout=30)
    except httpx.HTTPError:
        pass


def chat(prompt: str, schema: dict, on_progress: Optional[Callable[[int], None]] = None) -> str:
    """Stream one JSON answer from Gemma. `on_progress` gets the number of characters so far."""
    body = {
        "model": GEMMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "format": schema,
        "stream": True,
        "think": False,
        "keep_alive": "5m",
        "options": {"temperature": 0.2, "num_ctx": GEMMA_CTX},
    }
    out: list[str] = []
    count = 0
    with httpx.stream("POST", f"{OLLAMA_URL}/api/chat", json=body, timeout=TIMEOUT) as r:
        if r.status_code != 200:
            raise RuntimeError(f"Ollama error {r.status_code}: {r.read().decode(errors='replace')}")
        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if "error" in chunk:
                raise RuntimeError(f"Ollama error: {chunk['error']}")
            piece = chunk.get("message", {}).get("content", "")
            out.append(piece)
            count += len(piece)
            if on_progress:
                on_progress(count)
    return "".join(out)


def _ask(prompt_file: str, model: type[BaseModel], fields: dict, on_chars: Callable[[int], None]) -> tuple[BaseModel, bool]:
    """One Gemma call that must return `model`. Retries once with a fix-the-JSON call."""
    schema = gemma_json_schema(model)
    raw = chat(load_prompt(prompt_file).format(**fields), schema, on_chars)
    try:
        return model.model_validate_json(raw), False
    except ValidationError as e:
        fix = load_prompt("fix_json.md").format(error=str(e)[:2000], bad_json=raw)
        raw = chat(fix, schema, on_chars)
        return model.model_validate_json(raw), True  # a second failure propagates


def structure_transcript(
    transcript: str, speaker: str, language: str = "lug", on_progress: Optional[Callable[[int], None]] = None
) -> tuple[StructuredMemory, dict]:
    """Turn a corrected transcript into a StructuredMemory.

    Two focused calls work better than one big one with a small model: the first writes the
    clean Luganda and the English translation, the second notes people, places, times and so on.
    """
    fields = {"language": LANGUAGES.get(language, language), "speaker": speaker, "transcript": transcript.strip()}
    started = time.time()
    done = 0

    def progress(n: int) -> None:
        if on_progress:
            on_progress(done + n)

    text, retried_text = _ask("structure_text.md", TextPart, fields, progress)
    done = len(text.model_dump_json())
    extract, retried_extract = _ask("structure_extract.md", ExtractPart, fields, progress)
    memory = StructuredMemory(**text.model_dump(), **extract.model_dump())
    meta = {"model": GEMMA_MODEL, "retried": retried_text or retried_extract, "seconds": round(time.time() - started, 1)}
    return memory, meta
