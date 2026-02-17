from __future__ import annotations

import asyncio
import logging
import socket
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

import uvicorn

logger = logging.getLogger("vimix.oauth")

router = APIRouter(prefix="/oauth", tags=["oauth"])

CALLBACK_PORT = 1455
TIMEOUT_SECONDS = 300  # 5 minutes

# In-memory storage for pending OAuth flows
_pending: Dict[str, str | None] = {}  # state -> code (None = waiting)
_server_task: asyncio.Task | None = None
_shutdown_event: asyncio.Event | None = None


SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Vimix – Sign in successful</title>
  <style>
    body { font-family: system-ui, sans-serif; display: flex; align-items: center;
           justify-content: center; min-height: 100vh; margin: 0; background: #0a0a0a; color: #fafafa; }
    .card { text-align: center; padding: 2rem; }
    .check { font-size: 3rem; margin-bottom: 1rem; }
    h1 { font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }
    p { color: #a1a1aa; font-size: 0.875rem; margin: 0; }
  </style>
</head>
<body>
  <div class="card">
    <div class="check">&#10003;</div>
    <h1>Sign in successful</h1>
    <p>You can close this tab and return to Vimix.</p>
  </div>
  <script>setTimeout(() => window.close(), 2000)</script>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Vimix – Sign in failed</title>
  <style>
    body { font-family: system-ui, sans-serif; display: flex; align-items: center;
           justify-content: center; min-height: 100vh; margin: 0; background: #0a0a0a; color: #fafafa; }
    .card { text-align: center; padding: 2rem; }
    .x { font-size: 3rem; margin-bottom: 1rem; color: #ef4444; }
    h1 { font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }
    p { color: #a1a1aa; font-size: 0.875rem; margin: 0; }
  </style>
</head>
<body>
  <div class="card">
    <div class="x">&#10007;</div>
    <h1>Sign in failed</h1>
    <p>{error}</p>
  </div>
</body>
</html>"""


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


async def _handle_callback(request: Request) -> HTMLResponse:
    """Handle the OAuth callback from the provider."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(ERROR_HTML.replace("{error}", error), status_code=400)

    if not code or not state:
        return HTMLResponse(
            ERROR_HTML.replace("{error}", "Missing code or state parameter"),
            status_code=400,
        )

    if state not in _pending:
        return HTMLResponse(
            ERROR_HTML.replace("{error}", "Unknown or expired session"),
            status_code=400,
        )

    _pending[state] = code
    logger.info("OAuth callback received for state=%s", state[:8])

    # Schedule shutdown of the callback server
    if _shutdown_event:
        _shutdown_event.set()

    return HTMLResponse(SUCCESS_HTML)


def _create_callback_app() -> Starlette:
    return Starlette(
        routes=[Route("/auth/callback", _handle_callback, methods=["GET"])],
    )


async def _run_callback_server() -> None:
    """Run the temporary callback server with auto-timeout."""
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    app = _create_callback_app()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=CALLBACK_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    # Run server in background
    serve_task = asyncio.create_task(server.serve())

    # Wait for either shutdown signal or timeout
    try:
        await asyncio.wait_for(_shutdown_event.wait(), timeout=TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.info("OAuth callback server timed out after %ds", TIMEOUT_SECONDS)
        # Clean up any pending states
        _pending.clear()

    # Give a moment for the success page to be served
    await asyncio.sleep(1)
    server.should_exit = True
    await serve_task
    logger.info("OAuth callback server stopped")


class OAuthStartRequest(BaseModel):
    state: str


@router.post("/start")
async def oauth_start(body: OAuthStartRequest):
    """Start the OAuth callback listener on port 1455."""
    global _server_task

    # Check if server is already running
    if _server_task and not _server_task.done():
        # Server is running — just register the new state
        _pending[body.state] = None
        return {"status": "listening"}

    if not _port_is_free(CALLBACK_PORT):
        raise HTTPException(
            status_code=409,
            detail=f"Port {CALLBACK_PORT} is already in use",
        )

    _pending[body.state] = None
    _server_task = asyncio.create_task(_run_callback_server())
    return {"status": "listening"}


@router.get("/poll/{state}")
async def oauth_poll(state: str):
    """Poll for the OAuth callback result."""
    if state not in _pending:
        raise HTTPException(status_code=404, detail="Unknown state")

    code = _pending[state]
    if code is None:
        return {"status": "waiting"}

    # Code received — clean up and return it
    del _pending[state]
    return {"status": "received", "code": code}


@router.post("/stop")
async def oauth_stop():
    """Explicitly stop the callback listener."""
    global _server_task
    _pending.clear()
    if _shutdown_event:
        _shutdown_event.set()
    if _server_task and not _server_task.done():
        _server_task.cancel()
        try:
            await _server_task
        except asyncio.CancelledError:
            pass
    _server_task = None
    return {"status": "stopped"}
