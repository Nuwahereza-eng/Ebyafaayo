"""SQLite tables for elders, recordings (with consent) and memories."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine

from .config import DB_PATH


def now() -> datetime:
    return datetime.now(timezone.utc)


class Person(SQLModel, table=True):
    """An elder or ancestor whose stories the family keeps."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    relationship: str = ""  # e.g. "Jjajja (grandmother)"
    years: str = ""  # free text, e.g. "1938 – 2019"
    about: str = ""
    photo_path: Optional[str] = None
    created_at: datetime = Field(default_factory=now)


class Recording(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    speaker_name: str
    language: str = "lug"

    # Consent is stored with the recording, exactly as it was shown.
    consent_given: bool
    consent_text: str
    consent_recorded_by: str
    consent_at: datetime = Field(default_factory=now)

    original_path: str
    wav_path: str
    duration_s: float = 0.0

    # uploaded -> queued -> transcribing -> transcribed | failed
    status: str = "uploaded"
    progress: float = 0.0
    error: str = ""
    asr_model: str = ""
    transcript_raw: str = ""  # what the model heard
    transcript: str = ""  # what the family corrected
    transcript_reviewed: bool = False
    created_at: datetime = Field(default_factory=now)


class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recording_id: int = Field(foreign_key="recording.id", index=True)
    person_id: int = Field(foreign_key="person.id", index=True)

    # generating -> draft -> saved | failed
    status: str = "generating"
    progress_chars: int = 0
    error: str = ""
    model: str = ""
    generation_seconds: float = 0.0
    title: str = ""
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Photo(SQLModel, table=True):
    """An old family photo. Gemma describes what it can see; the family says who is in it."""

    id: Optional[int] = Field(default=None, primary_key=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    path: str
    caption: str = ""  # written by the family: who, where, when

    # describing -> ready | failed
    status: str = "describing"
    progress_chars: int = 0
    error: str = ""
    model: str = ""
    generation_seconds: float = 0.0
    description: str = ""  # Gemma's draft, editable
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    notes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now)


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
