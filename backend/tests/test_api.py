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
