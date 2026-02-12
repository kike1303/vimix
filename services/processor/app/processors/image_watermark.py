from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.processors.base import BaseProcessor, ProgressCallback

_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)

_POSITIONS: dict[str, str] = {
    "bottom-right": "br",
    "bottom-left": "bl",
    "top-right": "tr",
    "top-left": "tl",
    "center": "c",
}


class ImageWatermarkProcessor(BaseProcessor):
    id = "image-watermark"
    label = "Image Watermark"
    description = "Add a text watermark to an image with position, size, and opacity controls."
    accepted_extensions = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "text",
                "label": "Watermark text",
                "type": "text",
                "default": "Vimix",
            },
            {
                "id": "position",
                "label": "Position",
                "type": "select",
                "default": "bottom-right",
                "choices": [
                    {"value": "bottom-right", "label": "Bottom right"},
                    {"value": "bottom-left", "label": "Bottom left"},
                    {"value": "top-right", "label": "Top right"},
                    {"value": "top-left", "label": "Top left"},
                    {"value": "center", "label": "Center"},
                ],
            },
            {
                "id": "size",
                "label": "Font size",
                "type": "number",
                "default": 5,
                "min": 1,
                "max": 20,
                "step": 1,
            },
            {
                "id": "opacity",
                "label": "Opacity",
                "type": "number",
                "default": 50,
                "min": 5,
                "max": 100,
                "step": 5,
            },
            {
                "id": "color",
                "label": "Color",
                "type": "select",
                "default": "white",
                "choices": [
                    {"value": "white", "label": "White"},
                    {"value": "black", "label": "Black"},
                    {"value": "red", "label": "Red"},
                    {"value": "gray", "label": "Gray"},
                ],
            },
            {
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "png",
                "choices": [
                    {"value": "png", "label": "PNG"},
                    {"value": "jpg", "label": "JPG"},
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
        text: str = str(opts.get("text", "Vimix"))
        position: str = str(opts.get("position", "bottom-right"))
        size_pct: int = int(opts.get("size", 5))
        opacity: int = int(opts.get("opacity", 50))
        color: str = str(opts.get("color", "white"))
        fmt: str = str(opts.get("format", "png"))

        output_file = output_dir / f"output.{fmt}"

        await on_progress(20, "Adding watermark...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            _pool,
            _apply_watermark,
            input_path,
            output_file,
            fmt,
            text,
            position,
            size_pct,
            opacity,
            color,
        )

        await on_progress(100, "Done!")
        return output_file


_COLORS: dict[str, tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (220, 38, 38),
    "gray": (156, 163, 175),
}


def _apply_watermark(
    src: Path,
    dest: Path,
    fmt: str,
    text: str,
    position: str,
    size_pct: int,
    opacity: int,
    color: str,
) -> None:
    with Image.open(src) as im:
        im = im.convert("RGBA")

        # Font size relative to image width
        font_size = max(12, int(im.width * size_pct / 100))

        # Try to load a clean font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        # Create transparent overlay for the watermark
        overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Measure text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Padding from edges
        pad = max(10, int(im.width * 0.02))

        # Calculate position
        pos_key = _POSITIONS.get(position, "br")
        if pos_key == "br":
            x = im.width - text_w - pad
            y = im.height - text_h - pad
        elif pos_key == "bl":
            x = pad
            y = im.height - text_h - pad
        elif pos_key == "tr":
            x = im.width - text_w - pad
            y = pad
        elif pos_key == "tl":
            x = pad
            y = pad
        else:  # center
            x = (im.width - text_w) // 2
            y = (im.height - text_h) // 2

        # Draw text with opacity
        rgb = _COLORS.get(color, (255, 255, 255))
        alpha = int(255 * opacity / 100)
        fill = (*rgb, alpha)

        draw.text((x, y), text, font=font, fill=fill)

        # Composite
        result = Image.alpha_composite(im, overlay)

        # Save
        pil_format = "JPEG" if fmt == "jpg" else fmt.upper()
        save_kwargs: dict[str, Any] = {}

        if pil_format == "JPEG":
            result = result.convert("RGB")
            save_kwargs["quality"] = 95
        elif pil_format == "WEBP":
            save_kwargs["quality"] = 95

        result.save(dest, format=pil_format, **save_kwargs)
