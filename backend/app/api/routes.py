from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .. import db
from ..config import get_settings
from ..errors import AppError
from ..schemas import (CopyOutput, CreateGenerationRequest, GenerationJob, JobStatus,
                       RegenerateCopyRequest)
from ..services import jobs, storage
from ..services.copy import CopyService
from ..services.llm.ollama import OllamaProvider
from ..services.video import ffmpeg

router = APIRouter(prefix="/api")


def _job_or_404(job_id: str) -> GenerationJob:
    job = db.get_job(job_id)
    if job is None:
        raise AppError("job_not_found", "Generation not found.", status=404)
    return job


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/providers/status")
def providers_status():
    s = get_settings()
    llm = {"mode": "demo", "reachable": True, "model": "demo", "model_available": True} if s.demo_mode else \
        {"mode": "ollama", **OllamaProvider().health()}
    return {
        "llm": llm,
        "ffmpeg": {"available": ffmpeg.available()},
        "video": {"provider": s.video_provider, "method": "animated_photo" if s.video_provider == "fallback" else s.video_provider},
        "voiceover": {"configured": bool(s.elevenlabs_api_key)},
        "demo_mode": s.demo_mode,
    }


@router.post("/uploads", status_code=201)
def upload(file: UploadFile = File(...)):
    return storage.save_upload(file)


@router.post("/generations", status_code=202)
def create_generation(req: CreateGenerationRequest, bg: BackgroundTasks):
    row = db.get_asset_row(req.product.image_asset_id)
    if row is None or row["kind"] != "image" or row["job_id"] is not None:
        raise AppError("bad_image", "Upload a product photo first.", status=422)
    job_id = db.create_job(req.product, req.settings)
    db.attach_asset(req.product.image_asset_id, job_id)
    bg.add_task(jobs.run_generation, job_id)
    return _job_or_404(job_id)


@router.get("/generations/{job_id}")
def get_generation(job_id: str):
    return _job_or_404(job_id)


@router.patch("/generations/{job_id}/copy")
def save_copy(job_id: str, copy: CopyOutput):
    job = _job_or_404(job_id)
    if job.copy_output is None:
        raise AppError("no_copy", "This job has no copy to edit yet.", status=409)
    db.update_job(job_id, copy_output=copy)
    return _job_or_404(job_id)


@router.post("/generations/{job_id}/regenerate-copy")
def regenerate_copy(job_id: str, req: RegenerateCopyRequest):
    job = _job_or_404(job_id)
    if job.copy_output is None or job.status in (JobStatus.queued, JobStatus.generating_copy):
        raise AppError("not_ready", "Copy isn't ready yet.", status=409)
    result = CopyService().regenerate(job.copy_output, job.product, job.settings,
                                      section=req.section, tone=req.tone, instructions=req.instructions)
    fields = {"copy_output": result.copy, "copy_source": result.source}
    db.update_job(job_id, **fields)
    if req.tone and req.tone != job.settings.tone:
        db.update_job(job_id, settings=job.settings.model_copy(update={"tone": req.tone}))
    return _job_or_404(job_id)


@router.post("/generations/{job_id}/reassemble", status_code=202)
def reassemble(job_id: str, bg: BackgroundTasks):
    job = _job_or_404(job_id)
    if job.copy_output is None or job.status in (JobStatus.queued, JobStatus.generating_copy,
                                                  JobStatus.generating_video, JobStatus.assembling_video):
        raise AppError("not_ready", "The video isn't ready to update yet.", status=409)
    db.update_job(job_id, status=JobStatus.assembling_video, error=None)
    bg.add_task(jobs.run_reassembly, job_id)
    return _job_or_404(job_id)


@router.post("/generations/{job_id}/retry", status_code=202)
def retry_generation(job_id: str, bg: BackgroundTasks):
    job = _job_or_404(job_id)
    if job.status != JobStatus.failed:
        raise AppError("not_failed", "Only failed generations can be retried.", status=409)
    db.update_job(job_id, status=JobStatus.queued, error=None, stages=[])
    bg.add_task(jobs.run_generation, job_id)
    return _job_or_404(job_id)


@router.get("/generations/{job_id}/assets/{asset_id}")
def get_asset(job_id: str, asset_id: str):
    row = db.get_asset_row(asset_id)
    if row is None or row["job_id"] != job_id:
        raise AppError("asset_not_found", "Asset not found.", status=404)
    return FileResponse(storage.asset_file(row), media_type=row["mime"])
