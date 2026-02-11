from app.processors.base import BaseProcessor
from app.processors.video_bg_remove import VideoBgRemoveProcessor
from app.processors.image_bg_remove import ImageBgRemoveProcessor
from app.processors.image_convert import ImageConvertProcessor

_PROCESSORS: dict[str, BaseProcessor] = {}


def _register(proc: BaseProcessor) -> None:
    _PROCESSORS[proc.id] = proc


# Register all processors here.
_register(VideoBgRemoveProcessor())
_register(ImageBgRemoveProcessor())
_register(ImageConvertProcessor())


def get_processor(processor_id: str) -> BaseProcessor:
    proc = _PROCESSORS.get(processor_id)
    if proc is None:
        raise KeyError(f"Unknown processor: {processor_id}")
    return proc


def list_processors() -> list[dict]:
    return [
        {
            "id": p.id,
            "label": p.label,
            "description": p.description,
            "accepted_extensions": p.accepted_extensions,
            "options_schema": p.options_schema,
        }
        for p in _PROCESSORS.values()
    ]
