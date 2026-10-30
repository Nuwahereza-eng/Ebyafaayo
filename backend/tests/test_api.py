import subprocess

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def tone(tmp_path):
    path = tmp_path / "tone.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=2", str(path)], check=True)
    return path


def upload(client, tone, consent, name="Jjajja"):
    with tone.open("rb") as f:
        return client.post(
            "/api/recordings",
            data={"new_person_name": name, "speaker_name": name, "consent_given": str(consent).lower(),
                  "consent_recorded_by": "Peter"},
            files={"audio": ("a.mp3", f)},
        )


def test_recording_requires_consent(client, tone):
    r = upload(client, tone, False, name="Not Consented")
    assert r.status_code == 400
    assert "Not Consented" not in [p["name"] for p in client.get("/api/people").json()]


def test_recording_stores_consent_and_audio(client, tone):
    r = upload(client, tone, True)
    assert r.status_code == 200
    rec = r.json()
    assert rec["consent_given"] is True
    assert "stays on this computer" in rec["consent_text"]
    assert rec["duration_s"] == pytest.approx(2, abs=0.2)
    assert client.get(f"/api/recordings/{rec['id']}/audio").status_code == 200


def test_family_can_type_transcript(client, tone):
    rec = upload(client, tone, True).json()
    r = client.patch(f"/api/recordings/{rec['id']}/transcript", json={"transcript": "Nze Jjajja."})
    assert r.json()["transcript"] == "Nze Jjajja."
    assert r.json()["transcript_reviewed"] is True


def test_structuring_job_saves_gemma_result(client, tone, monkeypatch):
    """Runs the background job with Gemma replaced by a canned answer."""
    from app import jobs, llm
    from app.schemas import StructuredMemory

    rec = upload(client, tone, True, name="Job Test").json()
    client.patch(f"/api/recordings/{rec['id']}/transcript", json={"transcript": "Taata wange yali Kizito."})
    canned = StructuredMemory(title="T", luganda_text="Taata wange yali Kizito.", english_text="My father was Kizito.",
        people=[{"name": "Kizito", "relationship_to_speaker": "father", "source_sentence": "Taata wange yali Kizito.", "confidence": "clear"}])
    monkeypatch.setattr(llm, "ollama_status", lambda: {"model_ready": True})
    monkeypatch.setattr(llm, "structure_transcript", lambda *a, **k: (canned, {"model": "test", "retried": False, "seconds": 1}))
    monkeypatch.setattr(jobs, "submit", lambda fn, *args: fn(*args))
    mem = client.post(f"/api/recordings/{rec['id']}/structure").json()
    got = client.get(f"/api/memories/{mem['id']}").json()
    assert got["status"] == "draft", got["error"]
    assert got["model"] == "test"
    assert got["data"]["people"][0]["grounded"] is True
