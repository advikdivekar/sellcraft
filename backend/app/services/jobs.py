"""Job orchestration. Each stage updates real state in SQLite; the frontend polls it.
Runs inside FastAPI BackgroundTasks (threadpool): fine for a single-process prototype,
but jobs die with the process. Stage functions are independent so they can move to a worker later."""
import logging

from .. import db, tracing
from ..errors import AppError
from ..schemas import JobError, JobStatus, StageEntry
from .copy import CopyService

log = logging.getLogger("sellcraft.jobs")


def _set_stage(job_id: str, stages: list[StageEntry], name: str, status: str, detail: str | None = None) -> None:
    now = db.now()
    for s in stages:
        if s.name == name:
            s.status = status
            s.detail = detail
            s.finished_at = now if status != "running" else None
            break
    else:
        stages.append(StageEntry(name=name, status=status, detail=detail, started_at=now,
                                 finished_at=now if status != "running" else None))
    db.update_job(job_id, stages=stages)


def run_generation(job_id: str, copy_service: CopyService | None = None) -> None:
    job = db.get_job(job_id)
    if job is None:
        return
    stages: list[StageEntry] = []
    try:
        with tracing.span("job", "generation", job_id=job_id, platforms=len(job.settings.platforms)):
            # --- stage 1: copy ---
            db.update_job(job_id, status=JobStatus.generating_copy)
            _set_stage(job_id, stages, "copy", "running")
            svc = copy_service or CopyService()
            with tracing.span("llm", "copy.generate", model=getattr(svc.llm, "model", "demo")) as sp:
                result = svc.generate(job.product, job.settings)
                if sp is not None:
                    for k, v in result.usage.items():
                        sp.set_data(k, v)
            db.update_job(job_id, copy_output=result.copy, copy_source=result.source)
            _set_stage(job_id, stages, "copy", "done", result.source)

            # --- later phases plug in here: video, voiceover, assembly ---
            _set_stage(job_id, stages, "video", "skipped", "Video generation not enabled yet")

        db.update_job(job_id, status=JobStatus.completed)
    except AppError as e:
        _fail(job_id, stages, e.code, e.message, e.retryable)
    except Exception:  # noqa: BLE001 - never leak internals to the client
        log.exception("unexpected failure in job %s", job_id)
        _fail(job_id, stages, "internal_error", "Something went wrong on our side. Please retry.", True)


def _fail(job_id, stages, code, message, retryable):
    running = next((s for s in stages if s.status == "running"), None)
    if running:
        _set_stage(job_id, stages, running.name, "failed", code)
    db.update_job(job_id, status=JobStatus.failed, error=JobError(code=code, message=message, retryable=retryable))
