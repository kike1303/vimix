from app.processors.base import BaseProcessor
from app.processors.video_bg_remove import VideoBgRemoveProcessor
from app.processors.image_bg_remove import ImageBgRemoveProcessor
from app.processors.image_convert import ImageConvertProcessor
from app.processors.video_convert import VideoConvertProcessor
from app.processors.video_to_gif import VideoToGifProcessor
from app.processors.image_compress import ImageCompressProcessor
from app.processors.video_trim import VideoTrimProcessor

_PROCESSORS: dict[str, BaseProcessor] = {}


def _register(proc: BaseProcessor) -> None:
    _PROCESSORS[proc.id] = proc


# Register all processors here.
_register(VideoBgRemoveProcessor())
_register(ImageBgRemoveProcessor())
_register(ImageConvertProcessor())
_register(VideoConvertProcessor())
_register(VideoToGifProcessor())
_register(ImageCompressProcessor())
_register(VideoTrimProcessor())


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
