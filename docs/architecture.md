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
The **backend** runs the actual media processing (AI background removal, video encoding, etc.).

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
│              │        result         │  │  └ (future)  │  │
└─────────────┘                       │  └─────────────┘  │
                                       └──────────────────┘
```

1. User uploads a file and selects a processor.
2. SvelteKit sends a `POST /jobs` with the file + processor ID.
3. FastAPI creates a background task and returns a job ID.
4. The browser opens an SSE connection to `GET /jobs/:id/progress`.
5. When done, the browser fetches `GET /jobs/:id/result` to download the file.

## Frontend – `apps/web/`

- **Framework**: SvelteKit 2 with Svelte 5 (runes syntax)
- **UI Components**: shadcn-svelte
- **Styling**: TailwindCSS v4
- **i18n**: svelte-i18n (EN, ES)
- **Theming**: mode-watcher (dark/light)
- **Package manager**: pnpm

### Key files

| File | Purpose |
|------|---------|
| `src/routes/+page.svelte` | Home page – processor selector + file upload |
| `src/routes/jobs/[id]/+page.svelte` | Job progress + result download |
| `src/lib/api.ts` | All API calls centralized here |
| `src/lib/components/FileUpload.svelte` | Drag & drop file upload component |
| `src/lib/components/JobProgress.svelte` | Progress bar component |
| `src/lib/components/JobResult.svelte` | Preview + download component |
| `src/app.css` | TailwindCSS config + custom theme |

## Backend – `services/processor/`

- **Framework**: FastAPI
- **Processing**: rembg (AI bg removal), FFmpeg, img2webp
- **Pattern**: Processor registry (extensible)

### Key files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app setup, CORS, routers |
| `app/routers/jobs.py` | Job CRUD + SSE progress endpoint |
| `app/routers/processors.py` | List available processors |
| `app/processors/base.py` | Abstract `BaseProcessor` class |
| `app/processors/video_bg_remove.py` | Video → transparent WebP pipeline |
| `app/processors/registry.py` | Processor registration and lookup |
| `app/services/job_manager.py` | In-memory job state + SSE pub/sub |
| `app/services/file_manager.py` | File upload storage + cleanup |

## Data Flow for a Job

```
uploads/{job_id}/video.mp4          ← Uploaded file
jobs/{job_id}/
  ├── frames/frame_0001.png         ← Extracted frames (step 1)
  ├── cut/frame_0001.png            ← Background removed (step 2)
  └── output.webp                   ← Final animated WebP (step 3)
```

Both `uploads/` and `jobs/` are inside `services/processor/` and are git-ignored.
