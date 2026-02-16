from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfProtectProcessor(BaseProcessor):
    id = "pdf-protect"
    label = "Protect PDF"
    description = "Add password protection and permission restrictions to a PDF."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "password",
                "label": "Password",
                "type": "text",
                "default": "",
            },
            {
                "id": "permissions",
                "label": "Permissions",
                "type": "select",
                "default": "all",
                "choices": [
                    {"value": "all", "label": "All allowed"},
                    {"value": "no_print", "label": "No printing"},
                    {"value": "no_copy", "label": "No copying"},
                    {"value": "read_only", "label": "Read only"},
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
        password = str(opts.get("password", ""))
        permissions = str(opts.get("permissions", "all"))
        output_file = output_dir / "output.pdf"

        if not password:
            raise ValueError("Password is required")

        await on_progress(10, "Protecting PDF...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool, _protect_pdf, input_path, output_file, password, permissions
        )

        await on_progress(100, "Done!")
        return output_file


def _protect_pdf(src: Path, dest: Path, password: str, permissions: str) -> None:
    import fitz

    perm_map = {
        "all": int(
            fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_MODIFY
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        ),
        "no_print": int(
            fitz.PDF_PERM_MODIFY | fitz.PDF_PERM_COPY | fitz.PDF_PERM_ANNOTATE
        ),
        "no_copy": int(
            fitz.PDF_PERM_PRINT | fitz.PDF_PERM_MODIFY | fitz.PDF_PERM_ANNOTATE
        ),
        "read_only": 0,
    }

    perm = perm_map.get(permissions, perm_map["all"])

    doc = fitz.open(str(src))
    doc.save(
        str(dest),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw=password,
        permissions=perm,
    )
    doc.close()
