from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg

_FORMAT_CONFIG: dict[str, dict[str, Any]] = {
    "mp3": {"ext": ".mp3", "codec": "libmp3lame", "default_bitrate": "192k"},
    "aac": {"ext": ".aac", "codec": "aac", "default_bitrate": "192k"},
    "wav": {"ext": ".wav", "codec": "pcm_s16le", "default_bitrate": None},
    "flac": {"ext": ".flac", "codec": "flac", "default_bitrate": None},
    "ogg": {"ext": ".ogg", "codec": "libvorbis", "default_bitrate": "192k"},
}


class AudioExtractProcessor(BaseProcessor):
    id = "audio-extract"
    label = "Extract Audio"
    description = "Extract the audio track from a video as MP3, AAC, WAV, FLAC, or OGG."
    accepted_extensions = [".mp4", ".mov", ".webm", ".avi", ".mkv"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "mp3",
                "choices": [
                    {"value": "mp3", "label": "MP3"},
                    {"value": "aac", "label": "AAC"},
                    {"value": "wav", "label": "WAV"},
                    {"value": "flac", "label": "FLAC"},
                    {"value": "ogg", "label": "OGG"},
                ],
            },
            {
                "id": "bitrate",
                "label": "Bitrate",
                "type": "select",
                "default": "192k",
                "choices": [
                    {"value": "320k", "label": "320 kbps"},
                    {"value": "256k", "label": "256 kbps"},
                    {"value": "192k", "label": "192 kbps"},
                    {"value": "128k", "label": "128 kbps"},
                    {"value": "96k", "label": "96 kbps"},
                ],
                "showWhen": {"format": ["mp3", "aac", "ogg"]},
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
        fmt: str = str(opts.get("format", "mp3"))
        bitrate: str = str(opts.get("bitrate", "192k"))

        config = _FORMAT_CONFIG[fmt]
        output_file = output_dir / f"output{config['ext']}"

        await on_progress(10, "Extracting audio...")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-i", str(input_path),
            "-vn",
            "-c:a", config["codec"],
        ]

        if config["default_bitrate"] is not None:
            cmd += ["-b:a", bitrate]

        cmd += ["-y", str(output_file)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extract failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
