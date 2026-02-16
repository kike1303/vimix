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
                "default": "u2net",
                "choices": [
                    {"value": "u2net", "label": "Quality (u2net)"},
                    {"value": "isnet-general-use", "label": "ISNet"},
                    {"value": "u2netp", "label": "Fast (u2netp)"},
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
                "id": "fg_threshold",
                "label": "Foreground threshold",
                "type": "number",
                "default": 240,
                "min": 0,
                "max": 255,
                "step": 1,
                "showWhen": {"refine_edges": "on"},
            },
            {
                "id": "bg_threshold",
                "label": "Background threshold",
                "type": "number",
                "default": 10,
                "min": 0,
                "max": 255,
                "step": 1,
                "showWhen": {"refine_edges": "on"},
            },
            {
                "id": "erode_size",
                "label": "Erode size",
                "type": "number",
                "default": 10,
                "min": 1,
                "max": 40,
                "step": 1,
                "showWhen": {"refine_edges": "on"},
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
        input_paths: list[Path] | None = None,
    ) -> Path:
        opts = options or {}
        model_name: str = str(opts.get("model", "u2netp"))
        refine_edges: bool = str(opts.get("refine_edges", "off")) == "on"
        fg_threshold: int = int(opts.get("fg_threshold", 240))
        bg_threshold: int = int(opts.get("bg_threshold", 10))
        erode_size: int = int(opts.get("erode_size", 10))
        out_format: str = str(opts.get("format", "png"))

        output_file = output_dir / f"output.{out_format}"

        await on_progress(10, f"Loading model ({model_name})...")
        loop = asyncio.get_running_loop()
        session = await loop.run_in_executor(_pool, new_session, model_name)

        await on_progress(30, "Removing background...")
        await loop.run_in_executor(
            _pool, _process_image, input_path, output_file, session,
            refine_edges, fg_threshold, bg_threshold, erode_size,
        )

        await on_progress(100, "Done!")
        return output_file


def _process_image(
    src: Path, dest: Path, session: object,
    refine_edges: bool,
    fg_threshold: int = 240,
    bg_threshold: int = 10,
    erode_size: int = 10,
) -> None:
    with Image.open(src) as im:
        im = im.convert("RGBA")
        result = remove(
            im,
            session=session,
            alpha_matting=refine_edges,
            alpha_matting_foreground_threshold=fg_threshold,
            alpha_matting_background_threshold=bg_threshold,
            alpha_matting_erode_size=erode_size,
        )
        if isinstance(result, bytes):
            dest.write_bytes(result)
        else:
            result.save(dest)
