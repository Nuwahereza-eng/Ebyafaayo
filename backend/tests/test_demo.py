"""The public demo: sample data is loaded, deleting is off. Runs in its own process, because
the demo setting is read when the app is imported."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

CHECK = """
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as c:
    assert c.get("/api/status").json()["demo"] is True
    people = c.get("/api/people").json()
    assert [p["name"] for p in people] == ["Nalongo Namubiru"]
    page = c.get(f"/api/people/{people[0]['id']}/remembrance").json()
    assert len(page["memories"]) == 1 and len(page["photos"]) == 2
    assert {p["name"] for p in page["people"]} >= {"Kizito", "Nakato", "Ssemakula"}
    assert c.get(page["photos"][0]["url"]).status_code == 200
    rec = page["memories"][0]["recording_id"]
    assert c.get(f"/api/recordings/{rec}/audio").status_code == 200
    assert c.delete(f"/api/recordings/{rec}").status_code == 403
    assert c.delete(f"/api/photos/{page['photos'][0]['id']}").status_code == 403
with TestClient(app) as c:  # a restart does not load the sample twice
    assert len(c.get("/api/people").json()) == 1
print("ok")
"""


def test_demo_mode_loads_sample_and_blocks_deleting():
    env = {**os.environ, "EBYAFAAYO_DEMO": "1", "EBYAFAAYO_TEMPORAL": "off",
           "EBYAFAAYO_DATA": tempfile.mkdtemp(prefix="ebyafaayo-demo-test-")}
    r = subprocess.run([sys.executable, "-c", CHECK], cwd=Path(__file__).parents[1], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip().endswith("ok"), r.stderr[-2000:]
