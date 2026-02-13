from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg

# Codec → FFmpeg encoder + pixel format + file extension
_CODECS: dict[str, dict[str, str]] = {
    "h264":    {"encoder": "libx264",    "pix_fmt": "yuv420p", "ext": "mp4"},
    "h265":    {"encoder": "libx265",    "pix_fmt": "yuv420p", "ext": "mp4"},
    "vp9":     {"encoder": "libvpx-vp9", "pix_fmt": "yuv420p", "ext": "webm"},
    "prores":  {"encoder": "prores_ks",  "pix_fmt": "yuv422p10le", "ext": "mov"},
    "copy":    {"encoder": "copy",       "pix_fmt": "",        "ext": ""},
}


class VideoConvertProcessor(BaseProcessor):
    id = "video-convert"
    label = "Video Format Conversion"
    description = "Convert a video to a different format, codec, or resolution."
    accepted_extensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "codec",
                "label": "Codec",
                "type": "select",
                "default": "h264",
                "choices": [
                    {"value": "h264", "label": "H.264 (MP4)"},
                    {"value": "h265", "label": "H.265 (MP4)"},
                    {"value": "vp9", "label": "VP9 (WebM)"},
                    {"value": "prores", "label": "ProRes (MOV)"},
                    {"value": "copy", "label": "Copy (no re-encode)"},
                ],
            },
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 70,
                "min": 1,
                "max": 100,
                "step": 1,
                "showWhen": {"codec": ["h264", "h265", "vp9"]},
            },
            {
                "id": "resolution",
                "label": "Resolution",
                "type": "select",
                "default": "original",
                "choices": [
                    {"value": "original", "label": "Original"},
                    {"value": "1920", "label": "1920p"},
                    {"value": "1280", "label": "1280p"},
                    {"value": "720", "label": "720p"},
                    {"value": "480", "label": "480p"},
                ],
                "showWhen": {"codec": ["h264", "h265", "vp9", "prores"]},
            },
            {
                "id": "fps",
                "label": "Frames per second",
                "type": "select",
                "default": "original",
                "choices": [
                    {"value": "original", "label": "Original"},
                    {"value": "60", "label": "60"},
                    {"value": "30", "label": "30"},
                    {"value": "24", "label": "24"},
                    {"value": "15", "label": "15"},
                ],
                "showWhen": {"codec": ["h264", "h265", "vp9", "prores"]},
            },
            {
                "id": "audio",
                "label": "Audio",
                "type": "select",
                "default": "keep",
                "choices": [
                    {"value": "keep", "label": "Keep"},
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
    ) -> Path:
        opts = options or {}
        codec_id: str = str(opts.get("codec", "h264"))
        quality_pct: int = int(opts.get("quality", 70))
        resolution: str = str(opts.get("resolution", "original"))
        fps: str = str(opts.get("fps", "original"))
        audio: str = str(opts.get("audio", "keep"))

        codec_info = _CODECS.get(codec_id, _CODECS["h264"])
        encoder = codec_info["encoder"]
        pix_fmt = codec_info["pix_fmt"]
        ext = codec_info["ext"]

        # For "copy" mode, keep the original extension
        if codec_id == "copy":
            ext = input_path.suffix.lstrip(".")

        output_file = output_dir / f"output.{ext}"

        await on_progress(5, "Preparing conversion...")

        # Build FFmpeg command
        cmd: list[str] = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-i", str(input_path),
        ]

        # Video codec
        cmd += ["-c:v", encoder]

        if encoder != "copy":
            # Pixel format
            if pix_fmt:
                cmd += ["-pix_fmt", pix_fmt]

            # Quality: convert 1-100 scale to CRF (lower CRF = better)
            if codec_id in ("h264", "h265"):
                crf = round((100 - quality_pct) * 51 / 99)
                cmd += ["-crf", str(crf)]
            elif codec_id == "vp9":
                crf = round((100 - quality_pct) * 63 / 99)
                cmd += ["-crf", str(crf), "-b:v", "0"]
            elif codec_id == "prores":
                cmd += ["-profile:v", "3"]  # HQ profile

            # Resolution
            if resolution != "original":
                cmd += ["-vf", f"scale={resolution}:-2"]

            # FPS
            if fps != "original":
                cmd += ["-r", fps]

        # Audio
        if audio == "remove":
            cmd += ["-an"]
        else:
            if encoder == "copy":
                cmd += ["-c:a", "copy"]
            else:
                cmd += ["-c:a", "aac", "-b:a", "128k"]

        cmd += ["-y", str(output_file)]

        await on_progress(10, f"Converting with {encoder}...")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
