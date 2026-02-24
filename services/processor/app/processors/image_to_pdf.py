from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)

_PAGE_SIZES = {
    "a4": (595.276, 841.890),
    "letter": (612, 792),
}


class ImageToPdfProcessor(BaseProcessor):
    id = "image-to-pdf"
    label = "Image to PDF"
    description = "Convert one or more images into a single PDF document."
    accepted_extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]

    @property
    def accepts_multiple_files(self) -> bool:
        return True

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "page_size",
                "label": "Page size",
                "type": "select",
                "default": "a4",
                "choices": [
                    {"value": "a4", "label": "A4"},
                    {"value": "letter", "label": "Letter"},
                    {"value": "original", "label": "Original size"},
                ],
            },
            {
                "id": "orientation",
                "label": "Orientation",
                "type": "select",
                "default": "portrait",
                "choices": [
                    {"value": "portrait", "label": "Portrait"},
                    {"value": "landscape", "label": "Landscape"},
                ],
                "showWhen": {"page_size": ["a4", "letter"]},
            },
            {
                "id": "margin",
                "label": "Margin (mm)",
                "type": "number",
                "default": 10,
                "min": 0,
                "max": 50,
                "step": 5,
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
        paths = input_paths or [input_path]
        opts = options or {}
        page_size = str(opts.get("page_size", "a4"))
        orientation = str(opts.get("orientation", "portrait"))
        margin_mm = int(opts.get("margin", 10))
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Creating PDF from images...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _images_to_pdf, paths, output_file, page_size, orientation, margin_mm
        )

        await on_progress(100, "Done!")
        return output_file


def _images_to_pdf(
    paths: list[Path],
    output: Path,
    page_size: str,
    orientation: str,
    margin_mm: int,
) -> None:
    import pymupdf as fitz
    from PIL import Image

    margin_pt = margin_mm * 72 / 25.4  # mm to points
    doc = fitz.open()

    for img_path in paths:
        # Get image dimensions
        with Image.open(img_path) as im:
            img_w, img_h = im.size

        if page_size == "original":
            # Use image dimensions as page size (pixels -> points at 72 DPI)
            pw, ph = float(img_w), float(img_h)
        else:
            pw, ph = _PAGE_SIZES[page_size]
            if orientation == "landscape":
                pw, ph = ph, pw

        page = doc.new_page(width=pw, height=ph)

        # Calculate image rect with margins
        avail_w = pw - 2 * margin_pt
        avail_h = ph - 2 * margin_pt

        if avail_w <= 0 or avail_h <= 0:
            avail_w, avail_h = pw, ph
            margin_pt_used = 0.0
        else:
            margin_pt_used = margin_pt

        # Scale image to fit within available area
        scale = min(avail_w / img_w, avail_h / img_h)
        if page_size == "original":
            scale = 1.0

        disp_w = img_w * scale
        disp_h = img_h * scale

        # Center the image
        x0 = margin_pt_used + (avail_w - disp_w) / 2
        y0 = margin_pt_used + (avail_h - disp_h) / 2

        rect = fitz.Rect(x0, y0, x0 + disp_w, y0 + disp_h)
        page.insert_image(rect, filename=str(img_path))

    doc.save(str(output))
    doc.close()
