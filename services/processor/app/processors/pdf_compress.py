from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class PdfCompressProcessor(BaseProcessor):
    id = "pdf-compress"
    label = "Compress PDF"
    description = "Reduce PDF file size by compressing content and images."
    accepted_extensions = [".pdf"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "quality",
                "label": "Quality",
                "type": "select",
                "default": "medium",
                "choices": [
                    {"value": "low", "label": "Low (smallest)"},
                    {"value": "medium", "label": "Medium"},
                    {"value": "high", "label": "High (best quality)"},
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
        quality = str(opts.get("quality", "medium"))
        output_file = output_dir / "output.pdf"

        await on_progress(10, "Compressing PDF...")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(_pool, _compress_pdf, input_path, output_file, quality)

        await on_progress(100, "Done!")
        return output_file


def _compress_pdf(src: Path, dest: Path, quality: str) -> None:
    import fitz

    image_quality = {"low": 30, "medium": 60, "high": 85}[quality]

    doc = fitz.open(str(src))

    for page in doc:
        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if base_image is None:
                    continue
                image_bytes = base_image["image"]

                from PIL import Image
                import io

                with Image.open(io.BytesIO(image_bytes)) as im:
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=image_quality, optimize=True)
                    compressed = buf.getvalue()

                if len(compressed) < len(image_bytes):
                    doc.update_stream(xref, compressed)
            except Exception:
                continue

    doc.save(
        str(dest),
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        garbage=4,
        clean=True,
    )
    doc.close()
