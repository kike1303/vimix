from __future__ import annotations

import asyncio
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfToImageProcessor(BaseProcessor):
    id = "pdf-to-image"
    label = "PDF to Image"
    description = "Convert PDF pages to images (PNG, JPG, or WebP)."
    accepted_extensions = [".pdf"]

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
                ],
            },
            {
                "id": "dpi",
                "label": "DPI",
                "type": "select",
                "default": "150",
                "choices": [
                    {"value": "72", "label": "72 (fast)"},
                    {"value": "150", "label": "150 (standard)"},
                    {"value": "300", "label": "300 (high)"},
                ],
            },
            {
                "id": "pages",
                "label": "Pages",
                "type": "select",
                "default": "all",
                "choices": [
                    {"value": "all", "label": "All"},
                    {"value": "first", "label": "First only"},
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
        fmt: str = str(opts.get("format", "png"))
        dpi: int = int(opts.get("dpi", 150))
        pages_mode: str = str(opts.get("pages", "all"))
        quality: int = int(opts.get("quality", 90))

        await on_progress(10, "Converting PDF...")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _pool,
            _convert_pdf,
            input_path,
            output_dir,
            fmt,
            dpi,
            pages_mode,
            quality,
        )

        await on_progress(100, "Done!")
        return result


def _convert_pdf(
    src: Path,
    output_dir: Path,
    fmt: str,
    dpi: int,
    pages_mode: str,
    quality: int,
) -> Path:
    import fitz  # PyMuPDF

    doc = fitz.open(str(src))
    total_pages = len(doc)

    if pages_mode == "first":
        page_range = range(1)
    else:
        page_range = range(total_pages)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    image_paths: list[Path] = []

    for i in page_range:
        page = doc[i]
        pix = page.get_pixmap(matrix=matrix)

        ext = "jpg" if fmt == "jpg" else fmt
        page_file = output_dir / f"page_{i + 1:04d}.{ext}"

        if fmt == "png":
            pix.save(str(page_file))
        else:
            # For JPG/WebP, convert via Pillow for quality control
            from PIL import Image
            import io

            img_data = pix.tobytes("png")
            with Image.open(io.BytesIO(img_data)) as im:
                if fmt == "jpg":
                    im = im.convert("RGB")
                    im.save(str(page_file), "JPEG", quality=quality)
                else:
                    im.save(str(page_file), "WEBP", quality=quality)

        image_paths.append(page_file)

    doc.close()

    # Single page → return image directly
    if len(image_paths) == 1:
        return image_paths[0]

    # Multiple pages → zip them
    zip_file = output_dir / "pages.zip"
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in image_paths:
            zf.write(p, p.name)

    return zip_file
