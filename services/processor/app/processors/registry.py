from app.processors.base import BaseProcessor
from app.processors.video_bg_remove import VideoBgRemoveProcessor
from app.processors.image_bg_remove import ImageBgRemoveProcessor
from app.processors.image_convert import ImageConvertProcessor
from app.processors.video_convert import VideoConvertProcessor
from app.processors.video_to_gif import VideoToGifProcessor
from app.processors.image_compress import ImageCompressProcessor
from app.processors.video_trim import VideoTrimProcessor
from app.processors.audio_extract import AudioExtractProcessor
from app.processors.video_compress import VideoCompressProcessor
from app.processors.image_watermark import ImageWatermarkProcessor
from app.processors.pdf_to_image import PdfToImageProcessor
from app.processors.video_thumbnail import VideoThumbnailProcessor
from app.processors.pdf_merge import PdfMergeProcessor
from app.processors.pdf_split import PdfSplitProcessor
from app.processors.pdf_compress import PdfCompressProcessor
from app.processors.pdf_rotate import PdfRotateProcessor
from app.processors.pdf_protect import PdfProtectProcessor
from app.processors.pdf_unlock import PdfUnlockProcessor
from app.processors.pdf_page_numbers import PdfPageNumbersProcessor
from app.processors.pdf_watermark import PdfWatermarkProcessor
from app.processors.pdf_extract_text import PdfExtractTextProcessor
from app.processors.image_to_pdf import ImageToPdfProcessor
from app.processors.audio_convert import AudioConvertProcessor
from app.processors.audio_trim import AudioTrimProcessor

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
_register(AudioExtractProcessor())
_register(VideoCompressProcessor())
_register(ImageWatermarkProcessor())
_register(PdfToImageProcessor())
_register(VideoThumbnailProcessor())
_register(PdfMergeProcessor())
_register(PdfSplitProcessor())
_register(PdfCompressProcessor())
_register(PdfRotateProcessor())
_register(PdfProtectProcessor())
_register(PdfUnlockProcessor())
_register(PdfPageNumbersProcessor())
_register(PdfWatermarkProcessor())
_register(PdfExtractTextProcessor())
_register(ImageToPdfProcessor())
_register(AudioConvertProcessor())
_register(AudioTrimProcessor())


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
            "accepts_multiple_files": p.accepts_multiple_files,
        }
        for p in _PROCESSORS.values()
    ]
