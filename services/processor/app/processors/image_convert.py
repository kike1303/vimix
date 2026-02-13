from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class ImageConvertProcessor(BaseProcessor):
    id = "image-convert"
    label = "Image Format Conversion"
    description = "Convert an image to a different format with optional resizing."
    accepted_extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "png",
                "choices": [
                    {"value": "png", "label": "PNG"},
                    {"value": "jpg", "label": "JPG"},
                    {"value": "webp", "label": "WebP"},
                    {"value": "bmp", "label": "BMP"},
                    {"value": "tiff", "label": "TIFF"},
                    {"value": "gif", "label": "GIF"},
                ],
            },
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 90,
                "min": 1,
                "max": 100,
                "step": 1,
            },
            {
                "id": "resize",
                "label": "Resize width",
                "type": "dimension",
                "default": "original",
                "min": 16,
                "max": 7680,
                "presets": [1920, 1280, 1024, 512, 256],
                "allow_original": True,
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
        out_format: str = str(opts.get("format", "png"))
        quality: int = int(opts.get("quality", 90))
        resize: str = str(opts.get("resize", "original"))

        output_file = output_dir / f"output.{out_format}"

        await on_progress(20, "Converting image...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _convert_image, input_path, output_file, out_format, quality, resize
        )

        await on_progress(100, "Done!")
        return output_file


def _convert_image(
    src: Path, dest: Path, fmt: str, quality: int, resize: str
) -> None:
    with Image.open(src) as im:
        # Resize if requested (maintain aspect ratio)
        if resize != "original":
            target_w = int(resize)
            ratio = target_w / im.width
            target_h = round(im.height * ratio)
            im = im.resize((target_w, target_h), Image.LANCZOS)

        # Handle color mode for formats that don't support alpha
        if fmt in ("jpg", "bmp", "gif"):
            if im.mode == "RGBA":
                background = Image.new("RGB", im.size, (255, 255, 255))
                background.paste(im, mask=im.split()[3])
                im = background
            else:
                im = im.convert("RGB")

        save_kwargs: dict[str, Any] = {}
        if fmt in ("jpg", "webp"):
            save_kwargs["quality"] = quality
        if fmt == "png":
            # PNG compression level: map quality 1-100 to compress_level 9-0
            save_kwargs["compress_level"] = max(0, 9 - (quality * 9 // 100))
        if fmt == "tiff":
            save_kwargs["compression"] = "tiff_lzw"

        # Pillow uses "JPEG" internally for jpg
        pil_format = "JPEG" if fmt == "jpg" else fmt.upper()
        im.save(dest, format=pil_format, **save_kwargs)
