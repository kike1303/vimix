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

# Map input extensions to Pillow save format + output extension
_FORMAT_MAP: dict[str, tuple[str, str]] = {
    ".png": ("PNG", ".png"),
    ".jpg": ("JPEG", ".jpg"),
    ".jpeg": ("JPEG", ".jpg"),
    ".webp": ("WEBP", ".webp"),
    ".bmp": ("BMP", ".bmp"),
    ".tiff": ("TIFF", ".tiff"),
}


class ImageCompressProcessor(BaseProcessor):
    id = "image-compress"
    label = "Compress Image"
    description = "Reduce image file size with quality and resize controls."
    accepted_extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 75,
                "min": 1,
                "max": 100,
                "step": 1,
            },
            {
                "id": "resize",
                "label": "Max width",
                "type": "dimension",
                "default": "original",
                "min": 16,
                "max": 7680,
                "presets": [1920, 1280, 1024, 800, 640],
                "allow_original": True,
            },
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "auto",
                "choices": [
                    {"value": "auto", "label": "Same as input"},
                    {"value": "webp", "label": "WebP"},
                    {"value": "jpg", "label": "JPG"},
                    {"value": "png", "label": "PNG"},
                ],
            },
            {
                "id": "strip_metadata",
                "label": "Strip metadata",
                "type": "select",
                "default": "on",
                "choices": [
                    {"value": "on", "label": "On"},
                    {"value": "off", "label": "Off"},
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
        quality: int = int(opts.get("quality", 75))
        resize: str = str(opts.get("resize", "original"))
        out_format: str = str(opts.get("format", "auto"))
        strip_metadata: bool = str(opts.get("strip_metadata", "on")) == "on"

        # Determine output format
        if out_format == "auto":
            pil_format, ext = _FORMAT_MAP.get(
                input_path.suffix.lower(), ("WEBP", ".webp")
            )
        else:
            ext_map = {"webp": ".webp", "jpg": ".jpg", "png": ".png"}
            ext = ext_map[out_format]
            pil_format = "JPEG" if out_format == "jpg" else out_format.upper()

        output_file = output_dir / f"output{ext}"

        await on_progress(20, "Compressing image...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool,
            _compress_image,
            input_path,
            output_file,
            pil_format,
            quality,
            resize,
            strip_metadata,
        )

        await on_progress(100, "Done!")
        return output_file


def _compress_image(
    src: Path,
    dest: Path,
    pil_format: str,
    quality: int,
    resize: str,
    strip_metadata: bool,
) -> None:
    with Image.open(src) as im:
        # Resize if requested (only downscale, maintain aspect ratio)
        if resize != "original":
            target_w = int(resize)
            if im.width > target_w:
                ratio = target_w / im.width
                target_h = round(im.height * ratio)
                im = im.resize((target_w, target_h), Image.LANCZOS)

        # Handle alpha for formats that don't support it
        if pil_format in ("JPEG", "BMP"):
            if im.mode == "RGBA":
                background = Image.new("RGB", im.size, (255, 255, 255))
                background.paste(im, mask=im.split()[3])
                im = background
            elif im.mode != "RGB":
                im = im.convert("RGB")

        save_kwargs: dict[str, Any] = {}

        if pil_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            if pil_format == "JPEG":
                save_kwargs["optimize"] = True
        elif pil_format == "PNG":
            save_kwargs["compress_level"] = max(0, 9 - (quality * 9 // 100))
            save_kwargs["optimize"] = True
        elif pil_format == "TIFF":
            save_kwargs["compression"] = "tiff_lzw"

        if strip_metadata:
            # Saving without passing exif/info strips metadata
            im.save(dest, format=pil_format, **save_kwargs)
        else:
            # Preserve original metadata
            info = im.info or {}
            exif = info.get("exif")
            if exif:
                save_kwargs["exif"] = exif
            im.save(dest, format=pil_format, **save_kwargs)
