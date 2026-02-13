# Contributing to Vimix

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

### Prerequisites

- **Node.js** >= 20
- **pnpm** >= 9
- **Python** 3.9+
- **FFmpeg** (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Ubuntu)
- **libwebp** / img2webp (`brew install webp` on macOS, `apt install webp` on Ubuntu)
- **Rust** toolchain — only needed for desktop app work (install via [rustup.rs](https://rustup.rs/))

### Getting Started

```bash
# Clone the repo
git clone https://github.com/your-username/vimix.git
cd vimix

# Install Node dependencies
pnpm install

# Set up Python backend
cd services/processor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..

# Run both services
pnpm dev:all
```

Frontend runs at `http://localhost:5173`, API at `http://localhost:8787`.

### Desktop App Development

If you're working on the Tauri desktop app:

```bash
# 1. Build the Python sidecar (one-time)
cd services/processor && source venv/bin/activate
pip install pyinstaller
pyinstaller vimix-processor.spec
cp dist/Vimix-processor ../apps/web/src-tauri/binaries/Vimix-processor-aarch64-apple-darwin
cd ../..

# 2. Download static binaries (one-time)
./scripts/download-desktop-binaries.sh

# 3. Run the desktop app
pnpm tauri:dev
```

**Note:** The sidecar binary takes 20-30 seconds to start on first launch. The app shows a loading screen while it initializes.

If you only change frontend code, you don't need to rebuild the sidecar. If you change Python code, rebuild with `pyinstaller vimix-processor.spec` and copy the binary again.

## Project Structure

- `apps/web/` — SvelteKit frontend (Svelte 5, TailwindCSS v4, shadcn-svelte)
- `apps/web/src-tauri/` — Tauri desktop shell (Rust)
- `services/processor/` — Python FastAPI backend (processors, job manager)
- `scripts/` — Build and setup scripts
- `docs/` — Architecture, API reference, and guides

See [docs/architecture.md](docs/architecture.md) for the full system overview.

## Making Changes

### Branch Naming

- `feat/short-description` — New features
- `fix/short-description` — Bug fixes
- `docs/short-description` — Documentation only

### Code Conventions

**Frontend (Svelte/TypeScript):**
- Svelte 5 runes only (`$state()`, `$derived()`, `$effect()`, `$props()`)
- Never use legacy `let`/`$:` reactivity or `on:event` syntax
- All UI strings must use i18n — add keys to both `en.json` and `es.json`
- shadcn-svelte components live in `$lib/components/ui/` (auto-generated, don't edit manually)
- All API calls go through `apps/web/src/lib/api.ts`

**Backend (Python):**
- Always add `from __future__ import annotations` at the top of every file
- Python 3.9 compatible syntax (use `from __future__ import annotations` for `X | Y` unions)
- External binary paths (ffmpeg, img2webp) must use `app.services.binary_paths` helpers, never hardcode paths

**Desktop (Rust):**
- The Tauri Rust code lives in `apps/web/src-tauri/src/`
- The sidecar communicates via HTTP — no Tauri IPC needed for processing
- Only `get_api_port` uses Tauri IPC (to tell the frontend which port the sidecar runs on)

### Adding a New Processor

See the dedicated guide: [docs/adding-processors.md](docs/adding-processors.md)

After adding a processor, remember to:
1. Add it to the hidden imports list in `vimix-processor.spec`
2. Update `en.json` and `es.json` with the processor label/description
3. Update `docs/api.md` if there are new endpoints

### Running Checks

```bash
# Type-check the frontend
pnpm --filter web check

# Verify Rust compiles (if working on desktop)
cd apps/web/src-tauri && cargo check

# Make sure both services start without errors
pnpm dev:all
```

## Pull Requests

1. Fork the repo and create your branch from `main`
2. Make your changes following the conventions above
3. Test your changes locally with `pnpm dev:all`
4. If you changed desktop code, also test with `pnpm tauri:dev`
5. Update documentation if you changed behavior or added features
6. Open a PR with a clear title and description

### PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Include screenshots for UI changes
- Update `en.json` and `es.json` for any new UI strings
- Update `docs/` if you added or changed a processor, endpoint, or architecture

## Reporting Bugs

Use the [Bug Report](https://github.com/your-username/vimix/issues/new?template=bug_report.md) issue template. Include:

- Steps to reproduce
- Expected vs actual behavior
- Your OS and browser/app version
- Screenshots if applicable

## Feature Requests

Use the [Feature Request](https://github.com/your-username/vimix/issues/new?template=feature_request.md) issue template. Describe what you'd like and why it would be useful.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
