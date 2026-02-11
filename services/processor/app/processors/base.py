from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Awaitable

ProgressCallback = Callable[[float, str], Awaitable[None]]


class BaseProcessor(ABC):
    """Base class for all media processors."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique processor identifier (e.g. 'video-bg-remove')."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable name shown in the UI."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what the processor does."""

    @property
    @abstractmethod
    def accepted_extensions(self) -> list[str]:
        """File extensions this processor accepts (e.g. ['.mp4', '.mov'])."""

    @property
    def options_schema(self) -> list[dict]:
        """Declare configurable options for this processor.

        Each entry is a dict with:
            id:      unique key sent in the options payload
            label:   human-readable name for the UI
            type:    "number" | "select"
            default: default value

        For type "number":
            min, max, step  (all optional)

        For type "select":
            choices: list of {"value": ..., "label": ...}
        """
        return []

    @abstractmethod
    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        options: dict[str, Any] | None = None,
    ) -> Path:
        """Run the processing pipeline.

        Args:
            input_path: Path to the uploaded file.
            output_dir: Temporary directory for intermediate and output files.
            on_progress: Callback to report progress (0-100) and a message.
            options: User-supplied options matching this processor's options_schema.

        Returns:
            Path to the final output file.
        """
