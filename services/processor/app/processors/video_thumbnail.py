from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg


class VideoThumbnailProcessor(BaseProcessor):
    id = "video-thumbnail"
    label = "Video Thumbnail"
    description = "Extract a frame from a video at a specific time as an image."
    accepted_extensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "time",
                "label": "Time (seconds)",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 3600,
                "step": 1,
            },
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "png",
                "choices": [
                    {"value": "png", "label": "PNG"},
                    {"value": "jpg", "label": "JPG"},
                    {"value": "webp", "label": "WebP"},
                ],
            },
            {
                "id": "resolution",
                "label": "Resolution",
                "type": "select",
                "default": "original",
                "choices": [
                    {"value": "original", "label": "Original"},
                    {"value": "1920", "label": "1920 px"},
                    {"value": "1280", "label": "1280 px"},
                    {"value": "640", "label": "640 px"},
                ],
            },
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 95,
                "min": 1,
                "max": 100,
                "step": 1,
                "showWhen": {"format": ["jpg", "webp"]},
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
        time: int = int(opts.get("time", 0))
        fmt: str = str(opts.get("format", "png"))
        resolution: str = str(opts.get("resolution", "original"))
        quality: int = int(opts.get("quality", 95))

        output_file = output_dir / f"thumbnail.{fmt}"

        await on_progress(20, "Extracting frame...")

        # Build filter chain
        filters: list[str] = []
        if resolution != "original":
            filters.append(f"scale={resolution}:-2")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-ss", str(time),
            "-i", str(input_path),
            "-frames:v", "1",
        ]

        if filters:
            cmd += ["-vf", ",".join(filters)]

        # Format-specific options
        if fmt == "jpg":
            cmd += ["-q:v", str(max(1, 31 - (quality * 30 // 100)))]
        elif fmt == "webp":
            cmd += ["-quality", str(quality)]

        cmd += ["-y", str(output_file)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg thumbnail failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
