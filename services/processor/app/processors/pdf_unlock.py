from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfUnlockProcessor(BaseProcessor):
    id = "pdf-unlock"
    label = "Unlock PDF"
    description = "Remove password protection from a PDF file."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "password",
                "label": "Current password",
                "type": "text",
                "default": "",
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
        password = str(opts.get("password", ""))
        output_file = output_dir / "output.pdf"

        if not password:
            raise ValueError("Password is required")

        await on_progress(10, "Unlocking PDF...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _unlock_pdf, input_path, output_file, password
        )

        await on_progress(100, "Done!")
        return output_file


def _unlock_pdf(src: Path, dest: Path, password: str) -> None:
    import pymupdf as fitz

    doc = fitz.open(str(src))
    if doc.is_encrypted:
        if not doc.authenticate(password):
            doc.close()
            raise ValueError("Incorrect password")

    doc.save(str(dest), encryption=fitz.PDF_ENCRYPT_NONE)
    doc.close()
