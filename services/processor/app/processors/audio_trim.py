from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg


class AudioTrimProcessor(BaseProcessor):
    id = "audio-trim"
    label = "Trim Audio"
    description = "Cut a segment from an audio file by selecting start time and duration."
    accepted_extensions = [".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a", ".wma"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "start",
                "label": "Start time",
                "type": "text",
                "default": "00:00:00",
            },
            {
                "id": "duration",
                "label": "Duration",
                "type": "text",
                "default": "00:00:30",
            },
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "same",
                "choices": [
                    {"value": "same", "label": "Same as input"},
                    {"value": "mp3", "label": "MP3"},
                    {"value": "wav", "label": "WAV"},
                    {"value": "aac", "label": "AAC"},
                    {"value": "ogg", "label": "OGG"},
                    {"value": "flac", "label": "FLAC"},
                ],
            },
        ]

    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict[str, Any] | None = None,
        input_paths: list[Path] | None = None,
    ) -> Path:
        opts = options or {}
        start = str(opts.get("start", "00:00:00"))
        duration = str(opts.get("duration", "00:00:30"))
        fmt = str(opts.get("format", "same"))

        if fmt == "same":
            ext = input_path.suffix.lower()
        else:
            ext = f".{fmt}"

        output_file = output_dir / f"output{ext}"

        await on_progress(10, "Trimming audio...")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-i", str(input_path),
            "-ss", start,
            "-t", duration,
            "-c", "copy",
            "-y", str(output_file),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg audio trim failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
