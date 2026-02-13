"""Resolve paths to external binaries (ffmpeg, ffprobe, img2webp).

In development the binaries are expected to be on the system PATH.
When running as a Tauri sidecar (PyInstaller bundle), the binaries live
next to the frozen executable and environment variables override the defaults.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _bundled_dir() -> Path | None:
    """Return the directory containing bundled binaries when frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return None


def get_ffmpeg() -> str:
    """Return the path to ffmpeg."""
    env = os.environ.get("FFMPEG_BIN")
    if env:
        return env

    bundled = _bundled_dir()
    if bundled:
        candidate = bundled / "ffmpeg"
        if candidate.exists():
            return str(candidate)

    return shutil.which("ffmpeg") or "ffmpeg"


def get_ffprobe() -> str:
    """Return the path to ffprobe."""
    env = os.environ.get("FFPROBE_BIN")
    if env:
        return env

    bundled = _bundled_dir()
    if bundled:
        candidate = bundled / "ffprobe"
        if candidate.exists():
            return str(candidate)

    return shutil.which("ffprobe") or "ffprobe"


def get_img2webp() -> str:
    """Return the path to img2webp."""
    env = os.environ.get("IMG2WEBP_BIN")
    if env:
        return env

    bundled = _bundled_dir()
    if bundled:
        candidate = bundled / "img2webp"
        if candidate.exists():
            return str(candidate)

    return shutil.which("img2webp") or "img2webp"
