from __future__ import annotations

import os
import sys

# Limit numba's internal parallelism to 1 thread to avoid contention with
# ONNX Runtime's own thread pool. Must be set before numba is imported
# (via rembg → pymatting → numba). The rembg processors also use a single-
# thread pool to prevent numba's workqueue "Concurrent access detected" crash.
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI

# When running as a PyInstaller bundle, point rembg to bundled models
if getattr(sys, "frozen", False):
    _bundle_dir = sys._MEIPASS  # type: ignore[attr-defined]
    _model_dir = os.path.join(_bundle_dir, ".u2net")
    if os.path.isdir(_model_dir):
        os.environ.setdefault("U2NET_HOME", _model_dir)
from fastapi.middleware.cors import CORSMiddleware

from app.routers import jobs, processors, oauth
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


_mcp_process: subprocess.Popen | None = None


def _start_mcp_server() -> None:
    """Start the MCP server as a subprocess (Streamable HTTP on port 8788).

    In development the MCP venv provides Python 3.12 + the mcp package.
    The subprocess is kept alive for the lifetime of the backend.
    Logs are written to services/mcp/mcp.log for debugging.
    """
    global _mcp_process
    mcp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mcp")
    mcp_server = os.path.join(mcp_dir, "server.py")
    mcp_python = os.path.join(mcp_dir, "venv", "bin", "python")

    if not os.path.isfile(mcp_python) or not os.path.isfile(mcp_server):
        logger.debug("MCP server not found, skipping auto-start")
        return

    try:
        log_path = os.path.join(mcp_dir, "mcp.log")
        log_file = open(log_path, "a")  # noqa: SIM115
        _mcp_process = subprocess.Popen(
            [mcp_python, mcp_server],
            cwd=mcp_dir,
            stdout=log_file,
            stderr=log_file,
        )
        logger.info("MCP server started (pid=%d, port=8788, log=%s)", _mcp_process.pid, log_path)
    except OSError:
        logger.debug("Failed to start MCP server subprocess")


def _stop_mcp_server() -> None:
    """Stop the MCP server subprocess if it's running."""
    global _mcp_process
    if _mcp_process is not None:
        _mcp_process.terminate()
        _mcp_process.wait(timeout=5)
        _mcp_process = None


def _register_mcp() -> None:
    """Register Vimix MCP server in all detected AI agent configurations."""
    try:
        mcp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mcp")
        if os.path.isfile(os.path.join(mcp_dir, "register.py")):
            sys.path.insert(0, mcp_dir)

        if getattr(sys, "frozen", False):
            bundle_dir = sys._MEIPASS  # type: ignore[attr-defined]
            mcp_bundle = os.path.join(bundle_dir, "mcp")
            if os.path.isfile(os.path.join(mcp_bundle, "register.py")):
                sys.path.insert(0, mcp_bundle)

        from register import ensure_registered

        results = ensure_registered()
        registered = [n for n, s in results.items() if s == "registered"]
        if registered:
            logger.info("Registered MCP in: %s", ", ".join(registered))
    except Exception:
        logger.debug("MCP registration skipped (module not available)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _register_mcp()
    _start_mcp_server()
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()
    _stop_mcp_server()


app = FastAPI(
    title="Vimix – Processor API",
    version="0.7.1",
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
app.include_router(oauth.router)


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
