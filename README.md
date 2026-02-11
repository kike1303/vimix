# Vimix

Local AI-powered media processing toolkit. Upload a video, remove its background, and download an animated WebP — all running on your machine.

## Features

- **Video Background Removal**: Upload an MP4/MOV/WebM, get an animated WebP with transparent background
- **Real-time progress**: SSE-powered live progress updates in the browser
- **Extensible**: Add new processors with a single Python class (see [docs/adding-processors.md](docs/adding-processors.md))
- **Dark/Light mode**: Automatic theme detection with manual toggle
- **Multilanguage**: English and Spanish (easily extensible)

## Prerequisites

- **Node.js** >= 20
- **pnpm** >= 9
- **Python** >= 3.10
- **FFmpeg** (`brew install ffmpeg`)
- **libwebp** / img2webp (`brew install webp`)

## Quick Start

### 1. Install dependencies

```bash
# Node dependencies
pnpm install

# Python virtual environment
cd services/processor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 2. Run both services

```bash
# Terminal 1 – API server
cd services/processor
source venv/bin/activate
uvicorn app.main:app --reload --port 8787

# Terminal 2 – Frontend
pnpm dev
```

Or run both at once:

```bash
pnpm dev:all
```

Then open **http://localhost:5173**.

## Project Structure

```
vimix/
├── apps/web/                  # SvelteKit 5 + TailwindCSS v4 + shadcn-svelte
│   └── src/
│       ├── routes/            # Pages
│       ├── lib/components/    # App components + shadcn UI
│       └── lib/i18n/          # Translations (en, es)
├── services/processor/        # Python FastAPI
│   └── app/
│       ├── routers/           # HTTP endpoints
│       ├── processors/        # Processing pipelines
│       └── services/          # Job manager, file manager
├── docs/                      # Documentation
│   ├── architecture.md        # System architecture
│   ├── api.md                 # API reference
│   ├── adding-processors.md   # Guide to extend the tool
│   ├── deployment.md          # Production deployment plan
│   └── desktop-app.md         # Tauri desktop app plan
└── pnpm-workspace.yaml        # Monorepo config
```

## Documentation

- [Architecture](docs/architecture.md) – How the system works
- [API Reference](docs/api.md) – All endpoints
- [Adding Processors](docs/adding-processors.md) – How to add new features
- [Deployment](docs/deployment.md) – Plan for production web deployment
- [Desktop App](docs/desktop-app.md) – Plan for Tauri desktop app

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 2, Svelte 5 (runes), TailwindCSS v4, shadcn-svelte |
| Backend | Python, FastAPI |
| AI/Processing | rembg (U2Net), FFmpeg, img2webp |
| i18n | svelte-i18n (EN, ES) |
| Theming | mode-watcher (dark/light) |
| Monorepo | pnpm workspaces |
