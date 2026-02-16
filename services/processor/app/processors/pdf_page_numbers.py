from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfPageNumbersProcessor(BaseProcessor):
    id = "pdf-page-numbers"
    label = "Add Page Numbers"
    description = "Add page numbers to every page of a PDF document."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "position",
                "label": "Position",
                "type": "select",
                "default": "bottom-center",
                "choices": [
                    {"value": "bottom-center", "label": "Bottom center"},
                    {"value": "bottom-right", "label": "Bottom right"},
                    {"value": "bottom-left", "label": "Bottom left"},
                    {"value": "top-center", "label": "Top center"},
                    {"value": "top-right", "label": "Top right"},
                    {"value": "top-left", "label": "Top left"},
                ],
            },
            {
                "id": "start_number",
                "label": "Start number",
                "type": "number",
                "default": 1,
                "min": 1,
                "max": 9999,
                "step": 1,
            },
            {
                "id": "font_size",
                "label": "Font size",
                "type": "number",
                "default": 12,
                "min": 6,
                "max": 36,
                "step": 1,
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
        position = str(opts.get("position", "bottom-center"))
        start_number = int(opts.get("start_number", 1))
        font_size = int(opts.get("font_size", 12))
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Adding page numbers...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _add_page_numbers, input_path, output_file, position, start_number, font_size
        )

        await on_progress(100, "Done!")
        return output_file


def _add_page_numbers(
    src: Path, dest: Path, position: str, start_number: int, font_size: int
) -> None:
    import fitz

    doc = fitz.open(str(src))
    total = len(doc)
    margin = 36  # 0.5 inch

    for i, page in enumerate(doc):
        rect = page.rect
        num_text = str(start_number + i)

        if "bottom" in position:
            y = rect.height - margin
        else:
            y = margin + font_size

        if "center" in position:
            x = rect.width / 2
        elif "right" in position:
            x = rect.width - margin
        else:
            x = margin

        # Determine text alignment
        if "center" in position:
            # Approximate centering: measure text width
            text_width = fitz.get_text_length(num_text, fontsize=font_size)
            x -= text_width / 2
        elif "right" in position:
            text_width = fitz.get_text_length(num_text, fontsize=font_size)
            x -= text_width

        point = fitz.Point(x, y)
        page.insert_text(
            point,
            num_text,
            fontsize=font_size,
            color=(0, 0, 0),
        )

    doc.save(str(dest))
    doc.close()
