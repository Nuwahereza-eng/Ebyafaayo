"""Gemma 4 through the local Ollama HTTP API."""

import json
import time
from typing import Callable, Optional

import httpx
from pydantic import ValidationError

from .config import GEMMA_CTX, GEMMA_MODEL, LANGUAGES, OLLAMA_URL, PROMPTS_DIR
from .schemas import StructuredMemory, gemma_json_schema

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


def structure_transcript(
    transcript: str, speaker: str, language: str = "lug", on_progress: Optional[Callable[[int], None]] = None
) -> tuple[StructuredMemory, dict]:
    """Turn a corrected transcript into a StructuredMemory. Retries once with a fix-the-JSON call."""
    schema = gemma_json_schema()
    prompt = load_prompt("structure.md").format(
        language=LANGUAGES.get(language, language), speaker=speaker, transcript=transcript.strip()
    )
    started = time.time()
    raw = chat(prompt, schema, on_progress)
    meta = {"model": GEMMA_MODEL, "retried": False}
    try:
        memory = StructuredMemory.model_validate_json(raw)
    except ValidationError as e:
        meta["retried"] = True
        fix = load_prompt("fix_json.md").format(error=str(e)[:2000], bad_json=raw)
        raw = chat(fix, schema, on_progress)
        memory = StructuredMemory.model_validate_json(raw)  # second failure propagates
    meta["seconds"] = round(time.time() - started, 1)
    return memory, meta
