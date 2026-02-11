# Adding New Processors

This guide explains how to add a new media processing capability to Vimix.

## 1. Create the processor class

Create a new file in `services/processor/app/processors/`:

```python
# services/processor/app/processors/my_processor.py
from __future__ import annotations

from pathlib import Path
from typing import Any
from PIL import Image
from app.processors.base import BaseProcessor, ProgressCallback


class MyProcessor(BaseProcessor):
    id = "my-processor"
    label = "My Processor"
    description = "Does something useful with files."
    accepted_extensions = [".png", ".jpg"]

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
            {
                "id": "mode",
                "label": "Mode",
                "type": "select",
                "default": "fast",
                "choices": [
                    {"value": "fast", "label": "Fast"},
                    {"value": "quality", "label": "Quality"},
                ],
            },
            {
                "id": "advanced_option",
                "label": "Advanced option",
                "type": "number",
                "default": 50,
                "min": 0,
                "max": 100,
                "step": 1,
                "showWhen": {"mode": "quality"},  # Only shown when mode is "quality"
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
        quality = int(opts.get("quality", 90))
        output_file = output_dir / "output.webp"

        await on_progress(10, "Processing...")

        with Image.open(input_path) as im:
            im.save(output_file, "WEBP", quality=quality)

        await on_progress(100, "Done!")
        return output_file
```

### Required properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique identifier (used in API calls and i18n keys) |
| `label` | `str` | Human-readable name (fallback if no i18n translation) |
| `description` | `str` | Short description (fallback if no i18n translation) |
| `accepted_extensions` | `list[str]` | File extensions with dot (e.g. `[".png", ".jpg"]`) |

### Optional: `options_schema` property

Override `options_schema` to expose configurable options in the UI. The frontend renders controls automatically based on this schema. Supported types:

- **`number`**: renders a range slider. Fields: `min`, `max`, `step`.
- **`select`**: renders toggle buttons. Field: `choices` (list of `{"value", "label"}`).

#### Conditional visibility with `showWhen`

Add `showWhen` to an option to only show it when another option has a specific value:

```python
# Show only when "refine_edges" is "on"
{"showWhen": {"refine_edges": "on"}}

# Show when "codec" is any of these values
{"showWhen": {"codec": ["h264", "h265", "vp9"]}}
```

If you don't override `options_schema`, the processor will have no options (which is fine).

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
from app.processors.my_processor import MyProcessor

_register(MyProcessor())
```

## 3. Add an icon (optional)

Open `apps/web/src/lib/processor-icons.ts` and map your processor ID to a lucide icon:

```typescript
import MyIcon from "lucide-svelte/icons/my-icon";

const icons: Record<string, ComponentType> = {
  // ...existing icons...
  "my-processor": MyIcon,
};
```

If you don't add an icon, a default CPU icon will be used.

## 4. Add i18n translations (optional)

Add translations in `apps/web/src/lib/i18n/en.json` and `es.json`:

```json
{
  "processors": {
    "my-processor": {
      "label": "My Processor",
      "description": "Does something useful with files."
    }
  },
  "options": {
    "my_option": {
      "label": "My Option",
      "description": "Tooltip text explaining what this option does."
    }
  }
}
```

If no translation is found, the `label`/`description` from the Python class are used as fallback.

Options with a `description` key in i18n will show an info icon with a tooltip in the UI.

## 5. Add dependencies (if needed)

If your processor needs new Python packages:

```bash
cd services/processor
source venv/bin/activate
pip install new-package
pip freeze > requirements.txt
```

## 6. Add result media type (if needed)

If your processor outputs a file type not already supported, add it to `_MEDIA_TYPES` in `services/processor/app/routers/jobs.py`.

## Tips

- Always add `from __future__ import annotations` for Python 3.9 compatibility.
- Use `asyncio.create_subprocess_exec()` for external tools (like FFmpeg).
- Use `loop.run_in_executor()` for CPU-heavy sync code (like image processing with Pillow).
- Report progress granularly — users see it in real time via SSE.
- Put intermediate files in `output_dir` — they are cleaned up automatically.
- The processor will automatically appear in the card grid, the API, and accept files with the specified extensions.
