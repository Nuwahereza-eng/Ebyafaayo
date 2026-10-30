"""The public demo (EBYAFAAYO_DEMO=1): a sample story and two test photos, loaded on first start.

None of this is a real family's history. The story was written to test the app, and the photos
are public-domain archive photos (samples/photos/SOURCES.md).
"""

import json
import shutil
import subprocess

from sqlmodel import Session, select

from .config import AUDIO_DIR, PHOTO_DIR, ROOT
from .db import Memory, Person, Photo, Recording, engine

SAMPLES = ROOT / "backend" / "samples"

# Limits so one visitor cannot keep the shared Gemma busy for everyone.
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_TRANSCRIPT_CHARS = 3000
MAX_JOBS_WAITING = 3


def seed() -> None:
    with Session(engine) as s:
        if s.exec(select(Person)).first():
            return
        data = json.loads((SAMPLES / "demo_seed.json").read_text(encoding="utf-8"))
        person = Person(**data["person"])
        s.add(person)
        s.commit()
        s.refresh(person)

        # The sample story was typed, not recorded: a few seconds of silence stand in for the audio.
        wav = AUDIO_DIR / "demo-sample-silence.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "3",
                        "-c:a", "pcm_s16le", str(wav)], check=True, capture_output=True)
        transcript = (SAMPLES / data["transcript_file"]).read_text(encoding="utf-8").strip()
        rec = Recording(
            person_id=person.id, speaker_name=person.name, language="lug", consent_given=True,
            consent_text="Demo: a sample story written for testing. No one was recorded.",
            consent_recorded_by="Demo", original_path=str(wav), wav_path=str(wav), duration_s=3.0,
            status="transcribed", transcript_raw=transcript, transcript=transcript, transcript_reviewed=True,
        )
        s.add(rec)
        s.commit()
        s.refresh(rec)

        m = data["memory"]
        s.add(Memory(recording_id=rec.id, person_id=person.id, status="saved", model="gemma4:e2b",
                     generation_seconds=m["generation_seconds"], title=m["title"], data=m["data"]))
        for p in data["photos"]:
            dst = PHOTO_DIR / f"demo-{(SAMPLES / p['file']).name}"
            shutil.copy(SAMPLES / p["file"], dst)
            s.add(Photo(person_id=person.id, path=str(dst), caption=p["caption"], status="ready", model="gemma4:e2b",
                        generation_seconds=p["generation_seconds"], description=p["description"], questions=p["questions"]))
        s.commit()


def jobs_waiting() -> int:
    with Session(engine) as s:
        return (
            len(s.exec(select(Recording).where(Recording.status.in_(["queued", "transcribing"]))).all())
            + len(s.exec(select(Memory).where(Memory.status == "generating")).all())
            + len(s.exec(select(Photo).where(Photo.status == "describing")).all())
        )
