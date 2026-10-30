"""Ebyafaayo API. Runs on localhost only; makes no requests outside this laptop."""

import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from . import asr, durable, jobs, llm
from .audio import duration_seconds, to_wav16k
from .config import AUDIO_DIR, FRONTEND_DIST, LANGUAGES, PHOTO_DIR
from .db import Memory, Person, Photo, Recording, get_session, init_db, now
from .grounding import normalize

app = FastAPI(title="Ebyafaayo", docs_url="/api/docs", openapi_url="/api/openapi.json")

CONSENT_TEXT = (
    "{speaker} agrees to be recorded telling this story. The recording stays on this computer. "
    "It is not uploaded anywhere. The family can delete it at any time."
)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    await durable.runner.connect()
    # Jobs Temporal is still running carry on where they stopped; others are marked for a retry.
    resumed = await durable.recover()
    if resumed:
        print(f"Resuming {len(resumed)} job(s) with Temporal: {', '.join(resumed)}")


@app.on_event("shutdown")
async def shutdown() -> None:
    await durable.runner.stop()


# ---------- status ----------


@app.get("/api/status")
def status():
    return {
        "asr": asr.asr_status(),
        "gemma": llm.ollama_status(),
        "jobs": durable.runner.status(),
        "languages": LANGUAGES,
        "consent_text": CONSENT_TEXT,
        "privacy": "Everything runs on this computer. No analytics, no telemetry, no cloud AI.",
    }


# ---------- people ----------


class PersonIn(BaseModel):
    name: str
    relationship: str = ""
    years: str = ""
    about: str = ""


def person_out(p: Person, s: Session) -> dict:
    stories = s.exec(select(Memory).where(Memory.person_id == p.id, Memory.status == "saved")).all()
    d = p.model_dump()
    d["story_count"] = len(stories)
    d["photo_url"] = f"/api/people/{p.id}/photo" if p.photo_path else None
    return d


@app.get("/api/people")
def list_people(s: Session = Depends(get_session)):
    return [person_out(p, s) for p in s.exec(select(Person).order_by(Person.name)).all()]


@app.post("/api/people")
def create_person(body: PersonIn, s: Session = Depends(get_session)):
    p = Person(**body.model_dump())
    s.add(p)
    s.commit()
    s.refresh(p)
    return person_out(p, s)


@app.patch("/api/people/{person_id}")
def update_person(person_id: int, body: PersonIn, s: Session = Depends(get_session)):
    p = s.get(Person, person_id) or _404()
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    s.add(p)
    s.commit()
    return person_out(p, s)


@app.post("/api/people/{person_id}/photo")
def upload_photo(person_id: int, photo: UploadFile = File(...), s: Session = Depends(get_session)):
    p = s.get(Person, person_id) or _404()
    ext = Path(photo.filename or "").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(400, "Please use a JPG, PNG or WebP photo.")
    dst = PHOTO_DIR / f"person-{person_id}-{uuid.uuid4().hex[:8]}{ext}"
    with dst.open("wb") as f:
        shutil.copyfileobj(photo.file, f)
    p.photo_path = str(dst)
    s.add(p)
    s.commit()
    return person_out(p, s)


@app.get("/api/people/{person_id}/photo")
def get_photo(person_id: int, s: Session = Depends(get_session)):
    p = s.get(Person, person_id) or _404()
    if not p.photo_path:
        _404()
    return FileResponse(p.photo_path)


# ---------- old family photos: Gemma describes them, the family says who is in them ----------

PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".webp"}


def photo_out(p: Photo) -> dict:
    d = p.model_dump(exclude={"path"})
    d["url"] = f"/api/photos/{p.id}/image"
    return d


@app.post("/api/people/{person_id}/photos")
def add_family_photo(person_id: int, photo: UploadFile = File(...), s: Session = Depends(get_session)):
    s.get(Person, person_id) or _404()
    ext = Path(photo.filename or "").suffix.lower() or ".jpg"
    if ext not in PHOTO_TYPES:
        raise HTTPException(400, "Please use a JPG, PNG or WebP photo.")
    dst = PHOTO_DIR / f"family-{person_id}-{uuid.uuid4().hex[:8]}{ext}"
    with dst.open("wb") as f:
        shutil.copyfileobj(photo.file, f)
    gemma_ready = llm.ollama_status()["model_ready"]
    p = Photo(person_id=person_id, path=str(dst), status="describing" if gemma_ready else "failed",
              error="" if gemma_ready else "Gemma is not running. Start Ollama, then press Describe again.")
    s.add(p)
    s.commit()
    s.refresh(p)
    if gemma_ready:
        jobs.start("photo", p.id)
    return photo_out(p)


