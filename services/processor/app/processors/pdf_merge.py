from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfMergeProcessor(BaseProcessor):
    id = "pdf-merge"
    label = "Merge PDFs"
    description = "Combine multiple PDF files into a single document."
    accepted_extensions = [".pdf"]

    @property
    def accepts_multiple_files(self) -> bool:
        return True

    @property
    def options_schema(self) -> list[dict]:
        return []

    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict[str, Any] | None = None,
        input_paths: list[Path] | None = None,
    ) -> Path:
        paths = input_paths or [input_path]
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Merging PDFs...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(_pool, _merge_pdfs, paths, output_file)

        await on_progress(100, "Done!")
        return output_file


def _merge_pdfs(paths: list[Path], output: Path) -> None:
    import fitz

    result = fitz.open()
    for p in paths:
        doc = fitz.open(str(p))
        result.insert_pdf(doc)
        doc.close()
    result.save(str(output))
    result.close()
