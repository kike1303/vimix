# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Commands

```bash
# Run frontend + API + MCP server in parallel
pnpm dev:all

# Frontend only (SvelteKit on :5173)
pnpm dev

# API only (FastAPI on :8787, auto-starts MCP server on :8788)
pnpm dev:api

# MCP server only (Streamable HTTP on :8788)
pnpm dev:mcp

# Build frontend
pnpm build

# Type-check frontend
pnpm --filter web check

# Python API — activate venv first
cd services/processor && source venv/bin/activate
uvicorn app.main:app --reload --port 8787

# Install Python deps
cd services/processor && source venv/bin/activate && pip install -r requirements.txt

# System dependency: OpenMP runtime for numba (threadsafe parallel processing)
# macOS:   brew install libomp
# Windows: included with MSVC (no action needed)
# Linux:   sudo apt install libgomp1 (usually pre-installed)

# Add a shadcn-svelte component
cd apps/web && pnpm dlx shadcn-svelte@latest add <component-name>

# Tauri desktop app (requires Rust toolchain)
pnpm tauri:dev    # Dev mode with hot-reload
pnpm tauri:build  # Build .dmg/.msi/.AppImage
```

## Architecture

Monorepo with three services that communicate over HTTP:

- **`apps/web/`** — SvelteKit 2 frontend (Svelte 5, TailwindCSS v4,
  shadcn-svelte, pnpm)
- **`services/processor/`** — Python FastAPI backend (rembg, FFmpeg, img2webp)
- **`services/mcp/`** — MCP server (Streamable HTTP on :8788) that exposes Vimix
  tools to AI agents (Claude Code, Cursor, Codex, etc.). Auto-started by the
  backend, auto-registers in all detected agents.

The browser talks directly to FastAPI at `:8787`. CORS is configured in
`app/main.py`.

### Processing pipeline

1. User uploads file + selects processor + configures options → `POST /jobs`
2. FastAPI saves file, creates a background task, returns job ID
3. Browser opens SSE to `GET /jobs/{id}/progress` for real-time updates
4. Processor runs (extract frames → AI bg removal → encode WebP)
5. Browser downloads result from `GET /jobs/{id}/result`

### Processor system (extensible)

All processors inherit from `BaseProcessor` (`app/processors/base.py`) and are
registered in `app/processors/registry.py`. Each processor declares:

- `id`, `label`, `description`, `accepted_extensions`
- `options_schema` — list of option dicts (`type: "number" | "select"`) that the
  frontend renders dynamically as UI controls
- `process(input_path, output_dir, on_progress, options)` — the actual pipeline

The frontend reads `options_schema` from `GET /processors` and auto-generates
the controls — no frontend changes needed when adding a new processor.

### Job lifecycle

Managed in-memory by `JobManager` (`app/services/job_manager.py`). Jobs go
through: `pending → processing → completed | failed`. Progress updates are
broadcast to SSE listeners via `asyncio.Queue` per job.

### i18n

Uses `svelte-i18n`. Locale files are in `apps/web/src/lib/i18n/` (en.json,
es.json). Initialized in `$lib/i18n/index.ts`, imported in root layout. All UI
strings use `$_("key")`.

### Theming

Uses shadcn-svelte CSS variables (oklch) defined in `app.css` for `:root`
(light) and `.dark` (dark). Mode toggle via `mode-watcher`. All colors use
semantic tokens: `--primary`, `--background`, `--muted`, etc.

## Key Conventions

- **Svelte 5 runes only** — use `$state()`, `$derived()`, `$effect()`,
  `$props()`, `$bindable()`. Never use legacy `let`/`$:` reactivity or
  `on:event` syntax.
- **shadcn-svelte components** — UI components live in `$lib/components/ui/`
  (auto-generated, don't edit). App components in `$lib/components/`.
- **Python 3.9 compat** — always add `from __future__ import annotations` at top
  of Python files (needed for `X | Y` union syntax).
- All API calls from the frontend are centralized in `apps/web/src/lib/api.ts`.
- All UI strings must be translated — add keys to both `en.json` and `es.json`.
- **Always update docs** — when adding a new processor or making relevant
  changes to an existing one, update the documentation in `docs/`
  (architecture.md, api.md, adding-processors.md as needed).
- Temp files go in `services/processor/uploads/` and `services/processor/jobs/`
  (both gitignored).

## Distribution & Dependencies

This is an **open-source project** distributed as a desktop app via Tauri. End
users install and run the app without any development tooling — everything must
be bundled and work out of the box.

When adding **any** new dependency or feature, always check and update all of
these:

1. **`services/processor/requirements.txt`** — pin the new Python package.
2. **`services/processor/vimix-processor.spec`** (PyInstaller) — add
   `hiddenimports` for any modules PyInstaller can't auto-detect, `datas` for
   non-Python files, and `binaries` for native libraries (`.dylib`, `.dll`,
   `.so`).
3. **`.github/workflows/release.yml`** (CI) — add system-level install steps if
   the dependency needs OS packages (e.g. `brew install`, `apt install`). Check
   that it works on all platforms: macOS ARM64, Windows x64, and Linux x64.
4. **`scripts/build-sidecar.sh`** — add any pre-build checks or installs needed
   for local sidecar builds.
5. **`services/mcp/requirements.txt`** — if the dependency is for the MCP server
   (separate venv, Python 3.12).

Think of it this way: if it works in `venv` during development but isn't mapped
for PyInstaller and CI, **it will break for every user who downloads the app**.
