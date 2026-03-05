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
    import pymupdf as fitz

    image_quality = {"low": 30, "medium": 60, "high": 85}[quality]

    doc = fitz.open(str(src))

    seen_xrefs: set[int] = set()
    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                pix = fitz.Pixmap(doc, xref)
                has_alpha = pix.n > 3
                if has_alpha:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                jpeg_bytes = pix.tobytes("jpeg", jpg_quality=image_quality)
                current_stream = doc.xref_stream(xref)

                if current_stream is None or len(jpeg_bytes) >= len(current_stream):
                    continue

                # Store raw JPEG — do NOT let update_stream apply FlateDecode on top
                doc.update_stream(xref, jpeg_bytes, compress=False)

                # Update the image XObject dictionary to match the new JPEG stream
                colorspace = "/DeviceGray" if pix.n == 1 else "/DeviceRGB"
                doc.xref_set_key(xref, "Filter", "/DCTDecode")
                doc.xref_set_key(xref, "ColorSpace", colorspace)
                doc.xref_set_key(xref, "BitsPerComponent", "8")
                doc.xref_set_key(xref, "Width", str(pix.width))
                doc.xref_set_key(xref, "Height", str(pix.height))
                if has_alpha:
                    # SMask referenced an alpha channel we've dropped; remove it
                    doc.xref_set_key(xref, "SMask", "")
                # Remove any decode array that applied to the old format
                doc.xref_set_key(xref, "Decode", "")
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
