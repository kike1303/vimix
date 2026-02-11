import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
JOBS_DIR = BASE_DIR / "jobs"

UPLOADS_DIR.mkdir(exist_ok=True)
JOBS_DIR.mkdir(exist_ok=True)


def save_upload(job_id: str, filename: str, data: bytes) -> Path:
    """Save an uploaded file and return its path."""
    job_upload_dir = UPLOADS_DIR / job_id
    job_upload_dir.mkdir(exist_ok=True)
    dest = job_upload_dir / filename
    dest.write_bytes(data)
    return dest


def get_job_dir(job_id: str) -> Path:
    """Get (and create) the working directory for a job."""
    d = JOBS_DIR / job_id
    d.mkdir(exist_ok=True)
    return d


def cleanup_job(job_id: str) -> None:
    """Remove all temporary files for a job."""
    for d in (UPLOADS_DIR / job_id, JOBS_DIR / job_id):
        if d.exists():
            shutil.rmtree(d)
