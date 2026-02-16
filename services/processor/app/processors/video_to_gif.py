from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg


class VideoToGifProcessor(BaseProcessor):
    id = "video-to-gif"
    label = "Video to GIF"
    description = "Convert a video clip to an animated GIF."
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
                "max": 600,
                "step": 1,
            },
            {
                "id": "duration",
                "label": "Duration (seconds)",
                "type": "number",
                "default": 5,
                "min": 1,
                "max": 30,
                "step": 1,
            },
            {
                "id": "fps",
                "label": "Frames per second",
                "type": "number",
                "default": 15,
                "min": 5,
                "max": 30,
                "step": 1,
            },
            {
                "id": "resolution",
                "label": "Width",
                "type": "dimension",
                "default": "480",
                "min": 16,
                "max": 7680,
                "presets": [640, 480, 320, 240],
                "allow_original": True,
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
        start: int = int(opts.get("start", 0))
        duration: int = int(opts.get("duration", 5))
        fps: int = int(opts.get("fps", 15))
        resolution: str = str(opts.get("resolution", "480"))

        output_file = output_dir / "output.gif"
        palette_file = output_dir / "palette.png"

        # Build filter chain
        filters = f"fps={fps}"
        if resolution != "original":
            filters += f",scale={resolution}:-1:flags=lanczos"

        # --- Step 1: Generate optimized palette ---
        await on_progress(10, "Generating color palette...")

        palette_cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-ss", str(start),
            "-t", str(duration),
            "-i", str(input_path),
            "-vf", f"{filters},palettegen=stats_mode=diff",
            "-y", str(palette_file),
        ]

        proc = await asyncio.create_subprocess_exec(
            *palette_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg palette failed: {stderr.decode()}")

        # --- Step 2: Create GIF using palette ---
        await on_progress(50, "Creating GIF...")

        gif_cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-ss", str(start),
            "-t", str(duration),
            "-i", str(input_path),
            "-i", str(palette_file),
            "-lavfi", f"{filters} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-y", str(output_file),
        ]

        proc = await asyncio.create_subprocess_exec(
            *gif_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg GIF failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
