"""Job orchestration. Each stage updates real state in SQLite; the frontend polls it.
Runs inside FastAPI BackgroundTasks (threadpool): fine for a single-process prototype,
but jobs die with the process. Stage functions are independent so they can move to a worker later."""
import logging

from .. import db, tracing
from ..errors import AppError
from ..schemas import JobError, JobStatus, StageEntry
from .copy import CopyService
from .video import ffmpeg, service as video

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


def _stage_copy(job_id, stages, copy_service):
    job = db.get_job(job_id)
    if job.copy_output is not None:  # retry after a later-stage failure: keep the copy (and the seller's edits)
        _set_stage(job_id, stages, "copy", "done", job.copy_source)
        return
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


def _stage_video(job_id, stages):
    job = db.get_job(job_id)
    db.update_job(job_id, status=JobStatus.generating_video)
    _set_stage(job_id, stages, "video", "running")
    video.clear_outputs(job_id, kinds=("clip", "video"))
    with tracing.span("video", "video.clip", style=job.settings.visual_style.value):
        clip, method = video.render_clip(job)
    db.add_asset(kind="clip", mime="video/mp4", path=clip, method=method, job_id=job_id)
    _set_stage(job_id, stages, "video", "done", method)
    return clip, method


def _stage_assembly(job_id, stages, clip, method):
    job = db.get_job(job_id)
    db.update_job(job_id, status=JobStatus.assembling_video)
    _set_stage(job_id, stages, "assembly", "running")
    with tracing.span("video", "video.assemble"):
        out, probe = video.render_final(job, clip)
    db.add_asset(kind="video", mime="video/mp4", path=out, method=method, duration_seconds=probe.duration, job_id=job_id)
    _set_stage(job_id, stages, "assembly", "done", f"{probe.duration:.1f}s")


def run_generation(job_id: str, copy_service: CopyService | None = None) -> None:
    job = db.get_job(job_id)
    if job is None:
        return
    stages: list[StageEntry] = []
    try:
        with tracing.span("job", "generation", job_id=job_id, platforms=len(job.settings.platforms)):
            _stage_copy(job_id, stages, copy_service)
            clip, method = _stage_video(job_id, stages)
            if job.settings.voiceover:
                _set_stage(job_id, stages, "voiceover", "skipped", "Voiceover isn't enabled yet")
            _stage_assembly(job_id, stages, clip, method)
        db.update_job(job_id, status=JobStatus.completed)
    except AppError as e:
        _fail(job_id, stages, e.code, e.message, e.retryable)
    except Exception:  # noqa: BLE001 - never leak internals to the client
        log.exception("unexpected failure in job %s", job_id)
        _fail(job_id, stages, "internal_error", "Something went wrong on our side. Please retry.", True)


def run_reassembly(job_id: str) -> None:
    """Re-render only the text overlays after the seller edits the copy. Reuses the existing motion clip."""
    job = db.get_job(job_id)
    if job is None:
        return
    stages = [s for s in job.stages if s.name != "assembly"]
    try:
        rows = db.list_asset_rows(job_id, ("clip",))
        if not rows:
            raise AppError("clip_missing", "The base video is missing. Use Try again to rebuild it.", retryable=True, status=409)
        from pathlib import Path
        old = db.list_asset_rows(job_id, ("video",))
        _stage_assembly(job_id, stages, Path(rows[0]["path"]), rows[0]["method"])
        for r in old:  # keep the previous video until the new one is verified
            Path(r["path"]).unlink(missing_ok=True)
            db.delete_asset(r["id"])
        db.update_job(job_id, status=JobStatus.completed, error=None)
    except AppError as e:
        _fail(job_id, stages, e.code, e.message, e.retryable, keep_copy_ok=True)
    except Exception:  # noqa: BLE001
        log.exception("unexpected failure re-assembling job %s", job_id)
        _fail(job_id, stages, "internal_error", "Something went wrong on our side. Please retry.", True, keep_copy_ok=True)


def _fail(job_id, stages, code, message, retryable, keep_copy_ok=False):
    running = next((s for s in stages if s.status == "running"), None)
    if running:
        _set_stage(job_id, stages, running.name, "failed", code)
    db.update_job(job_id, status=JobStatus.failed, error=JobError(code=code, message=message, retryable=retryable))
