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


class PdfSplitProcessor(BaseProcessor):
    id = "pdf-split"
    label = "Split PDF"
    description = "Extract specific pages or split a PDF into separate files."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "mode",
                "label": "Mode",
                "type": "select",
                "default": "all_pages",
                "choices": [
                    {"value": "all_pages", "label": "All pages (separate)"},
                    {"value": "range", "label": "Page range"},
                ],
            },
            {
                "id": "range",
                "label": "Page range",
                "type": "text",
                "default": "1-3",
                "showWhen": {"mode": "range"},
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
        mode = str(opts.get("mode", "all_pages"))
        page_range = str(opts.get("range", "1-3"))

        await on_progress(10, "Splitting PDF...")

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _pool, _split_pdf, input_path, output_dir, mode, page_range
        )

        await on_progress(100, "Done!")
        return result


def _parse_page_range(range_str: str, total_pages: int) -> list[int]:
    """Parse a range string like '1-3,5,7-9' into zero-based page indices."""
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
    # Deduplicate while preserving order
    seen: set[int] = set()
    result: list[int] = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _split_pdf(src: Path, output_dir: Path, mode: str, page_range: str) -> Path:
    import fitz

    doc = fitz.open(str(src))
    total = len(doc)

    if mode == "range":
        indices = _parse_page_range(page_range, total)
        if not indices:
            doc.close()
            raise ValueError(f"No valid pages in range: {page_range}")

        out = fitz.open()
        for idx in indices:
            out.insert_pdf(doc, from_page=idx, to_page=idx)
        result = output_dir / "output.pdf"
        out.save(str(result))
        out.close()
        doc.close()
        return result

    # all_pages mode: split into individual files
    if total == 1:
        result = output_dir / "page_1.pdf"
        out = fitz.open()
        out.insert_pdf(doc, from_page=0, to_page=0)
        out.save(str(result))
        out.close()
        doc.close()
        return result

    pdf_paths: list[Path] = []
    for i in range(total):
        out = fitz.open()
        out.insert_pdf(doc, from_page=i, to_page=i)
        p = output_dir / f"page_{i + 1:04d}.pdf"
        out.save(str(p))
        out.close()
        pdf_paths.append(p)

    doc.close()

    zip_file = output_dir / "pages.zip"
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in pdf_paths:
            zf.write(p, p.name)

    return zip_file
