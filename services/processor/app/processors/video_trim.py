from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg


class VideoTrimProcessor(BaseProcessor):
    id = "video-trim"
    label = "Trim Video"
    description = "Cut a segment from a video by selecting start time and duration."
    accepted_extensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "start",
                "label": "Start time (seconds)",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 3600,
                "step": 1,
            },
            {
                "id": "duration",
                "label": "Duration (seconds)",
                "type": "number",
                "default": 10,
                "min": 1,
                "max": 300,
                "step": 1,
            },
            {
                "id": "codec",
                "label": "Re-encode",
                "type": "select",
                "default": "copy",
                "choices": [
                    {"value": "copy", "label": "No (fast)"},
                    {"value": "h264", "label": "H.264"},
                    {"value": "h265", "label": "H.265"},
                ],
            },
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 80,
                "min": 1,
                "max": 100,
                "step": 1,
                "showWhen": {"codec": ["h264", "h265"]},
            },
        ]

    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict[str, Any] | None = None,
    ) -> Path:
        opts = options or {}
        start: int = int(opts.get("start", 0))
        duration: int = int(opts.get("duration", 10))
        codec: str = str(opts.get("codec", "copy"))
        quality_pct: int = int(opts.get("quality", 80))

        ext = input_path.suffix.lower()
        # If re-encoding, output as mp4
        if codec != "copy":
            ext = ".mp4"
        output_file = output_dir / f"output{ext}"

        await on_progress(10, "Trimming video...")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-ss", str(start),
            "-t", str(duration),
            "-i", str(input_path),
        ]

        if codec == "copy":
            cmd += ["-c", "copy"]
        elif codec == "h264":
            crf = round((100 - quality_pct) * 51 / 99)
            cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-c:a", "aac"]
        elif codec == "h265":
            crf = round((100 - quality_pct) * 51 / 99)
            cmd += ["-c:v", "libx265", "-crf", str(crf), "-preset", "medium", "-c:a", "aac"]

        cmd += ["-y", str(output_file)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg trim failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
