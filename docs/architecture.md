# Architecture

## Overview

Vimix is a monorepo with two main components:

```
vimix/
├── apps/web/              ← SvelteKit 5 frontend (UI)
├── services/processor/    ← Python FastAPI backend (processing)
├── services/mcp/          ← MCP server (AI agent integration)
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
│              │                       │  │  ├ vid-comp  │  │
│              │                       │  │  ├ img-wm    │  │
│              │                       │  │  ├ pdf-img   │  │
│              │                       │  │  ├ vid-thumb │  │
│              │                       │  │  ├ pdf-merge │  │
│              │                       │  │  ├ pdf-split │  │
│              │                       │  │  ├ pdf-comp  │  │
│              │                       │  │  ├ pdf-rot   │  │
│              │                       │  │  ├ pdf-prot  │  │
│              │                       │  │  ├ pdf-unlk  │  │
│              │                       │  │  ├ pdf-pgnum │  │
│              │                       │  │  ├ pdf-wm    │  │
│              │                       │  │  ├ pdf-text  │  │
│              │                       │  │  ├ img-pdf   │  │
│              │                       │  │  ├ aud-conv  │  │
│              │                       │  │  └ aud-trim  │  │
└─────────────┘                       │  └─────────────┘  │
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
- **Processing**: rembg (AI bg removal), FFmpeg, Pillow, img2webp, PyMuPDF
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
| `image-watermark` | Add text watermark to image | Pillow (ImageDraw + alpha composite) |
| `pdf-to-image` | Convert PDF pages to images | PyMuPDF + Pillow |
| `video-thumbnail` | Extract a frame from video as image | FFmpeg |
| `pdf-merge` | Merge multiple PDFs into one (multi-file) | PyMuPDF |
| `pdf-split` | Split PDF into pages or extract ranges | PyMuPDF |
| `pdf-compress` | Compress PDF file size | PyMuPDF + Pillow |
| `pdf-rotate` | Rotate PDF pages | PyMuPDF |
| `pdf-protect` | Add password protection to PDF | PyMuPDF (AES-256) |
| `pdf-unlock` | Remove password from PDF | PyMuPDF |
| `pdf-page-numbers` | Add page numbers to PDF | PyMuPDF |
| `pdf-watermark` | Add text watermark to PDF pages | PyMuPDF |
| `pdf-extract-text` | Extract text from PDF as TXT/JSON | PyMuPDF |
| `image-to-pdf` | Convert images to PDF (multi-file) | PyMuPDF + Pillow |
| `audio-convert` | Convert audio format/bitrate/sample rate | FFmpeg |
| `audio-trim` | Cut a segment from audio | FFmpeg |

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
| `app/processors/image_watermark.py` | Image watermark |
| `app/processors/pdf_to_image.py` | PDF to image conversion |
| `app/processors/video_thumbnail.py` | Video thumbnail extraction |
| `app/processors/pdf_merge.py` | PDF merge (multi-file) |
| `app/processors/pdf_split.py` | PDF split/extract pages |
| `app/processors/pdf_compress.py` | PDF compression |
| `app/processors/pdf_rotate.py` | PDF page rotation |
| `app/processors/pdf_protect.py` | PDF password protection |
| `app/processors/pdf_unlock.py` | PDF password removal |
| `app/processors/pdf_page_numbers.py` | PDF page numbering |
| `app/processors/pdf_watermark.py` | PDF text watermark |
| `app/processors/pdf_extract_text.py` | PDF text extraction |
| `app/processors/image_to_pdf.py` | Image to PDF (multi-file) |
| `app/processors/audio_convert.py` | Audio format conversion |
| `app/processors/audio_trim.py` | Audio trimming |
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

## MCP Server – `services/mcp/`

The MCP (Model Context Protocol) server allows AI agents to use Vimix tools directly from a conversation. It runs as a Streamable HTTP server on port 8788 and acts as an HTTP client to the FastAPI backend.

### How it works

```
┌──────────────┐     MCP (HTTP)      ┌──────────────┐     HTTP      ┌──────────────┐
│  AI Agent    │ ◄──────────────────► │  MCP Server  │ ────────────► │  FastAPI     │
│  (Claude,    │   list_processors    │  :8788       │  POST /jobs   │  :8787       │
│   Cursor,    │   process_file       │              │  GET /jobs/   │              │
│   Codex...)  │   batch_process      │              │  GET /result  │              │
└──────────────┘                      └──────────────┘               └──────────────┘
```

### Tools exposed

| Tool | Description |
|------|-------------|
| `list_processors` | Discover all available processors with their options |
| `process_file` | Process a single file (upload → poll → download result) |
| `batch_process` | Process multiple files in one batch operation |

### Auto-registration

On startup, the MCP server automatically registers itself in all detected AI agent configurations:
- Claude Code (`~/.claude.json`)
- Cursor (`~/.cursor/mcp.json`)
- Windsurf (`~/.codeium/windsurf/mcp_config.json`)
- OpenCode (`~/.config/opencode/opencode.json`)
- Gemini CLI (`~/.gemini/settings.json`)
- Kiro (`~/.kiro/settings/mcp.json`)
- Copilot CLI (`~/.copilot/mcp-config.json`)
- Antigravity (`~/.gemini/antigravity/mcp_config.json`)
- VS Code (platform-specific path)
- Codex CLI (`~/.codex/config.toml`)

New agents can be added by appending an `AgentProvider` entry to the `PROVIDERS` list in `register.py`.

### Privacy

All processing happens 100% locally. The MCP server reads files from disk, sends them to the local backend, and saves results back to disk. The AI agent only sees text metadata (file paths, sizes, processor names) — never the file contents.

### Key files

| File | Purpose |
|------|---------|
| `server.py` | MCP server with 3 tools (Streamable HTTP transport) |
| `register.py` | Auto-registration in AI agent configs |
| `requirements.txt` | Python dependencies (mcp, httpx) |

## AI Chat – `apps/web/src/lib/ai/`

The in-app AI chat lets users describe what they want in natural language, and the AI executes it using Vimix processors. LLM calls run **client-side** (browser → LLM API directly) since this is a desktop app with `adapter-static`.

### Architecture

```
┌──────────────┐     LLM API      ┌──────────────┐
│  Browser     │ ────────────────► │  LLM Provider│
│  (AI SDK)    │ ◄──────────────── │  (streaming)  │
│              │                    └──────────────┘
│  streamText()│     HTTP
│  + tools     │ ────────────────► ┌──────────────┐
│              │ ◄──────────────── │  FastAPI      │
│              │   POST /jobs      │  :8787        │
└──────────────┘   GET /progress   └──────────────┘
```

### Supported providers

| Provider | Type | SDK |
|----------|------|-----|
| Ollama | Local (free) | `@ai-sdk/openai` (compat mode) |
| Google Gemini | Free API key | `@ai-sdk/google` |
| Anthropic | API key | `@ai-sdk/anthropic` |
| OpenAI | API key | `@ai-sdk/openai` |
| OpenRouter | API key | `@ai-sdk/openai` (custom baseURL) |

### Key files

| File | Purpose |
|------|---------|
| `src/lib/ai/types.ts` | TypeScript types for chat, providers, tool calls |
| `src/lib/ai/client.ts` | Provider factory: config → AI SDK model instance |
| `src/lib/ai/tools.ts` | Tool definitions (list_processors, process_file, batch_process) |
| `src/lib/stores/chat.svelte.ts` | Chat state: messages, streaming, tool execution loop |
| `src/lib/stores/ai-providers.svelte.ts` | Provider config: API keys, models, Ollama detection |
| `src/lib/components/chat/ChatView.svelte` | Main chat layout |
| `src/lib/components/settings/ProviderSettings.svelte` | Provider configuration dialog |
