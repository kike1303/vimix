"""Vimix MCP Server — exposes Vimix processing tools to LLM agents via MCP.

Runs as a Streamable HTTP server on port 8788 by default. Any MCP-compatible
agent (Claude Code, Cursor, Codex, etc.) can connect to http://localhost:8788/mcp.

All file processing happens 100% locally — files are read from disk, sent to the
local Vimix backend at localhost:8787, processed on your machine, and saved back
to disk. No data ever leaves your computer.

Usage:
    python server.py                  # Streamable HTTP on :8788 (default)
    python server.py stdio            # stdio transport (for subprocess-based agents)

Environment variables:
    VIMIX_API_URL   — backend URL (default: http://localhost:8787)
    VIMIX_MCP_PORT  — server port (default: 8788)
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("vimix.mcp")

VIMIX_API_URL = os.environ.get("VIMIX_API_URL", "http://localhost:8787")
VIMIX_MCP_PORT = int(os.environ.get("VIMIX_MCP_PORT", "8788"))
POLL_INTERVAL = 2  # seconds
POLL_TIMEOUT = 300  # 5 minutes
MAX_POLL_RETRIES = 5  # consecutive transient errors before giving up

mcp = FastMCP(
    "vimix",
    instructions=(
        "Vimix is a local media-processing toolkit that processes files 100% on your machine. "
        "No data ever leaves your computer. Use list_processors to discover available tools "
        "and their options, then process_file or batch_process to run them. "
        "The Vimix desktop app (or API backend) must be running."
    ),
    host="127.0.0.1",
    port=VIMIX_MCP_PORT,
)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=VIMIX_API_URL,
        timeout=httpx.Timeout(connect=10, read=120, write=120, pool=10),
    )


async def _health_check(client: httpx.AsyncClient) -> None:
    """Raise a clear error if the Vimix backend is not reachable."""
    try:
        resp = await client.get("/health")
        resp.raise_for_status()
    except (httpx.ConnectError, httpx.ConnectTimeout):
        raise RuntimeError(
            f"Cannot connect to Vimix backend at {VIMIX_API_URL}. "
            "Make sure it is running:\n"
            "  cd services/processor && source venv/bin/activate && uvicorn app.main:app --port 8787"
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Vimix backend health check failed: {exc.response.status_code}")


async def _poll_job(client: httpx.AsyncClient, job_id: str) -> dict:
    """Poll a job until it reaches a terminal state (completed/failed) or timeout.

    Retries on transient network errors to handle brief hiccups during
    long-running jobs (video processing can take minutes).
    """
    elapsed = 0
    consecutive_errors = 0
    last_status = "unknown"

    while elapsed < POLL_TIMEOUT:
        try:
            resp = await client.get(f"/jobs/{job_id}")
            resp.raise_for_status()
            job = resp.json()
            consecutive_errors = 0  # reset on success
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            consecutive_errors += 1
            logger.warning("Poll error for job %s (attempt %d): %s", job_id, consecutive_errors, exc)
            if consecutive_errors >= MAX_POLL_RETRIES:
                raise RuntimeError(
                    f"Lost connection to Vimix backend while polling job {job_id}. "
                    f"The job may still be running — check the Vimix app."
                )
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            continue

        last_status = job.get("status", "unknown")
        if last_status == "completed":
            return job
        if last_status == "failed":
            error = job.get("error") or job.get("message") or "Unknown processing error"
            raise RuntimeError(f"Processing failed: {error}")

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    raise RuntimeError(
        f"Processing timed out after {POLL_TIMEOUT}s (last status: {last_status}). "
        f"The job may still be running — check the Vimix app."
    )


async def _download_result(client: httpx.AsyncClient, job_id: str, output_path: Path) -> Path:
    """Download the result file for a completed job."""
    resp = await client.get(f"/jobs/{job_id}/result", timeout=120)
    resp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)
    return output_path


def _auto_output_path(input_path: Path, processor_id: str, result_ext: str) -> Path:
    """Generate an output path like photo_image-compress.webp next to the original."""
    ext = result_ext if result_ext.startswith(".") else f".{result_ext}"
    return input_path.parent / f"{input_path.stem}_{processor_id}{ext}"


def _format_size(size_bytes: int | float) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_processors() -> str:
    """List all available Vimix processors with their options.

    Returns each processor's id, label, description, accepted file extensions,
    and configurable options so you can choose the right processor and parameters.
    """
    try:
        async with _client() as client:
            await _health_check(client)
            resp = await client.get("/processors")
            resp.raise_for_status()
            processors = resp.json()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to list processors: {exc}") from exc

    lines: list[str] = []
    for p in processors:
        lines.append(f"## {p['label']}  (`{p['id']}`)")
        lines.append(f"{p['description']}")
        exts = ", ".join(p["accepted_extensions"])
        lines.append(f"Accepted extensions: {exts}")
        multi = p.get("accepts_multiple_files", False)
        if multi:
            lines.append("Accepts multiple files: yes")

        options = p.get("options_schema", [])
        if options:
            lines.append("Options:")
            for opt in options:
                opt_line = f"  - `{opt['id']}` ({opt['type']}): {opt.get('label', opt['id'])}"
                if "default" in opt:
                    opt_line += f" [default: {opt['default']}]"
                if "min" in opt:
                    opt_line += f" [min: {opt['min']}]"
                if "max" in opt:
                    opt_line += f" [max: {opt['max']}]"
                if "choices" in opt:
                    choices = ", ".join(f"{c['value']}" for c in opt["choices"])
                    opt_line += f" [choices: {choices}]"
                if "presets" in opt:
                    presets = ", ".join(str(v) for v in opt["presets"])
                    opt_line += f" [presets: {presets}]"
                lines.append(opt_line)
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def process_file(
    processor_id: str,
    file_path: str,
    options: dict | None = None,
    output_path: str | None = None,
) -> str:
    """Process a single file with a Vimix processor.

    Args:
        processor_id: Processor to use (e.g. "image-compress", "video-trim"). Use list_processors to see available IDs.
        file_path: Absolute path to the input file on disk.
        options: Processor-specific options as a dict (e.g. {"quality": 80, "format": "webp"}). See list_processors for available options.
        output_path: Where to save the result. If omitted, saves next to the original with a processor-id suffix.
    """
    input_file = Path(file_path).expanduser().resolve()
    if not input_file.is_file():
        raise RuntimeError(f"File not found: {input_file}")

    opts = options or {}
    mime_type = mimetypes.guess_type(str(input_file))[0] or "application/octet-stream"

    try:
        async with _client() as client:
            await _health_check(client)

            # Submit job
            files = {"file": (input_file.name, input_file.read_bytes(), mime_type)}
            data: dict[str, str] = {"processor_id": processor_id}
            if opts:
                data["options"] = json.dumps(opts)

            resp = await client.post("/jobs", files=files, data=data)
            if resp.status_code == 400:
                detail = resp.json().get("detail", resp.text)
                raise RuntimeError(f"Bad request: {detail}")
            resp.raise_for_status()
            job = resp.json()
            job_id = job["id"]

            # Poll until done
            completed_job = await _poll_job(client, job_id)

            # Determine output path
            result_ext = completed_job.get("result_extension", "")
            if output_path:
                out = Path(output_path).expanduser().resolve()
            else:
                if not result_ext:
                    result_ext = input_file.suffix
                out = _auto_output_path(input_file, processor_id, result_ext)

            # Download result
            await _download_result(client, job_id, out)

    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Processing failed: {exc}") from exc

    original_size = input_file.stat().st_size
    result_size = out.stat().st_size

    return (
        f"Done! Saved to: {out}\n"
        f"Original: {_format_size(original_size)}\n"
        f"Result:   {_format_size(result_size)}"
    )


@mcp.tool()
async def batch_process(
    processor_id: str,
    file_paths: list[str],
    options: dict | None = None,
    output_dir: str | None = None,
) -> str:
    """Process multiple files with a Vimix processor in one batch.

    For single-file processors (e.g. image-compress) each file is processed independently.
    For multi-file processors (e.g. pdf-merge) all files are combined in one operation.

    Args:
        processor_id: Processor to use. Use list_processors to see available IDs.
        file_paths: List of absolute paths to input files.
        options: Processor-specific options as a dict.
        output_dir: Directory to save results. If omitted, saves next to the first input file.
    """
    if not file_paths:
        raise RuntimeError("No file paths provided.")

    input_files = []
    for fp in file_paths:
        p = Path(fp).expanduser().resolve()
        if not p.is_file():
            raise RuntimeError(f"File not found: {p}")
        input_files.append(p)

    opts = options or {}
    out_dir = Path(output_dir).expanduser().resolve() if output_dir else input_files[0].parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with _client() as client:
            await _health_check(client)

            # Build multipart upload
            upload_files = []
            for f in input_files:
                mime = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
                upload_files.append(("files", (f.name, f.read_bytes(), mime)))

            data: dict[str, str] = {"processor_id": processor_id}
            if opts:
                data["options"] = json.dumps(opts)

            resp = await client.post("/jobs/batch", files=upload_files, data=data)
            if resp.status_code == 400:
                detail = resp.json().get("detail", resp.text)
                raise RuntimeError(f"Bad request: {detail}")
            resp.raise_for_status()
            batch = resp.json()

            results: list[str] = []

            if batch.get("type") == "job":
                # Multi-file processor — single combined job
                job_id = batch["id"]
                completed = await _poll_job(client, job_id)
                result_ext = completed.get("result_extension", "")
                out_name = f"batch_{processor_id}{result_ext if result_ext.startswith('.') else '.' + result_ext}"
                out_path = out_dir / out_name
                await _download_result(client, job_id, out_path)
                results.append(str(out_path))
            else:
                # Single-file processor — one job per file
                job_ids = batch.get("job_ids", [])

                # Poll all jobs concurrently
                completed_jobs = await asyncio.gather(
                    *[_poll_job(client, jid) for jid in job_ids],
                    return_exceptions=True,
                )

                for i, result in enumerate(completed_jobs):
                    if isinstance(result, Exception):
                        results.append(f"FAILED ({job_ids[i]}): {result}")
                        continue
                    result_ext = result.get("result_extension", "")
                    orig_name = result.get("original_filename", f"file_{i}")
                    stem = Path(orig_name).stem
                    ext = result_ext if result_ext.startswith(".") else f".{result_ext}"
                    out_path = out_dir / f"{stem}_{processor_id}{ext}"
                    await _download_result(client, job_ids[i], out_path)
                    results.append(str(out_path))

    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Batch processing failed: {exc}") from exc

    return f"Batch complete! {len(results)} file(s) processed:\n" + "\n".join(f"  - {r}" for r in results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    # Auto-register in all detected agents before starting
    from register import ensure_registered

    results = ensure_registered(port=VIMIX_MCP_PORT)
    for name, status in results.items():
        if status == "registered":
            print(f"  [+] Registered MCP in {name}")

    transport = sys.argv[1] if len(sys.argv) > 1 else "streamable-http"
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")
