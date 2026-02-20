# Vimix

**Vimix is a free desktop app that lets you process videos, images, PDFs, and audio files directly on your computer — no internet connection needed, no files uploaded anywhere.**

You drop in a file, pick what you want to do (remove background, compress, convert format, trim, extract audio…), and Vimix handles everything locally using AI and open-source tools. There's also a built-in chat where you can just describe what you need in plain language and the AI figures out the rest.

Think of it as having Photoshop's background removal, a video editor, a PDF tool, and an AI assistant — all in one lightweight app, running entirely offline.

<p align="center">
  <img src="screenshot_1.png" alt="Vimix - Tool selection" width="700" />
</p>

<p align="center">
  <img src="screenshot_2.png" alt="Vimix - Processor options" width="700" />
</p>

<p align="center">
  <img src="screenshot_3.png" alt="Vimix - AI Chat" width="700" />
</p>

## Download

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon) | [Vimix_aarch64.dmg](https://github.com/kike1303/vimix/releases/latest/download/Vimix_aarch64.dmg) |
| Windows (x64) | [Vimix_x64-setup.exe](https://github.com/kike1303/vimix/releases/latest/download/Vimix_x64-setup.exe) |

Or browse all releases on the [Releases page](https://github.com/kike1303/vimix/releases).

> **macOS:** open the `.dmg`, drag Vimix to Applications, and launch it. On first open, right-click → Open if macOS warns about an unidentified developer.

## Features

### Processing Tools

- **Video Background Removal**: Upload an MP4/MOV/WebM, get an animated WebP with transparent background
- **Image Background Removal**: Remove backgrounds from images (PNG, JPG, WebP)
- **Format Conversion**: Convert between video/image formats
- **Video Compression**: Reduce file sizes with quality controls
- **Video Trimming**: Cut clips with start/end time
- **Audio Extraction**: Pull audio from video files
- **Video to GIF**: Convert videos to animated GIFs
- **Image Compression**: Optimize image file sizes
- **Image Watermark**: Add text watermarks to images
- **PDF to Image**: Convert PDF pages to images
- **PDF Merge**: Combine multiple PDFs into one
- **PDF Split**: Extract page ranges from a PDF
- **Video Thumbnails**: Extract thumbnail frames from videos
- **Batch Processing**: Process multiple files at once

### AI Chat

Vimix includes a built-in AI chat where you can describe what you want in plain language and the AI does it for you — no need to navigate menus or configure options manually.

Just type something like *"remove the background from this image"* or *"merge these PDFs"*, attach your files, and the AI picks the right processor, runs it, and gives you a download button when it's done.

Supports multiple LLM providers:

| Provider | Type |
|----------|------|
| Ollama | Local and free — auto-detected if running |
| Google Gemini | Free API key |
| Anthropic | API key |
| OpenAI | API key |
| OpenRouter | API key (access to hundreds of models) |

Configure your provider in the chat settings (gear icon). Ollama is detected automatically if it's running on your machine.

### MCP Server

Vimix exposes its processing tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), so AI coding agents like Claude Code, Cursor, Windsurf, Copilot, and others can use Vimix as a tool directly from your editor.

The MCP server starts automatically alongside the API and runs on **port 8788** (Streamable HTTP). On startup, Vimix auto-registers itself in all detected AI agents on your machine.

Available MCP tools:
- `list_processors` — discover all available processors and their options
- `process_file` — process a single file with any processor
- `batch_process` — process multiple files in one operation

To use it manually, add this to your agent's MCP config:

```json
{
  "mcpServers": {
    "vimix": {
      "type": "streamable-http",
      "url": "http://localhost:8788/mcp"
    }
  }
}
```

### General

- **Real-time progress**: SSE-powered live progress updates
- **Dark/Light mode**: Automatic theme detection with manual toggle
- **Multilanguage**: English and Spanish
- **Desktop App**: Native macOS/Windows app via Tauri

## Prerequisites

- **Node.js** >= 20
- **pnpm** >= 9
- **Python** 3.9+
- **FFmpeg** (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Ubuntu)
- **libwebp** / img2webp (`brew install webp` on macOS, `apt install webp` on Ubuntu)

## Quick Start (Web)

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
pnpm dev:all
```

This starts the frontend at **http://localhost:5173** and the API at **http://localhost:8787**.

You can also run them separately:

```bash
# Terminal 1 – API server (requires venv activated)
cd services/processor
source venv/bin/activate
uvicorn app.main:app --reload --port 8787

# Terminal 2 – Frontend
pnpm dev
```

## Desktop App (Tauri)

Vimix can also run as a native desktop app using Tauri 2. The app bundles everything (frontend + Python backend + FFmpeg) so the user doesn't need to install anything.

### Additional prerequisites

- **Rust** toolchain (install via [rustup.rs](https://rustup.rs/))

### Setup

```bash
# 1. Build the Python sidecar (one-time, requires venv activated)
cd services/processor
source venv/bin/activate
pip install pyinstaller
pyinstaller vimix-processor.spec

# 2. Copy the sidecar binary to Tauri's expected location
#    Replace the suffix with your platform:
#      aarch64-apple-darwin     (macOS ARM)
#      x86_64-apple-darwin      (macOS Intel)
#      x86_64-pc-windows-msvc   (Windows, add .exe)
#      x86_64-unknown-linux-gnu (Linux)
cp dist/Vimix-processor apps/web/src-tauri/binaries/Vimix-processor-aarch64-apple-darwin
cd ../..

# 3. Download static FFmpeg/img2webp binaries
./scripts/download-desktop-binaries.sh

# 4. Run the desktop app in dev mode
pnpm tauri:dev
```

### Build for distribution

```bash
pnpm tauri:build
```

Output: `apps/web/src-tauri/target/release/bundle/` (`.dmg` on macOS, `.msi` on Windows, `.AppImage` on Linux).

See [docs/desktop-app.md](docs/desktop-app.md) for full details.

## Troubleshooting

### "Could not connect to the API" in the browser

The Python backend is not running. Make sure you:
1. Activated the virtual environment: `cd services/processor && source venv/bin/activate`
2. Started the API: `uvicorn app.main:app --reload --port 8787`
3. Or use `pnpm dev:all` which starts both services

### Python module not found errors

Make sure you're in the virtual environment and all deps are installed:

```bash
cd services/processor
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg / img2webp not found

Video processors need FFmpeg and img2webp on your system PATH:

```bash
# macOS
brew install ffmpeg webp

# Ubuntu/Debian
sudo apt install ffmpeg webp
```

### Desktop app: loading screen stays forever

The PyInstaller sidecar binary can take 20-30 seconds to start on first launch (it decompresses to a temp directory). If it never loads:

1. Check the sidecar was built: `ls apps/web/src-tauri/binaries/Vimix-processor-*`
2. Check the resources were downloaded: `ls apps/web/src-tauri/resources/`
3. Try running the sidecar manually to see errors: `./apps/web/src-tauri/binaries/Vimix-processor-aarch64-apple-darwin --port 9999`

### Desktop app: PyInstaller build fails with metadata errors

Some packages need explicit metadata bundling. If you see `PackageNotFoundError`, make sure `vimix-processor.spec` includes the package in the `copy_metadata()` list.

### Port already in use

If port 8787 is busy, either kill the process using it or set a custom port:

```bash
uvicorn app.main:app --reload --port 9000
VITE_API_URL=http://localhost:9000 pnpm dev
```

## Project Structure

```
vimix/
├── apps/web/                  # SvelteKit 2 + Svelte 5 + TailwindCSS v4 + shadcn-svelte
│   ├── src/
│   │   ├── routes/            # Pages (tools, chat, jobs)
│   │   ├── lib/ai/            # AI chat: provider factory, tools, types
│   │   ├── lib/components/    # App components + shadcn UI
│   │   └── lib/i18n/          # Translations (en, es)
│   └── src-tauri/             # Tauri desktop shell (Rust)
│       ├── binaries/          # PyInstaller sidecar (gitignored)
│       └── resources/         # Static ffmpeg/img2webp (gitignored)
├── services/processor/        # Python FastAPI (port 8787)
│   └── app/
│       ├── routers/           # HTTP endpoints
│       ├── processors/        # Processing pipelines
│       └── services/          # Job manager, file manager, binary paths
├── services/mcp/              # MCP server (port 8788)
│   ├── server.py              # Streamable HTTP MCP server
│   └── register.py            # Auto-registration in AI agents
├── scripts/                   # Build scripts
│   └── download-desktop-binaries.sh
├── docs/                      # Documentation
└── pnpm-workspace.yaml        # Monorepo config
```

## Documentation

- [Architecture](docs/architecture.md) — How the system works
- [API Reference](docs/api.md) — All endpoints
- [Adding Processors](docs/adding-processors.md) — How to add new tools
- [Desktop App](docs/desktop-app.md) — Tauri desktop build details
- [Deployment](docs/deployment.md) — Production web deployment

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 2, Svelte 5 (runes), TailwindCSS v4, shadcn-svelte |
| Backend | Python 3.9+, FastAPI, Uvicorn |
| AI Chat | Vercel AI SDK, @ai-sdk/openai, @ai-sdk/anthropic, @ai-sdk/google |
| MCP Server | Model Context Protocol (Streamable HTTP) |
| Processing | rembg (U2Net/ONNX), FFmpeg, img2webp |
| Desktop | Tauri 2 (Rust), PyInstaller |
| i18n | svelte-i18n (EN, ES) |
| Theming | mode-watcher (dark/light) |
| Monorepo | pnpm workspaces |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, conventions, and guidelines.

## License

MIT
