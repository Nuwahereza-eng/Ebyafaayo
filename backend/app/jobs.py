"""Slow work: transcribing a story, writing a memory with Gemma, describing a photo.

Each job is a few steps, and each step saves its result. With a local Temporal server running
(see durable.py), the steps run as a durable workflow: if the laptop runs out of memory or the
app is closed half way, the job picks up at the step it was on. Without Temporal, the same steps
run one after another in a background thread, and an interrupted job is marked failed.

Only one heavy step runs at a time: an 8 GB laptop cannot hold the speech model and Gemma together.
"""

import shutil
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from sqlmodel import Session, select

from . import asr, llm
from .config import AUDIO_DIR
from .db import Memory, Person, Photo, Recording, engine, now
from .grounding import ground, remove_names, similarity
from .schemas import ExtractPart, StructuredMemory, TextPart

executor = ThreadPoolExecutor(max_workers=1)

Beat = Optional[Callable[[], None]]  # called while a step is working, so Temporal knows it is alive


def _update(table, id_: int, **fields) -> None:
    with Session(engine) as s:
        obj = s.get(table, id_)
        if obj is None:  # deleted by the family while the job ran
            return
        for k, v in fields.items():
            setattr(obj, k, v)
        s.add(obj)
        s.commit()


def mark_failed(kind: str, id_: int, error: str) -> None:
    table = {"transcribe": Recording, "memory": Memory, "photo": Photo}[kind]
    _update(table, id_, status="failed", error=error)


# ---------- transcription: prepare, then one step per 30-second piece, then finish ----------


def _chunk_dir(recording_id: int) -> Path:
    return AUDIO_DIR / "chunks" / f"rec-{recording_id}"


def prepare_transcription(recording_id: int) -> int:
    """Cut the audio into pieces and save them, so each piece can be retried on its own."""
    with Session(engine) as s:
        wav = s.get(Recording, recording_id).wav_path
    _update(Recording, recording_id, status="transcribing", progress=0.0, error="")
    llm.unload()  # free Gemma's RAM for the speech model
    folder = _chunk_dir(recording_id)
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    chunks = asr.load_chunks(wav)
    for i, chunk in enumerate(chunks):
        np.save(folder / f"{i:03d}.npy", chunk)
    return len(chunks)


def transcribe_piece(recording_id: int, index: int, total: int, beat: Beat = None) -> str:
    with Session(engine) as s:
        language = s.get(Recording, recording_id).language
    chunk = np.load(_chunk_dir(recording_id) / f"{index:03d}.npy")
    text = asr.transcribe_chunk(chunk, language, on_segment=beat)
    _update(Recording, recording_id, progress=(index + 1) / total)
    return text


def finish_transcription(recording_id: int, texts: list[str]) -> None:
    text = "\n".join(t for t in texts if t)
    _update(Recording, recording_id, status="transcribed", progress=1.0, transcript_raw=text, transcript=text,
            asr_model=asr.asr_status()["model"])
    asr.release()
    shutil.rmtree(_chunk_dir(recording_id), ignore_errors=True)


# ---------- a memory: Gemma writes the story, then finds the details, then we check and save ----------


def _story_fields(memory_id: int) -> dict:
    with Session(engine) as s:
        mem = s.get(Memory, memory_id)
        rec = s.get(Recording, mem.recording_id)
        person = s.get(Person, mem.person_id)
        return llm.story_fields(rec.transcript, rec.speaker_name or person.name, rec.language)


def _progress(table, id_: int, offset: int, beat: Beat) -> Callable[[int], None]:
    last = [0.0]

    def on_chars(n: int) -> None:
        if time.time() - last[0] > 1:  # a database write per token would slow Gemma down
            last[0] = time.time()
            _update(table, id_, progress_chars=offset + n)
            if beat:
                beat()

    return on_chars


def gemma_write_story(memory_id: int, beat: Beat = None) -> dict:
    """Step 1: the clean Luganda text and the English translation."""
    started = time.time()
    text, retried = llm.write_story(_story_fields(memory_id), _progress(Memory, memory_id, 0, beat))
    return {"part": text.model_dump(), "retried": retried, "seconds": time.time() - started}


def gemma_find_details(memory_id: int, done_chars: int, beat: Beat = None) -> dict:
    """Step 2: the people, places, times, proverbs, clan, totem and follow-up questions."""
    started = time.time()
    extract, retried = llm.find_details(_story_fields(memory_id), _progress(Memory, memory_id, done_chars, beat))
    return {"part": extract.model_dump(), "retried": retried, "seconds": time.time() - started}


def check_and_save_memory(memory_id: int, story: dict, details: dict) -> None:
    """Step 3: check every item against the transcript, then save the draft for the family."""
    transcript = _story_fields(memory_id)["transcript"]
    structured = StructuredMemory(**TextPart(**story["part"]).model_dump(), **ExtractPart(**details["part"]).model_dump())
    structured, notes = ground(structured, transcript)
    data = structured.model_dump()
    data["notes"] = notes
    data["luganda_similarity"] = similarity(structured.luganda_text, transcript)
    data["retried"] = story["retried"] or details["retried"]
    _update(Memory, memory_id, status="draft", title=structured.title, data=data, model=llm.GEMMA_MODEL,
            generation_seconds=round(story["seconds"] + details["seconds"], 1), updated_at=now())


# ---------- a photo: Gemma describes it, then we remove any names and save ----------


def gemma_describe_photo(photo_id: int, beat: Beat = None) -> None:
    with Session(engine) as s:
        photo = s.get(Photo, photo_id)
        person = s.get(Person, photo.person_id)
        path, name = photo.path, person.name
        known = [name] + [p.name for p in s.exec(select(Person))]
        for m in s.exec(select(Memory).where(Memory.person_id == person.id)):
            known += [p["name"] for p in (m.data or {}).get("people", [])]
    _update(Photo, photo_id, status="describing", error="", progress_chars=0)
    part, meta = llm.describe_photo(path, name, _progress(Photo, photo_id, 0, beat))
    description, notes = remove_names(part.description, known)
    _update(Photo, photo_id, status="ready", description=description, notes=notes,
            questions=[q.model_dump() for q in part.questions], model=meta["model"], generation_seconds=meta["seconds"])


# ---------- running the steps without Temporal ----------


def _run_in_thread(kind: str, id_: int) -> None:
    try:
        if kind == "transcribe":
            try:
                total = prepare_transcription(id_)
                finish_transcription(id_, [transcribe_piece(id_, i, total) for i in range(total)])
            finally:
                asr.release()
        elif kind == "memory":
            story = gemma_write_story(id_)
            details = gemma_find_details(id_, len(str(story["part"])))
            check_and_save_memory(id_, story, details)
        elif kind == "photo":
            gemma_describe_photo(id_)
    except Exception as e:  # shown to the family as "failed", with a retry button
        traceback.print_exc()
        mark_failed(kind, id_, str(e))


def start(kind: str, id_: int) -> str:
    """Start a job: as a durable Temporal workflow if the server is up, otherwise in a thread."""
    from . import durable

    if durable.runner.ready:
        durable.runner.start(kind, id_)
        return "temporal"
    executor.submit(_run_in_thread, kind, id_)
    return "thread"
