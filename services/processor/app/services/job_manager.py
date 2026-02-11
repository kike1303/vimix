from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    processor_id: str
    original_filename: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0
    message: str = ""
    result_path: str | None = None
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    _listeners: list[asyncio.Queue] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        result_ext = ""
        if self.result_path:
            result_ext = Path(self.result_path).suffix.lower()
        return {
            "id": self.id,
            "processor_id": self.processor_id,
            "original_filename": self.original_filename,
            "status": self.status.value,
            "progress": round(self.progress, 1),
            "message": self.message,
            "result_extension": result_ext,
            "error": self.error,
            "created_at": self.created_at,
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, processor_id: str, original_filename: str) -> Job:
        job = Job(
            id=uuid.uuid4().hex[:12],
            processor_id=processor_id,
            original_filename=original_filename,
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def update_progress(self, job_id: str, progress: float, message: str) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.progress = progress
        job.message = message
        event = {"progress": round(progress, 1), "message": message, "status": job.status.value}
        for q in job._listeners:
            await q.put(event)

    def mark_completed(self, job_id: str, result_path: Path) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.message = "Done!"
        job.result_path = str(result_path)

    def mark_failed(self, job_id: str, error: str) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.FAILED
        job.error = error
        job.message = f"Error: {error}"

    def subscribe(self, job_id: str) -> asyncio.Queue | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        q: asyncio.Queue = asyncio.Queue()
        job._listeners.append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        job = self._jobs.get(job_id)
        if job and q in job._listeners:
            job._listeners.remove(q)


job_manager = JobManager()
