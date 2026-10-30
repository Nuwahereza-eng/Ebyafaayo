"""Runs a memory job as a real Temporal workflow on a local test server, and kills a step half way."""

import shutil
import uuid
from pathlib import Path

import pytest

TEMPORAL_CLI = shutil.which("temporal") or str(Path.home() / ".local/temporal/temporal")
pytestmark = pytest.mark.skipif(not Path(TEMPORAL_CLI).exists(), reason="Temporal CLI not installed")


@pytest.mark.asyncio
async def test_failed_step_is_retried_without_redoing_finished_steps(monkeypatch):
    from temporalio.testing import WorkflowEnvironment

    from sqlmodel import Session
    from test_api import canned_gemma

    from app import db, durable, jobs
    from app.db import Memory, Person, Recording, init_db
    from app.workflows import WriteMemory

    init_db()
    with Session(db.engine) as s:
        person = Person(name="Durable Test")
        s.add(person)
        s.commit()
        rec = Recording(person_id=person.id, speaker_name="Durable Test", consent_given=True, consent_text="ok",
                        consent_recorded_by="Peter", original_path="x", wav_path="x", transcript="Taata wange yali Kizito.")
        s.add(rec)
        s.commit()
        mem = Memory(recording_id=rec.id, person_id=person.id)
        s.add(mem)
        s.commit()
        mem_id = mem.id

    canned_gemma(monkeypatch)
    calls = {"story": 0, "details": 0}
    real_story, real_details = jobs.gemma_write_story, jobs.gemma_find_details

    def story(*a, **k):
        calls["story"] += 1
        return real_story(*a, **k)

    def details(*a, **k):
        calls["details"] += 1
        if calls["details"] == 1:  # the first try dies, as if the laptop ran out of memory
            raise MemoryError("out of memory")
        return real_details(*a, **k)

    monkeypatch.setattr(jobs, "gemma_write_story", story)
    monkeypatch.setattr(jobs, "gemma_find_details", details)

    async with await WorkflowEnvironment.start_local(dev_server_existing_path=TEMPORAL_CLI) as env:
        async with durable.make_worker(env.client):
            result = await env.client.execute_workflow(
                WriteMemory.run, args=[mem_id, 1], id=f"test-{uuid.uuid4()}", task_queue=durable.TASK_QUEUE
            )

    assert result == "draft"
    assert calls == {"story": 1, "details": 2}  # Gemma's first answer was kept, not asked for again
    with Session(db.engine) as s:
        saved = s.get(Memory, mem_id)
        assert saved.status == "draft"
        assert saved.data["people"][0]["name"] == "Kizito"
