"""Temporal workflows: the order of the steps in each job, and nothing else.

Temporal records every finished step. If the app is killed half way (on an 8 GB laptop the
out-of-memory killer is a real visitor), the workflow is replayed from that record when the app
starts again, and only the unfinished step runs again. The steps themselves are in durable.py;
this file imports nothing from the app because Temporal replays it in a sandbox.
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError


def _steps(retry_seconds: int, minutes: int, heartbeat_minutes: int | None = None) -> dict:
    return {
        "start_to_close_timeout": timedelta(minutes=minutes),
        # A working step checks in at least this often; if it goes quiet (the app died), Temporal
        # gives it to the next worker instead of waiting out the whole timeout.
        "heartbeat_timeout": timedelta(minutes=heartbeat_minutes) if heartbeat_minutes else None,
        # Waits 15 s, 30 s, 1 min, 2 min between tries: long enough for Ollama to restart after
        # the out-of-memory killer stops it, short enough that the family is not kept waiting.
        "retry_policy": RetryPolicy(initial_interval=timedelta(seconds=retry_seconds), backoff_coefficient=2, maximum_attempts=5),
    }


def _reason(e: ActivityError) -> str:
    cause = e.cause
    return getattr(cause, "message", None) or str(cause or e)


async def _fail(kind: str, id_: int, e: ActivityError, retry_seconds: int) -> str:
    await workflow.execute_activity("mark_failed", args=[kind, id_, _reason(e)], **_steps(retry_seconds, 1))
    return "failed"


@workflow.defn
class TranscribeStory:
    """Prepare the audio, transcribe it one 30-second piece at a time, then save the transcript."""

    @workflow.run
    async def run(self, recording_id: int, retry_seconds: int = 15) -> str:
        try:
            total = await workflow.execute_activity("prepare_transcription", recording_id, **_steps(retry_seconds, 5))
            texts: list[str] = []
            for i in range(total):
                texts.append(
                    await workflow.execute_activity(
                        "transcribe_piece", args=[recording_id, i, total], **_steps(retry_seconds, 30, heartbeat_minutes=1)
                    )
                )
            await workflow.execute_activity("finish_transcription", args=[recording_id, texts], **_steps(retry_seconds, 5))
            return "transcribed"
        except ActivityError as e:
            return await _fail("transcribe", recording_id, e, retry_seconds)


@workflow.defn
class WriteMemory:
    """Gemma writes the story, then finds the details; then we check both against the transcript."""

    @workflow.run
    async def run(self, memory_id: int, retry_seconds: int = 15) -> str:
        gemma = _steps(retry_seconds, 30, heartbeat_minutes=1)
        try:
            story = await workflow.execute_activity("gemma_write_story", memory_id, **gemma)
            details = await workflow.execute_activity("gemma_find_details", args=[memory_id, len(str(story["part"]))], **gemma)
            await workflow.execute_activity("check_and_save_memory", args=[memory_id, story, details], **_steps(retry_seconds, 5))
            return "draft"
        except ActivityError as e:
            return await _fail("memory", memory_id, e, retry_seconds)


@workflow.defn
class DescribePhoto:
    """Gemma looks at an old photo; any sentence that names someone is removed before saving."""

    @workflow.run
    async def run(self, photo_id: int, retry_seconds: int = 15) -> str:
        try:
            await workflow.execute_activity("gemma_describe_photo", photo_id, **_steps(retry_seconds, 30, heartbeat_minutes=1))
            return "ready"
        except ActivityError as e:
            return await _fail("photo", photo_id, e, retry_seconds)
