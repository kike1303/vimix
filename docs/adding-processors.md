# Adding New Processors

This guide explains how to add a new media processing capability to Vimix.

## 1. Create the processor class

Create a new file in `services/processor/app/processors/`:

```python
# services/processor/app/processors/png_to_webp.py

from pathlib import Path
from PIL import Image
from app.processors.base import BaseProcessor, ProgressCallback


class PngToWebpProcessor(BaseProcessor):
    id = "png-to-webp"
    label = "PNG to WebP"
    description = "Convert a PNG image to WebP format."
    accepted_extensions = [".png"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "quality",
                "label": "Quality",
                "type": "number",
                "default": 90,
                "min": 1,
                "max": 100,
                "step": 1,
            },
        ]

    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict | None = None,
    ) -> Path:
        opts = options or {}
        quality = int(opts.get("quality", 90))
        output_file = output_dir / "output.webp"

        await on_progress(10, "Converting...")

        with Image.open(input_path) as im:
            im.save(output_file, "WEBP", quality=quality)

        await on_progress(100, "Done!")
        return output_file
```

### Required properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique identifier (used in API calls) |
| `label` | `str` | Human-readable name (shown in UI) |
| `description` | `str` | Short description (shown in UI) |
| `accepted_extensions` | `list[str]` | File extensions with dot (e.g. `[".png", ".jpg"]`) |

### Optional: `options_schema` property

Override `options_schema` to expose configurable options in the UI. The frontend renders controls automatically based on this schema. Supported types:

- **`number`**: renders a range slider. Fields: `min`, `max`, `step`.
- **`select`**: renders toggle buttons. Field: `choices` (list of `{"value", "label"}`).

If you don't override it, the processor will have no options (which is fine).

### Required method

`process(input_path, output_dir, on_progress, options) -> Path`

- `input_path`: Path to the uploaded file.
- `output_dir`: Writable directory for intermediate files and the final output.
- `on_progress`: Async callback — call `await on_progress(percent, message)` to report progress (0–100).
- `options`: Dict of user-selected values matching your `options_schema`. Always provide defaults.
- **Return**: Path to the final output file.

## 2. Register the processor

Open `services/processor/app/processors/registry.py` and add:

```python
from app.processors.png_to_webp import PngToWebpProcessor

_register(PngToWebpProcessor())
```

That's it. The processor will automatically:
- Appear in `GET /processors`
- Be selectable in the frontend dropdown
- Accept files with the specified extensions

## 3. Add dependencies (if needed)

If your processor needs new Python packages, add them to `services/processor/requirements.txt` and reinstall:

```bash
cd services/processor
pip install -r requirements.txt
```

## Tips

- Use `asyncio.create_subprocess_exec()` for external tools (like FFmpeg).
- Use `loop.run_in_executor()` for CPU-heavy sync code (like image processing with Pillow).
- Report progress granularly — users see it in real time via SSE.
- Put intermediate files in `output_dir` — they are cleaned up automatically.
