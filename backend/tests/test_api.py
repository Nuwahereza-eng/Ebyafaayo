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


def canned_gemma(monkeypatch):
    """Replace Gemma with fixed answers, and run jobs straight away instead of in the background."""
    from app import jobs, llm
    from app.schemas import ExtractPart, PhotoPart, TextPart

    text = TextPart(title="T", luganda_text="Taata wange yali Kizito.", english_text="My father was Kizito.")
    extract = ExtractPart(people=[{"name": "Kizito", "relationship_to_speaker": "father",
                                   "source_sentence": "Taata wange yali Kizito.", "confidence": "clear"}])
    photo = PhotoPart(description="A black-and-white photo of two men in suits. The man on the left is Kizito, the father.",
                      questions=[{"luganda": "Jjajja, ani ono?", "english": "Grandparent, who is this?"}])
    monkeypatch.setattr(llm, "ollama_status", lambda: {"model_ready": True})
    monkeypatch.setattr(llm, "write_story", lambda *a, **k: (text, False))
    monkeypatch.setattr(llm, "find_details", lambda *a, **k: (extract, False))
    monkeypatch.setattr(llm, "describe_photo", lambda *a, **k: (photo, {"model": "test", "retried": False, "seconds": 1}))
    monkeypatch.setattr(jobs, "start", lambda kind, id_: jobs._run_in_thread(kind, id_))


def test_structuring_job_saves_gemma_result(client, tone, monkeypatch):
    canned_gemma(monkeypatch)
    rec = upload(client, tone, True, name="Job Test").json()
    client.patch(f"/api/recordings/{rec['id']}/transcript", json={"transcript": "Taata wange yali Kizito."})
    mem = client.post(f"/api/recordings/{rec['id']}/structure").json()
    got = client.get(f"/api/memories/{mem['id']}").json()
    assert got["status"] == "draft", got["error"]
    from app.config import GEMMA_MODEL

    assert got["model"] == GEMMA_MODEL
    assert got["data"]["people"][0]["grounded"] is True


def test_photo_description_never_names_anyone(client, tone, monkeypatch):
    """Gemma said who was in the photo; that sentence must not reach the family book."""
    canned_gemma(monkeypatch)
    rec = upload(client, tone, True, name="Photo Test").json()
    client.patch(f"/api/recordings/{rec['id']}/transcript", json={"transcript": "Taata wange yali Kizito."})
    mem = client.post(f"/api/recordings/{rec['id']}/structure").json()
    client.patch(f"/api/memories/{mem['id']}", json={"title": "T", "data": client.get(f"/api/memories/{mem['id']}").json()["data"], "save": True})

    with tone.open("rb") as f:  # any bytes will do: Gemma is canned
        photo = client.post(f"/api/people/{rec['person_id']}/photos", files={"photo": ("old.jpg", f)}).json()
    got = client.get(f"/api/photos/{photo['id']}").json()
    assert got["status"] == "ready", got["error"]
    assert got["description"] == "A black-and-white photo of two men in suits."
    assert "Kizito" not in got["description"] and got["notes"]
    assert got["questions"][0]["english"] == "Grandparent, who is this?"

    page = client.get(f"/api/people/{rec['person_id']}/remembrance").json()
    assert page["photos"][0]["id"] == photo["id"]
    r = client.patch(f"/api/photos/{photo['id']}", json={"caption": "Taata Kizito, 1960s", "description": got["description"], "questions": []})
    assert r.json()["caption"] == "Taata Kizito, 1960s"
