from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback
from app.services.binary_paths import get_ffmpeg

_FORMAT_CONFIG: dict[str, dict[str, Any]] = {
    "mp3": {"ext": ".mp3", "codec": "libmp3lame"},
    "wav": {"ext": ".wav", "codec": "pcm_s16le"},
    "aac": {"ext": ".aac", "codec": "aac"},
    "ogg": {"ext": ".ogg", "codec": "libvorbis"},
    "flac": {"ext": ".flac", "codec": "flac"},
}


class AudioConvertProcessor(BaseProcessor):
    id = "audio-convert"
    label = "Convert Audio"
    description = "Convert audio files between formats with bitrate and sample rate control."
    accepted_extensions = [".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a", ".wma"]

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
                    {"value": "wav", "label": "WAV"},
                    {"value": "aac", "label": "AAC"},
                    {"value": "ogg", "label": "OGG"},
                    {"value": "flac", "label": "FLAC"},
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
                    {"value": "64k", "label": "64 kbps"},
                ],
                "showWhen": {"format": ["mp3", "aac", "ogg"]},
            },
            {
                "id": "sample_rate",
                "label": "Sample rate",
                "type": "select",
                "default": "44100",
                "choices": [
                    {"value": "48000", "label": "48000 Hz"},
                    {"value": "44100", "label": "44100 Hz"},
                    {"value": "22050", "label": "22050 Hz"},
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
        fmt = str(opts.get("format", "mp3"))
        bitrate = str(opts.get("bitrate", "192k"))
        sample_rate = str(opts.get("sample_rate", "44100"))

        config = _FORMAT_CONFIG[fmt]
        output_file = output_dir / f"output{config['ext']}"

        await on_progress(10, "Converting audio...")

        cmd = [
            get_ffmpeg(), "-hide_banner", "-loglevel", "error",
            "-i", str(input_path),
            "-c:a", config["codec"],
            "-ar", sample_rate,
        ]

        # Add bitrate for lossy formats
        if fmt in ("mp3", "aac", "ogg"):
            cmd += ["-b:a", bitrate]

        cmd += ["-y", str(output_file)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg audio convert failed: {stderr.decode()}")

        await on_progress(100, "Done!")
        return output_file
