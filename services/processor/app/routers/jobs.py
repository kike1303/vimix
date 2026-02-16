from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.processors.registry import get_processor
from app.services.job_manager import job_manager, JobStatus
from app.services.file_manager import save_upload, get_job_dir

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _validate_options(processor, options: dict) -> None:
    """Validate dimension-type options against min/max constraints."""
    for opt in processor.options_schema:
        if opt.get("type") != "dimension":
            continue
        opt_id = opt["id"]
        value = options.get(opt_id)
        if value is None:
            continue
        str_val = str(value)
        if str_val == "original" and opt.get("allow_original", False):
            continue
        try:
            num = int(str_val)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid dimension value for '{opt_id}': {value}",
            )
        opt_min = opt.get("min", 1)
        opt_max = opt.get("max", 99999)
        if num < opt_min or num > opt_max:
            raise HTTPException(
                status_code=400,
                detail=f"Dimension '{opt_id}' must be between {opt_min} and {opt_max}, got {num}",
            )


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

    _validate_options(processor, parsed_options)

    data = await file.read()
    job = job_manager.create(processor_id, file.filename or "upload")
    input_path = save_upload(job.id, file.filename or "upload", data)
    output_dir = get_job_dir(job.id)

    asyncio.create_task(_run_job(job.id, processor_id, input_path, output_dir, parsed_options))

    return job.to_dict()


@router.post("/batch")
async def create_batch(
    files: List[UploadFile],
    processor_id: str = Form(...),
    options: Optional[str] = Form(None),
):
    try:
        processor = get_processor(processor_id)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown processor: {processor_id}")

    parsed_options: dict = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid options JSON")

    _validate_options(processor, parsed_options)

    # Validate all file extensions upfront
    for f in files:
        ext = "." + (f.filename or "file").rsplit(".", 1)[-1].lower()
        if ext not in processor.accepted_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} not accepted for '{f.filename}'. Expected: {processor.accepted_extensions}",
            )

    # Multi-file processor: create ONE job with all files
    if processor.accepts_multiple_files:
        filenames = [f.filename or "upload" for f in files]
        combined_name = f"{len(files)}_files"
        job = job_manager.create(processor_id, combined_name)
        output_dir = get_job_dir(job.id)

        input_paths: list[Path] = []
        for f in files:
            data = await f.read()
            path = save_upload(job.id, f.filename or "upload", data)
            input_paths.append(path)

        asyncio.create_task(
            _run_job(job.id, processor_id, input_paths[0], output_dir, parsed_options, input_paths)
        )
        return {"type": "job", **job.to_dict()}

    # Standard processors: create N independent jobs
    job_ids: list[str] = []
    for f in files:
        data = await f.read()
        job = job_manager.create(processor_id, f.filename or "upload")
        input_path = save_upload(job.id, f.filename or "upload", data)
        output_dir = get_job_dir(job.id)
        asyncio.create_task(_run_job(job.id, processor_id, input_path, output_dir, parsed_options))
        job_ids.append(job.id)

    batch = job_manager.create_batch(processor_id, job_ids)
    return {"type": "batch", **batch.to_dict()}


@router.get("/batch/{batch_id}")
async def get_batch(batch_id: str):
    batch = job_manager.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    jobs = []
    for jid in batch.job_ids:
        job = job_manager.get(jid)
        if job:
            jobs.append(job.to_dict())

    return {**batch.to_dict(), "jobs": jobs}


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
    ".mp3": "audio/mpeg",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".json": "application/json",
    ".m4a": "audio/mp4",
    ".wma": "audio/x-ms-wma",
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


async def _run_job(
    job_id: str,
    processor_id: str,
    input_path,
    output_dir,
    options: dict | None = None,
    input_paths: list[Path] | None = None,
):
    job = job_manager.get(job_id)
    if job is None:
        return

    job.status = JobStatus.PROCESSING
    processor = get_processor(processor_id)

    async def on_progress(pct: float, msg: str):
        await job_manager.update_progress(job_id, pct, msg)

    try:
        result_path = await processor.process(
            input_path, output_dir, on_progress, options, input_paths
        )
        job_manager.mark_completed(job_id, result_path)
        await job_manager.update_progress(job_id, 100, "Done!")
        # Notify completion
        for q in job._listeners:
            await q.put({"status": "completed", "progress": 100, "message": "Done!"})
    except Exception as e:
        job_manager.mark_failed(job_id, str(e))
        for q in job._listeners:
            await q.put({"status": "failed", "progress": job.progress, "message": str(e)})
