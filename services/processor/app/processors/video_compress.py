from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg


class VideoCompressProcessor(BaseProcessor):
    id = "video-compress"
    label = "Compress Video"
    description = "Reduce video file size with quality and resolution controls."
    accepted_extensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 65,
                "min": 1,
                "max": 100,
                "step": 1,
            },
            {
                "id": "resolution",
                "label": "Resolution",
                "type": "dimension",
                "default": "original",
                "min": 16,
                "max": 7680,
                "presets": [1920, 1280, 854, 640],
                "allow_original": True,
            },
            {
                "id": "audio",
                "label": "Audio",
                "type": "select",
                "default": "keep",
                "choices": [
                    {"value": "keep", "label": "Keep"},
                    {"value": "compress", "label": "Compress"},
                    {"value": "remove", "label": "Remove"},
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
        quality_pct: int = int(opts.get("quality", 65))
        resolution: str = str(opts.get("resolution", "original"))
        audio: str = str(opts.get("audio", "keep"))

        output_file = output_dir / "output.mp4"

        # Map quality 1-100 to CRF (lower CRF = better quality)
        crf = round((100 - quality_pct) * 51 / 99)

        await on_progress(10, "Compressing video...")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-i", str(input_path),
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "slow",
        ]

        # Resolution
        if resolution != "original":
            cmd += ["-vf", f"scale={resolution}:-2"]

        # Audio handling
        if audio == "remove":
            cmd += ["-an"]
        elif audio == "compress":
            cmd += ["-c:a", "aac", "-b:a", "96k"]
        else:
            cmd += ["-c:a", "aac", "-b:a", "192k"]

        cmd += ["-movflags", "+faststart", "-y", str(output_file)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg compress failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
