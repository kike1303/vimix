from __future__ import annotations

import asyncio
import math
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfWatermarkProcessor(BaseProcessor):
    id = "pdf-watermark"
    label = "PDF Watermark"
    description = "Add a text watermark to every page of a PDF document."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "text",
                "label": "Watermark text",
                "type": "text",
                "default": "CONFIDENTIAL",
            },
            {
                "id": "opacity",
                "label": "Opacity",
                "type": "number",
                "default": 30,
                "min": 5,
                "max": 100,
                "step": 5,
            },
            {
                "id": "angle",
                "label": "Angle",
                "type": "number",
                "default": -45,
                "min": -90,
                "max": 90,
                "step": 5,
            },
            {
                "id": "font_size",
                "label": "Font size",
                "type": "number",
                "default": 48,
                "min": 12,
                "max": 120,
                "step": 4,
            },
            {
                "id": "color",
                "label": "Color",
                "type": "select",
                "default": "gray",
                "choices": [
                    {"value": "gray", "label": "Gray"},
                    {"value": "red", "label": "Red"},
                    {"value": "blue", "label": "Blue"},
                    {"value": "black", "label": "Black"},
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
        text = str(opts.get("text", "CONFIDENTIAL"))
        opacity = int(opts.get("opacity", 30)) / 100.0
        angle = int(opts.get("angle", -45))
        font_size = int(opts.get("font_size", 48))
        color = str(opts.get("color", "gray"))
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Adding watermark...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _add_watermark, input_path, output_file, text, opacity, angle, font_size, color
        )

        await on_progress(100, "Done!")
        return output_file


_COLORS: dict[str, tuple[float, float, float]] = {
    "gray": (0.5, 0.5, 0.5),
    "red": (0.8, 0.1, 0.1),
    "blue": (0.1, 0.1, 0.8),
    "black": (0, 0, 0),
}


def _add_watermark(
    src: Path,
    dest: Path,
    text: str,
    opacity: float,
    angle: int,
    font_size: int,
    color: str,
) -> None:
    import fitz

    doc = fitz.open(str(src))
    rgb = _COLORS.get(color, _COLORS["gray"])

    for page in doc:
        rect = page.rect
        cx, cy = rect.width / 2, rect.height / 2

        # Create text with rotation using a text writer
        tw = fitz.TextWriter(page.rect, opacity=opacity)
        tw.append(
            fitz.Point(cx, cy),
            text,
            fontsize=font_size,
        )

        # Calculate rotation matrix centered on page
        morph = (fitz.Point(cx, cy), fitz.Matrix(angle))
        tw.write_text(page, morph=morph, color=rgb)

    doc.save(str(dest))
    doc.close()
