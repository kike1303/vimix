from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfExtractTextProcessor(BaseProcessor):
    id = "pdf-extract-text"
    label = "Extract Text from PDF"
    description = "Extract all text content from a PDF as plain text or JSON."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "txt",
                "choices": [
                    {"value": "txt", "label": "Plain text (.txt)"},
                    {"value": "json", "label": "JSON (.json)"},
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
        fmt = str(opts.get("format", "txt"))
        pages_mode = str(opts.get("pages", "all"))
        page_range = str(opts.get("range", "1-3"))
        output_file = output_dir / f"output.{fmt}"

        await on_progress(10, "Extracting text...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _extract_text, input_path, output_file, fmt, pages_mode, page_range
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


def _extract_text(
    src: Path, dest: Path, fmt: str, pages_mode: str, page_range: str
) -> None:
    import pymupdf as fitz

    doc = fitz.open(str(src))
    total = len(doc)

    if pages_mode == "range":
        indices = _parse_page_range(page_range, total)
    else:
        indices = list(range(total))

    if fmt == "json":
        pages_data = []
        for idx in indices:
            page = doc[idx]
            pages_data.append({
                "page": idx + 1,
                "text": page.get_text("text"),
            })
        dest.write_text(json.dumps(pages_data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        lines: list[str] = []
        for idx in indices:
            page = doc[idx]
            text = page.get_text("text")
            if len(indices) > 1:
                lines.append(f"--- Page {idx + 1} ---")
            lines.append(text)
        dest.write_text("\n".join(lines), encoding="utf-8")

    doc.close()
