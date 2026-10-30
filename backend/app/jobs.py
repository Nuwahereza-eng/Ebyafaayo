"""Slow work (transcribing, structuring) runs one job at a time in a background thread.

One at a time on purpose: an 8 GB laptop cannot hold the speech model and Gemma together.
"""

import traceback
from concurrent.futures import ThreadPoolExecutor

from sqlmodel import Session

from . import asr, llm
from .db import Memory, Person, Recording, engine, now
from .grounding import ground, similarity

executor = ThreadPoolExecutor(max_workers=1)


def _update(model, id_: int, **fields) -> None:
    with Session(engine) as s:
        obj = s.get(model, id_)
        for k, v in fields.items():
            setattr(obj, k, v)
        s.add(obj)
        s.commit()


def run_transcription(recording_id: int) -> None:
    with Session(engine) as s:
        rec = s.get(Recording, recording_id)
        wav, language = rec.wav_path, rec.language
    _update(Recording, recording_id, status="transcribing", progress=0.0, error="")
    try:
        llm.unload()
        text = asr.transcribe(wav, language, on_progress=lambda p: _update(Recording, recording_id, progress=p))
        _update(
            Recording,
            recording_id,
            status="transcribed",
            progress=1.0,
            transcript_raw=text,
            transcript=text,
            asr_model=asr.asr_status()["model"],
        )
    except Exception as e:  # shown to the family as "failed", with a retry button
        traceback.print_exc()
        _update(Recording, recording_id, status="failed", error=str(e))
    finally:
        asr.release()


def run_structuring(memory_id: int) -> None:
    with Session(engine) as s:
        mem = s.get(Memory, memory_id)
        rec = s.get(Recording, mem.recording_id)
        person = s.get(Person, mem.person_id)
        transcript, speaker, language = rec.transcript, rec.speaker_name or person.name, rec.language
    try:
        structured, meta = llm.structure_transcript(
            transcript, speaker, language, on_progress=lambda n: _update(Memory, memory_id, progress_chars=n)
        )
        structured, notes = ground(structured, transcript)
        data = structured.model_dump()
        data["notes"] = notes
        data["luganda_similarity"] = similarity(structured.luganda_text, transcript)
        data["retried"] = meta["retried"]
        _update(
            Memory,
            memory_id,
            status="draft",
            title=structured.title,
            data=data,
            model=meta["model"],
            generation_seconds=meta["seconds"],
            updated_at=now(),
        )
    except Exception as e:
        traceback.print_exc()
        _update(Memory, memory_id, status="failed", error=str(e))


def submit(fn, *args) -> None:
    executor.submit(fn, *args)
