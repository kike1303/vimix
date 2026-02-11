from __future__ import annotations

import asyncio
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image
from rembg import new_session, remove

from app.processors.base import BaseProcessor, ProgressCallback

# Reuse a single thread pool across jobs so threads (and their ONNX sessions)
# stay warm between requests.
_MAX_WORKERS = max(2, (os.cpu_count() or 4) // 2)
_pool = ThreadPoolExecutor(max_workers=_MAX_WORKERS)


class VideoBgRemoveProcessor(BaseProcessor):
    id = "video-bg-remove"
    label = "Video Background Removal"
    description = "Remove the background from a video and export with transparency."
    accepted_extensions = [".mp4", ".mov", ".webm"]

    @property
    def options_schema(self) -> list[dict]:
        return [
            {
                "id": "fps",
                "label": "Frames per second",
                "type": "number",
                "default": 15,
                "min": 1,
                "max": 60,
                "step": 1,
            },
            {
                "id": "resolution",
                "label": "Output width",
                "type": "select",
                "default": "original",
                "choices": [
                    {"value": "original", "label": "Original"},
                    {"value": "1024", "label": "1024 px"},
                    {"value": "512", "label": "512 px"},
                    {"value": "256", "label": "256 px"},
                    {"value": "128", "label": "128 px"},
                ],
            },
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
                "id": "format",
                "label": "Output format",
                "type": "select",
                "default": "webp",
                "choices": [
                    {"value": "webp", "label": "WebP"},
                    {"value": "gif", "label": "GIF"},
                    {"value": "mov", "label": "MOV (ProRes 4444)"},
                    {"value": "png-zip", "label": "PNG sequence (ZIP)"},
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
        fps: int = int(opts.get("fps", 15))
        resolution: str = str(opts.get("resolution", "original"))
        model_name: str = str(opts.get("model", "u2netp"))
        out_format: str = str(opts.get("format", "webp"))

        frames_dir = output_dir / "frames"
        cut_dir = output_dir / "cut"
        frames_dir.mkdir(exist_ok=True)
        cut_dir.mkdir(exist_ok=True)

        # --- Step 1: Extract + scale frames with FFmpeg ---
        await on_progress(5, "Extracting frames from video...")
        await self._extract_frames(input_path, frames_dir, fps, resolution)

        frames = sorted(frames_dir.glob("*.png"))
        if not frames:
            raise RuntimeError("FFmpeg produced no frames.")

        await on_progress(10, f"Extracted {len(frames)} frames")

        # --- Step 2: Load AI model once ---
        await on_progress(12, f"Loading model ({model_name})...")
        loop = asyncio.get_running_loop()
        session = await loop.run_in_executor(_pool, new_session, model_name)

        # --- Step 3: Remove backgrounds in parallel ---
        total = len(frames)
        completed = 0
        sem = asyncio.Semaphore(_MAX_WORKERS)

        async def process_frame(fp: Path) -> None:
            nonlocal completed
            async with sem:
                await loop.run_in_executor(
                    _pool, _remove_bg_sync, fp, cut_dir / fp.name, session
                )
                completed += 1
                pct = 15 + (completed / total) * 65
                await on_progress(pct, f"Removing background – frame {completed}/{total}")

        await asyncio.gather(*(process_frame(fp) for fp in frames))

        await on_progress(82, "Background removal complete")

        # --- Step 4: Assemble output in chosen format ---
        delay_ms = max(1, 1000 // fps)

        if out_format == "gif":
            output_file = output_dir / "output.gif"
            await on_progress(85, "Creating animated GIF...")
            await self._create_gif(cut_dir, output_file, delay_ms)
        elif out_format == "mov":
            output_file = output_dir / "output.mov"
            await on_progress(85, "Creating MOV (ProRes 4444)...")
            await self._create_mov(cut_dir, output_file, fps)
        elif out_format == "png-zip":
            output_file = output_dir / "output.zip"
            await on_progress(85, "Packing PNG sequence...")
            await loop.run_in_executor(_pool, self._create_png_zip, cut_dir, output_file)
        else:
            output_file = output_dir / "output.webp"
            await on_progress(85, "Creating animated WebP...")
            await self._create_webp(cut_dir, output_file, delay_ms)

        await on_progress(100, "Done!")
        return output_file

    # --- private helpers ---------------------------------------------------

    async def _extract_frames(
        self, video: Path, dest: Path, fps: int, resolution: str
    ) -> None:
        vf = f"fps={fps}"
        if resolution != "original":
            vf += f",scale={resolution}:-2"

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            vf,
            str(dest / "frame_%04d.png"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    async def _create_webp(
        self, frames_dir: Path, output: Path, delay_ms: int
    ) -> None:
        frames = sorted(frames_dir.glob("*.png"))
        args = ["img2webp", "-loop", "0", "-d", str(delay_ms)]
        args += [str(f) for f in frames]
        args += ["-o", str(output)]

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"img2webp failed: {stderr.decode()}")

    async def _create_gif(
        self, frames_dir: Path, output: Path, delay_ms: int
    ) -> None:
        """Assemble an animated GIF from RGBA PNGs using Pillow."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(_pool, _assemble_gif, frames_dir, output, delay_ms)

    async def _create_mov(
        self, frames_dir: Path, output: Path, fps: int
    ) -> None:
        """Assemble a MOV with ProRes 4444 (alpha) via FFmpeg."""
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-c:v", "prores_ks",
            "-profile:v", "4444",
            "-pix_fmt", "yuva444p10le",
            "-y",
            str(output),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg MOV failed: {stderr.decode()}")

    @staticmethod
    def _create_png_zip(frames_dir: Path, output: Path) -> None:
        """Pack all cut PNG frames into a zip file."""
        frames = sorted(frames_dir.glob("*.png"))
        with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as zf:
            for f in frames:
                zf.write(f, f.name)


def _remove_bg_sync(src: Path, dest: Path, session: object) -> None:
    """Standalone function (picklable) for thread pool execution."""
    with Image.open(src) as im:
        im = im.convert("RGBA")
        result = remove(im, session=session)
        if isinstance(result, bytes):
            dest.write_bytes(result)
        else:
            result.save(dest)


def _assemble_gif(frames_dir: Path, output: Path, delay_ms: int) -> None:
    """Assemble RGBA PNGs into an animated GIF with transparency."""
    frames = sorted(frames_dir.glob("*.png"))
    images = []
    for f in frames:
        im = Image.open(f).convert("RGBA")
        images.append(im)

    if not images:
        raise RuntimeError("No frames to assemble into GIF.")

    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=delay_ms,
        loop=0,
        disposal=2,
        transparency=0,
    )
