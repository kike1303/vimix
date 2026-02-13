from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

# When running as a PyInstaller bundle, point rembg to bundled models
if getattr(sys, "frozen", False):
    _bundle_dir = sys._MEIPASS  # type: ignore[attr-defined]
    _model_dir = os.path.join(_bundle_dir, ".u2net")
    if os.path.isdir(_model_dir):
        os.environ.setdefault("U2NET_HOME", _model_dir)
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jobs, processors
from app.services.job_manager import job_manager
from app.services.file_manager import cleanup_job

logger = logging.getLogger("vimix")

CLEANUP_INTERVAL = 600  # check every 10 minutes
CLEANUP_MAX_AGE = 3600  # remove jobs older than 1 hour


async def _cleanup_loop() -> None:
    """Periodically remove expired jobs and their files."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        try:
            expired = job_manager.collect_expired(CLEANUP_MAX_AGE)
            for job_id in expired:
                cleanup_job(job_id)
                job_manager.remove_job(job_id)
            if expired:
                logger.info("Cleaned up %d expired job(s)", len(expired))
        except Exception:
            logger.exception("Error during cleanup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


app = FastAPI(
    title="Vimix – Processor API",
    version="0.2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(processors.router)
app.include_router(jobs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.delete("/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of expired jobs (older than 1 hour)."""
    expired = job_manager.collect_expired(CLEANUP_MAX_AGE)
    for job_id in expired:
        cleanup_job(job_id)
        job_manager.remove_job(job_id)
    return {"removed": len(expired)}


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Vimix Processor API")
    parser.add_argument("--port", type=int, default=8787, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
