from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.processors.registry import get_processor
from app.services.job_manager import job_manager, JobStatus
from app.services.file_manager import save_upload, get_job_dir

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("")
async def create_job(
    file: UploadFile,
    processor_id: str = Form(...),
    options: Optional[str] = Form(None),
):
    try:
        processor = get_processor(processor_id)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown processor: {processor_id}")

    ext = "." + (file.filename or "file").rsplit(".", 1)[-1].lower()
    if ext not in processor.accepted_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not accepted. Expected: {processor.accepted_extensions}",
        )

    parsed_options: dict = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid options JSON")

    data = await file.read()
    job = job_manager.create(processor_id, file.filename or "upload")
    input_path = save_upload(job.id, file.filename or "upload", data)
    output_dir = get_job_dir(job.id)

    asyncio.create_task(_run_job(job.id, processor_id, input_path, output_dir, parsed_options))

    return job.to_dict()


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/{job_id}/progress")
async def job_progress_sse(job_id: str):
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = job_manager.subscribe(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        try:
            # Send current state immediately
            yield f"data: {json.dumps(job.to_dict())}\n\n"

            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                return

            while True:
                event = await asyncio.wait_for(queue.get(), timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("status") in (JobStatus.COMPLETED.value, JobStatus.FAILED.value):
                    break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'status': 'timeout'})}\n\n"
        finally:
            job_manager.unsubscribe(job_id, queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


_MEDIA_TYPES: dict[str, str] = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".zip": "application/zip",
}


@router.get("/{job_id}/result")
async def download_result(job_id: str):
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED or job.result_path is None:
        raise HTTPException(status_code=400, detail="Result not ready")

    result = Path(job.result_path)
    ext = result.suffix.lower()
    media_type = _MEDIA_TYPES.get(ext, "application/octet-stream")
    stem = job.original_filename.rsplit(".", 1)[0] if "." in job.original_filename else job.original_filename
    return FileResponse(
        job.result_path,
        filename=f"{stem}{ext}",
        media_type=media_type,
    )


async def _run_job(job_id: str, processor_id: str, input_path, output_dir, options: dict | None = None):
    job = job_manager.get(job_id)
    if job is None:
        return

    job.status = JobStatus.PROCESSING
    processor = get_processor(processor_id)

    async def on_progress(pct: float, msg: str):
        await job_manager.update_progress(job_id, pct, msg)

    try:
        result_path = await processor.process(input_path, output_dir, on_progress, options)
        job_manager.mark_completed(job_id, result_path)
        await job_manager.update_progress(job_id, 100, "Done!")
        # Notify completion
        for q in job._listeners:
            await q.put({"status": "completed", "progress": 100, "message": "Done!"})
    except Exception as e:
        job_manager.mark_failed(job_id, str(e))
        for q in job._listeners:
            await q.put({"status": "failed", "progress": job.progress, "message": str(e)})