@app.get("/api/people/{person_id}/photos")
def list_family_photos(person_id: int, s: Session = Depends(get_session)):
    return [photo_out(p) for p in s.exec(select(Photo).where(Photo.person_id == person_id).order_by(Photo.created_at))]


@app.get("/api/photos/{photo_id}")
def get_family_photo(photo_id: int, s: Session = Depends(get_session)):
    return photo_out(s.get(Photo, photo_id) or _404())


@app.get("/api/photos/{photo_id}/image")
def get_family_photo_image(photo_id: int, s: Session = Depends(get_session)):
    return FileResponse((s.get(Photo, photo_id) or _404()).path)


class PhotoIn(BaseModel):
    caption: str
    description: str
    questions: list[dict[str, Any]]


@app.patch("/api/photos/{photo_id}")
def update_family_photo(photo_id: int, body: PhotoIn, s: Session = Depends(get_session)):
    p = s.get(Photo, photo_id) or _404()
    if p.status == "describing":
        raise HTTPException(409, "Gemma is still looking at this photo.")
    p.caption, p.description, p.questions = body.caption, body.description, body.questions
    s.add(p)
    s.commit()
    s.refresh(p)
    return photo_out(p)


@app.post("/api/photos/{photo_id}/describe")
def describe_family_photo(photo_id: int, s: Session = Depends(get_session)):
    p = s.get(Photo, photo_id) or _404()
    if not llm.ollama_status()["model_ready"]:
        raise HTTPException(409, "Gemma is not running. Start Ollama and pull the model first.")
    p.status, p.error = "describing", ""
    s.add(p)
    s.commit()
    s.refresh(p)
    jobs.start("photo", p.id)
    return photo_out(p)


@app.delete("/api/photos/{photo_id}")
def delete_family_photo(photo_id: int, s: Session = Depends(get_session)):
    p = s.get(Photo, photo_id) or _404()
    Path(p.path).unlink(missing_ok=True)
    s.delete(p)
    s.commit()
    return {"ok": True}


# ---------- recordings ----------


@app.post("/api/recordings")
def create_recording(
    audio: UploadFile = File(...),
    person_id: Optional[int] = Form(None),
    new_person_name: str = Form(""),
    new_person_relationship: str = Form(""),
    speaker_name: str = Form(...),
    language: str = Form("lug"),
    consent_given: bool = Form(...),
    consent_recorded_by: str = Form(...),
    s: Session = Depends(get_session),
):
    if not consent_given:
        raise HTTPException(400, "Consent is required before a story can be saved.")
    if not consent_recorded_by.strip():
        raise HTTPException(400, "Please say who recorded the consent.")
    if language not in LANGUAGES:
        raise HTTPException(400, f"Unknown language {language}.")
    if person_id is None:
        if not new_person_name.strip():
            raise HTTPException(400, "Choose an elder or add a new one.")
        person = Person(name=new_person_name.strip(), relationship=new_person_relationship.strip())
        s.add(person)
        s.commit()
        s.refresh(person)
        person_id = person.id
    elif not s.get(Person, person_id):
        _404()

    stem = f"rec-{uuid.uuid4().hex[:12]}"
    ext = Path(audio.filename or "").suffix.lower() or ".webm"
    original = AUDIO_DIR / f"{stem}{ext}"
    with original.open("wb") as f:
        shutil.copyfileobj(audio.file, f)
    wav = AUDIO_DIR / f"{stem}.wav"
    try:
        to_wav16k(original, wav)
        duration = duration_seconds(wav)
    except Exception:
        original.unlink(missing_ok=True)
        raise HTTPException(400, "Could not read this audio file. Try another format (MP3, M4A, WAV, WebM).")

    rec = Recording(
        person_id=person_id,
        speaker_name=speaker_name.strip(),
        language=language,
        consent_given=True,
        consent_text=CONSENT_TEXT.format(speaker=speaker_name.strip()),
        consent_recorded_by=consent_recorded_by.strip(),
        original_path=str(original),
        wav_path=str(wav),
        duration_s=round(duration, 1),
        status="queued" if asr.asr_status()["ready"] else "uploaded",
    )
    s.add(rec)
    s.commit()
    s.refresh(rec)
    if rec.status == "queued":
        jobs.start("transcribe", rec.id)
    return rec


