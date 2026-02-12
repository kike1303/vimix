# Architecture

## Overview

Vimix is a monorepo with two main components:

```
vimix/
├── apps/web/              ← SvelteKit 5 frontend (UI)
├── services/processor/    ← Python FastAPI backend (processing)
└── docs/                  ← Documentation
```

The **frontend** handles file upload, job tracking, and result preview/download.
The **backend** runs the actual media processing (AI background removal, video/image conversion, etc.).

## Communication Flow

```
┌─────────────┐       HTTP/SSE        ┌──────────────────┐
│  Browser     │ ◄──────────────────► │  FastAPI          │
│  (SvelteKit) │                       │  :8787            │
│  :5173       │   POST /jobs          │                   │
│              │   GET  /jobs/:id      │  ┌─────────────┐  │
│              │   GET  /jobs/:id/     │  │ Processor    │  │
│              │        progress (SSE) │  │ Registry     │  │
│              │   GET  /jobs/:id/     │  │  ├ video-bg  │  │
│              │        result         │  │  ├ image-bg  │  │
│              │                       │  │  ├ img-conv  │  │
│              │                       │  │  ├ vid-conv  │  │
│              │                       │  │  ├ vid-gif   │  │
│              │                       │  │  ├ img-comp  │  │
│              │                       │  │  ├ vid-trim  │  │
│              │                       │  │  ├ aud-ext   │  │
└─────────────┘                       │  │  └ vid-comp  │  │
                                       │  └─────────────┘  │
                                       └──────────────────┘
```

1. User selects a processor from the card grid on the home page.
2. User configures options and uploads a file.
3. SvelteKit sends a `POST /jobs` with the file + processor ID + options (as JSON).
4. FastAPI creates a background task and returns a job ID.
5. The browser opens an SSE connection to `GET /jobs/:id/progress`.
6. When done, the browser fetches `GET /jobs/:id/result` to download the file.

## Frontend – `apps/web/`

- **Framework**: SvelteKit 2 with Svelte 5 (runes syntax)
- **UI Components**: shadcn-svelte (button, card, slider, toggle-group, tooltip, alert, badge, progress)
- **Styling**: TailwindCSS v4 with oklch color theme
- **i18n**: svelte-i18n (EN, ES)
- **Theming**: mode-watcher (dark/light mode)
- **Icons**: lucide-svelte
- **Package manager**: pnpm

### Key files

| File | Purpose |
|------|---------|
| `src/routes/+page.svelte` | Home – card grid → tool view (two-state flow) |
| `src/routes/jobs/[id]/+page.svelte` | Job progress + result download |
| `src/lib/api.ts` | All API calls + types centralized |
| `src/lib/processor-icons.ts` | Maps processor IDs to lucide icons |
| `src/lib/components/ProcessorGrid.svelte` | Clickable card grid for processor selection |
| `src/lib/components/FileUpload.svelte` | Drag & drop file upload + submit |
| `src/lib/components/ProcessorOptions.svelte` | Dynamic options panel with tooltips |
| `src/lib/components/JobProgress.svelte` | Progress bar component |
| `src/lib/components/JobResult.svelte` | Preview + download (handles all formats) |
| `src/lib/components/ThemeToggle.svelte` | Dark/light mode toggle |
| `src/lib/components/LangToggle.svelte` | EN/ES language toggle |
| `src/app.css` | TailwindCSS config + oklch theme |
| `src/lib/i18n/` | Locale files (en.json, es.json) |

### Dynamic Options System

The frontend auto-renders UI controls from the processor's `options_schema`:
- `type: "number"` → Slider with value display
- `type: "select"` → ToggleGroup buttons
- `showWhen` → Conditional visibility (supports single value or array of values)
- Info tooltips are shown for options that have `options.{id}.description` i18n keys

## Backend – `services/processor/`

- **Framework**: FastAPI
- **Processing**: rembg (AI bg removal), FFmpeg, Pillow, img2webp
- **Pattern**: Processor registry (extensible)
- **Parallelism**: ThreadPoolExecutor for CPU-heavy tasks
- **Python**: 3.9+ (`from __future__ import annotations`)

### Processors

| ID | Description | Key tech |
|----|-------------|----------|
| `video-bg-remove` | Remove video background → WebP/GIF/MOV/ZIP | rembg + FFmpeg + img2webp |
| `image-bg-remove` | Remove image background → PNG/WebP | rembg |
| `image-convert` | Convert image format + resize + quality | Pillow |
| `video-convert` | Convert video codec/format/resolution | FFmpeg |
| `video-to-gif` | Convert video clip to animated GIF | FFmpeg (palette-based two-pass) |
| `image-compress` | Compress image with quality/resize/metadata controls | Pillow |
| `video-trim` | Cut a segment from a video | FFmpeg |
| `audio-extract` | Extract audio track from video | FFmpeg |
| `video-compress` | Reduce video file size | FFmpeg (H.264 slow preset) |

### Key files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app setup, CORS, routers |
| `app/routers/jobs.py` | Job CRUD + SSE progress + result download |
| `app/routers/processors.py` | List available processors |
| `app/processors/base.py` | Abstract `BaseProcessor` class |
| `app/processors/video_bg_remove.py` | Video BG removal (parallel + session reuse) |
| `app/processors/image_bg_remove.py` | Image BG removal |
| `app/processors/image_convert.py` | Image format conversion |
| `app/processors/video_convert.py` | Video format conversion |
| `app/processors/video_to_gif.py` | Video to GIF conversion |
| `app/processors/image_compress.py` | Image compression/optimization |
| `app/processors/video_trim.py` | Video trimming/cutting |
| `app/processors/audio_extract.py` | Audio extraction from video |
| `app/processors/video_compress.py` | Video compression/optimization |
| `app/processors/registry.py` | Processor registration and lookup |
| `app/services/job_manager.py` | In-memory job state + SSE pub/sub |
| `app/services/file_manager.py` | File upload storage |

## Data Flow for a Job

```
uploads/{job_id}/input.mp4          ← Uploaded file
jobs/{job_id}/
  ├── frames/frame_0001.png         ← Extracted frames (video processors)
  ├── cut/frame_0001.png            ← Background removed (bg processors)
  └── output.{ext}                  ← Final output (format depends on options)
```

Both `uploads/` and `jobs/` are inside `services/processor/` and are git-ignored.
