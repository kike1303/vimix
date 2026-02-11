from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image
from rembg import new_session, remove

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class ImageBgRemoveProcessor(BaseProcessor):
    id = "image-bg-remove"
    label = "Image Background Removal"
    description = "Remove the background from an image and export with transparency."
    accepted_extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "model",
                "label": "AI model",
                "type": "select",
                "default": "u2netp",
                "choices": [
                    {"value": "u2netp", "label": "Fast (u2netp)"},
                    {"value": "u2net", "label": "Quality (u2net)"},
                    {"value": "isnet-general-use", "label": "ISNet"},
                ],
            },
            {
                "id": "refine_edges",
                "label": "Refine edges",
                "type": "select",
                "default": "off",
                "choices": [
                    {"value": "off", "label": "Off"},
                    {"value": "on", "label": "On"},
                ],
            },
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "png",
                "choices": [
                    {"value": "png", "label": "PNG"},
                    {"value": "webp", "label": "WebP"},
                ],
            },
        ]

    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict[str, Any] | None = None,
    ) -> Path:
        opts = options or {}
        model_name: str = str(opts.get("model", "u2netp"))
        refine_edges: bool = str(opts.get("refine_edges", "off")) == "on"
        out_format: str = str(opts.get("format", "png"))

        output_file = output_dir / f"output.{out_format}"

        await on_progress(10, f"Loading model ({model_name})...")
        loop = asyncio.get_running_loop()
        session = await loop.run_in_executor(_pool, new_session, model_name)

        await on_progress(30, "Removing background...")
        await loop.run_in_executor(
            _pool, _process_image, input_path, output_file, session, refine_edges
        )

        await on_progress(100, "Done!")
        return output_file


def _process_image(
    src: Path, dest: Path, session: object, refine_edges: bool
) -> None:
    with Image.open(src) as im:
        im = im.convert("RGBA")
        result = remove(
            im,
            session=session,
            alpha_matting=refine_edges,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )
        if isinstance(result, bytes):
            dest.write_bytes(result)
        else:
            result.save(dest)