@app.get("/api/recordings/{rec_id}")
def get_recording(rec_id: int, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    memory = s.exec(select(Memory).where(Memory.recording_id == rec_id).order_by(Memory.id.desc())).first()
    d = rec.model_dump()
    d["memory_id"] = memory.id if memory else None
    d["person"] = s.get(Person, rec.person_id).model_dump()
    return d


@app.get("/api/recordings/{rec_id}/audio")
def get_audio(rec_id: int, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    return FileResponse(rec.wav_path, media_type="audio/wav")


@app.post("/api/recordings/{rec_id}/transcribe")
def retry_transcription(rec_id: int, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    if not asr.asr_status()["ready"]:
        raise HTTPException(409, "The speech model is not installed yet. You can type the transcript instead.")
    rec.status, rec.progress, rec.error = "queued", 0.0, ""
    s.add(rec)
    s.commit()
    s.refresh(rec)
    jobs.start("transcribe", rec.id)
    return rec


class TranscriptIn(BaseModel):
    transcript: str


@app.patch("/api/recordings/{rec_id}/transcript")
def save_transcript(rec_id: int, body: TranscriptIn, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    rec.transcript = body.transcript
    rec.transcript_reviewed = True
    if rec.status in {"uploaded", "failed"}:
        rec.status = "transcribed"  # typed by hand
    s.add(rec)
    s.commit()
    s.refresh(rec)
    return rec


@app.delete("/api/recordings/{rec_id}")
def delete_recording(rec_id: int, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    for m in s.exec(select(Memory).where(Memory.recording_id == rec_id)):
        s.delete(m)
    for path in (rec.original_path, rec.wav_path):
        Path(path).unlink(missing_ok=True)
    s.delete(rec)
    s.commit()
    return {"ok": True}


# ---------- memories ----------


@app.post("/api/recordings/{rec_id}/structure")
def structure(rec_id: int, s: Session = Depends(get_session)):
    rec = s.get(Recording, rec_id) or _404()
    if not rec.transcript.strip():
        raise HTTPException(400, "The transcript is empty.")
    if not llm.ollama_status()["model_ready"]:
        raise HTTPException(409, "Gemma is not running. Start Ollama and pull the model first.")
    mem = Memory(recording_id=rec.id, person_id=rec.person_id, status="generating")
    s.add(mem)
    s.commit()
    s.refresh(mem)
    jobs.start("memory", mem.id)
    return mem


def memory_out(m: Memory, s: Session) -> dict:
    rec = s.get(Recording, m.recording_id)
    d = m.model_dump()
    d["transcript"] = rec.transcript
    d["speaker_name"] = rec.speaker_name
    d["language"] = rec.language
    d["duration_s"] = rec.duration_s
    d["recorded_at"] = rec.created_at
    d["consent_text"] = rec.consent_text
    d["consent_recorded_by"] = rec.consent_recorded_by
    d["person"] = s.get(Person, m.person_id).model_dump()
    return d


@app.get("/api/memories/{mem_id}")
def get_memory(mem_id: int, s: Session = Depends(get_session)):
    return memory_out(s.get(Memory, mem_id) or _404(), s)


class MemoryIn(BaseModel):
    title: str
    data: dict[str, Any]
    save: bool = False


@app.patch("/api/memories/{mem_id}")
def update_memory(mem_id: int, body: MemoryIn, s: Session = Depends(get_session)):
    m = s.get(Memory, mem_id) or _404()
    if m.status == "generating":
        raise HTTPException(409, "Gemma is still writing this memory.")
    m.title = body.title
    m.data = body.data
    if body.save:
        m.status = "saved"
    m.updated_at = now()
    s.add(m)
    s.commit()
    return memory_out(m, s)


@app.delete("/api/memories/{mem_id}")
def delete_memory(mem_id: int, s: Session = Depends(get_session)):
    m = s.get(Memory, mem_id) or _404()
    s.delete(m)
    s.commit()
    return {"ok": True}


class AnsweredIn(BaseModel):
    answered: bool


@app.patch("/api/memories/{mem_id}/questions/{index}")
def mark_question(mem_id: int, index: int, body: AnsweredIn, s: Session = Depends(get_session)):
    m = s.get(Memory, mem_id) or _404()
    data = dict(m.data)
    questions = [dict(q) for q in data.get("follow_up_questions", [])]
    if not 0 <= index < len(questions):
        _404()
    questions[index]["answered"] = body.answered
    data["follow_up_questions"] = questions
    m.data = data
    s.add(m)
    s.commit()
    return {"ok": True}


# ---------- remembrance page and memory book ----------

YEAR = re.compile(r"\b(1[89]\d\d|20\d\d)s?\b")


def remembrance(person: Person, s: Session) -> dict:
    memories = s.exec(
        select(Memory).where(Memory.person_id == person.id, Memory.status == "saved").order_by(Memory.created_at)
    ).all()
    people: dict[str, dict] = {}
    places: dict[str, dict] = {}
    timeline, questions = [], []
    for m in memories:
        d = m.data
        for p in d.get("people", []):
            entry = people.setdefault(normalize(p["name"]), {"name": p["name"], "relationships": set(), "stories": []})
            if p.get("relationship_to_speaker"):
                entry["relationships"].add(p["relationship_to_speaker"])
            entry["stories"].append({"memory_id": m.id, "title": m.title, "source_sentence": p["source_sentence"]})
        for p in d.get("places", []):
            entry = places.setdefault(normalize(p["name"]), {"name": p["name"], "stories": []})
            entry["stories"].append({"memory_id": m.id, "title": m.title, "source_sentence": p["source_sentence"]})
        for t in d.get("time_periods", []):
            match = YEAR.search(t["description"]) or YEAR.search(t["source_sentence"])
            timeline.append(
                {
                    "year": int(match.group(1)) if match else None,
                    "description": t["description"],
                    "source_sentence": t["source_sentence"],
                    "memory_id": m.id,
                    "title": m.title,
                }
            )
        for i, q in enumerate(d.get("follow_up_questions", [])):
            if not q.get("answered"):
                questions.append({**q, "memory_id": m.id, "index": i, "title": m.title})
    timeline.sort(key=lambda e: (e["year"] is None, e["year"] or 0))
    for e in people.values():
        e["relationships"] = sorted(e["relationships"])
    return {
        "person": person_out(person, s),
        "memories": [memory_out(m, s) for m in memories],
        "people": sorted(people.values(), key=lambda e: e["name"]),
        "places": sorted(places.values(), key=lambda e: e["name"]),
        "timeline": timeline,
        "open_questions": questions,
        "photos": [photo_out(p) for p in s.exec(select(Photo).where(Photo.person_id == person.id).order_by(Photo.created_at))],
    }


@app.get("/api/people/{person_id}/remembrance")
def get_remembrance(person_id: int, s: Session = Depends(get_session)):
    return remembrance(s.get(Person, person_id) or _404(), s)


@app.get("/api/people/{person_id}/drafts")
def get_drafts(person_id: int, s: Session = Depends(get_session)):
    """Recordings for this elder that are not yet saved memories, so work is never lost."""
    out = []
    for rec in s.exec(select(Recording).where(Recording.person_id == person_id).order_by(Recording.created_at.desc())):
        mem = s.exec(select(Memory).where(Memory.recording_id == rec.id).order_by(Memory.id.desc())).first()
        if mem and mem.status == "saved":
            continue
        out.append({"recording_id": rec.id, "status": rec.status, "created_at": rec.created_at,
                    "memory_id": mem.id if mem else None, "memory_status": mem.status if mem else None,
                    "preview": rec.transcript[:120]})
    return out


@app.get("/api/book")
def book(person_id: Optional[int] = None, s: Session = Depends(get_session)):
    if person_id is not None:
        people = [s.get(Person, person_id) or _404()]
    else:
        people = s.exec(select(Person).order_by(Person.name)).all()
    return [remembrance(p, s) for p in people]


def _404():
    raise HTTPException(404, "Not found")


# ---------- the web app ----------

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            _404()
        file = FRONTEND_DIST / path
        if path and file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
