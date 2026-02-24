from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfRotateProcessor(BaseProcessor):
    id = "pdf-rotate"
    label = "Rotate PDF"
    description = "Rotate all or specific pages of a PDF by 90, 180, or 270 degrees."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "angle",
                "label": "Angle",
                "type": "select",
                "default": "90",
                "choices": [
                    {"value": "90", "label": "90°"},
                    {"value": "180", "label": "180°"},
                    {"value": "270", "label": "270°"},
                ],
            },
            {
                "id": "pages",
                "label": "Pages",
                "type": "select",
                "default": "all",
                "choices": [
                    {"value": "all", "label": "All pages"},
                    {"value": "range", "label": "Page range"},
                ],
            },
            {
                "id": "range",
                "label": "Page range",
                "type": "text",
                "default": "1-3",
                "showWhen": {"pages": "range"},
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
        angle = int(opts.get("angle", 90))
        pages_mode = str(opts.get("pages", "all"))
        page_range = str(opts.get("range", "1-3"))
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Rotating pages...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _rotate_pdf, input_path, output_file, angle, pages_mode, page_range
        )

        await on_progress(100, "Done!")
        return output_file


def _parse_page_range(range_str: str, total_pages: int) -> list[int]:
    pages: list[int] = []
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = max(1, int(start_s.strip()))
            end = min(total_pages, int(end_s.strip()))
            pages.extend(range(start - 1, end))
        else:
            num = int(part)
            if 1 <= num <= total_pages:
                pages.append(num - 1)
    return list(dict.fromkeys(pages))


def _rotate_pdf(src: Path, dest: Path, angle: int, pages_mode: str, page_range: str) -> None:
    import pymupdf as fitz

    doc = fitz.open(str(src))
    total = len(doc)

    if pages_mode == "range":
        indices = _parse_page_range(page_range, total)
    else:
        indices = list(range(total))

    for idx in indices:
        page = doc[idx]
        page.set_rotation((page.rotation + angle) % 360)

    doc.save(str(dest))
    doc.close()
