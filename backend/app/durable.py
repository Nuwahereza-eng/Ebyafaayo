"""Durable jobs with a local Temporal server (open source, runs on this laptop).

Start the server once with `make temporal`. The app connects to it at start-up and runs a worker
in the same process. If no server is running, jobs fall back to a plain background thread
(see jobs.py), so the app still works; it just cannot resume a job after a crash.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from sqlmodel import Session, select
from temporalio import activity
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError
from temporalio.worker import Worker

from . import asr, jobs
from .db import Memory, Photo, Recording, engine
from .workflows import DescribePhoto, TranscribeStory, WriteMemory

ADDRESS = os.environ.get("EBYAFAAYO_TEMPORAL", "127.0.0.1:7233")  # "off" to use threads only
TASK_QUEUE = "ebyafaayo"
WORKFLOWS = {"transcribe": TranscribeStory, "memory": WriteMemory, "photo": DescribePhoto}
INTERRUPTED = "Interrupted (the app was restarted). Please try again."


def workflow_id(kind: str, id_: int) -> str:
    return f"ebyafaayo-{kind}-{id_}"


# ---------- activities: thin wrappers that let each step tell Temporal it is still alive ----------


def _beat() -> None:
    activity.heartbeat()


@activity.defn(name="prepare_transcription")
def prepare_transcription(recording_id: int) -> int:
    return jobs.prepare_transcription(recording_id)


@activity.defn(name="transcribe_piece")
def transcribe_piece(recording_id: int, index: int, total: int) -> str:
    return jobs.transcribe_piece(recording_id, index, total, beat=_beat)


@activity.defn(name="finish_transcription")
def finish_transcription(recording_id: int, texts: list[str]) -> None:
    jobs.finish_transcription(recording_id, texts)


@activity.defn(name="gemma_write_story")
def gemma_write_story(memory_id: int) -> dict:
    return jobs.gemma_write_story(memory_id, beat=_beat)


@activity.defn(name="gemma_find_details")
def gemma_find_details(memory_id: int, done_chars: int) -> dict:
    return jobs.gemma_find_details(memory_id, done_chars, beat=_beat)


@activity.defn(name="check_and_save_memory")
def check_and_save_memory(memory_id: int, story: dict, details: dict) -> None:
    jobs.check_and_save_memory(memory_id, story, details)


@activity.defn(name="gemma_describe_photo")
def gemma_describe_photo(photo_id: int) -> None:
    jobs.gemma_describe_photo(photo_id, beat=_beat)


@activity.defn(name="mark_failed")
def mark_failed(kind: str, id_: int, error: str) -> None:
    if kind == "transcribe":
        asr.release()
    jobs.mark_failed(kind, id_, error)


ACTIVITIES = [prepare_transcription, transcribe_piece, finish_transcription, gemma_write_story, gemma_find_details,
              check_and_save_memory, gemma_describe_photo, mark_failed]


def make_worker(client: Client) -> Worker:
    return Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=list(WORKFLOWS.values()),
        activities=ACTIVITIES,
        activity_executor=ThreadPoolExecutor(max_workers=1),
        max_concurrent_activities=1,  # one heavy model in RAM at a time
    )


# ---------- the connection, owned by the app ----------


class Runner:
    def __init__(self) -> None:
        self.client: Optional[Client] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.worker: Optional[Worker] = None
        self.task: Optional[asyncio.Task] = None
        self.error = ""

    @property
    def ready(self) -> bool:
        return self.client is not None and self.task is not None and not self.task.done()

    def status(self) -> dict:
        return {"engine": "temporal" if self.ready else "thread", "address": ADDRESS, "error": self.error}

    async def connect(self) -> None:
        if ADDRESS == "off":
            self.error = "Turned off (EBYAFAAYO_TEMPORAL=off)."
            return
        try:
            self.client = await asyncio.wait_for(Client.connect(ADDRESS), timeout=5)
        except Exception as e:  # no server: fall back to threads
            self.client, self.error = None, f"No Temporal server at {ADDRESS} ({type(e).__name__}). Jobs run in a thread."
            return
        self.loop = asyncio.get_running_loop()
        self.worker = make_worker(self.client)
        self.task = asyncio.create_task(self.worker.run())
        self.error = ""

    async def stop(self) -> None:
        if self.worker and self.task and not self.task.done():
            await self.worker.shutdown()

    def start(self, kind: str, id_: int, retry_seconds: int = 15) -> None:
        """Called from FastAPI's worker threads; the client lives on the main event loop."""
        coro = self.client.start_workflow(
            WORKFLOWS[kind].run, args=[id_, retry_seconds], id=workflow_id(kind, id_), task_queue=TASK_QUEUE
        )
        try:
            asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=15)
        except WorkflowAlreadyStartedError:
            pass  # the same job is already running; it will update the page itself

    async def is_running(self, kind: str, id_: int) -> bool:
        try:
            desc = await self.client.get_workflow_handle(workflow_id(kind, id_)).describe()
        except RPCError:  # never started
            return False
        return desc.status == WorkflowExecutionStatus.RUNNING


runner = Runner()


async def recover() -> list[str]:
    """At start-up: jobs Temporal is still running carry on; any other unfinished job is marked failed."""
    unfinished = []
    with Session(engine) as s:
        unfinished += [("transcribe", r.id) for r in s.exec(select(Recording).where(Recording.status.in_(["queued", "transcribing"])))]
        unfinished += [("memory", m.id) for m in s.exec(select(Memory).where(Memory.status == "generating"))]
        unfinished += [("photo", p.id) for p in s.exec(select(Photo).where(Photo.status == "describing"))]
    resumed = []
    for kind, id_ in unfinished:
        if runner.ready and await runner.is_running(kind, id_):
            resumed.append(workflow_id(kind, id_))
        else:
            jobs.mark_failed(kind, id_, INTERRUPTED)
    return resumed
