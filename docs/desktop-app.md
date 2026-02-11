# Desktop App Plan (Tauri 2)

Package Vimix as a native desktop application using Tauri 2. The user installs it and everything runs locally on their machine — no server needed.

## Why Tauri

- Uses the system's native webview (not bundled Chromium like Electron)
- Tauri shell is ~10MB vs ~200MB for Electron
- Supports sidecar binaries — can launch the Python backend as a child process
- First-class SvelteKit support
- Cross-platform: macOS, Windows, Linux

## Architecture

```
Vimix.app
├── Tauri shell (Rust)
│   └── Manages window, lifecycle, sidecar
├── Frontend (existing SvelteKit, loaded in webview)
└── Sidecar binary (PyInstaller bundle)
    ├── FastAPI server (starts on a random local port)
    ├── rembg + ONNX model
    └── FFmpeg + img2webp (bundled)
```

On app launch:
1. Tauri starts the sidecar (Python bundle) on a random available port
2. Tauri opens the webview pointing to the SvelteKit app
3. The frontend talks to the local sidecar API (same as current architecture)
4. On app close, Tauri kills the sidecar process

## What can be reused as-is

- `apps/web/` — the entire SvelteKit frontend (no changes)
- `services/processor/app/` — the entire FastAPI backend (no changes)
- All processors, job manager, file manager — unchanged

## What needs to be built

### 1. Add Tauri to the SvelteKit app

```bash
cd apps/web
pnpm add -D @tauri-apps/cli @tauri-apps/api
pnpm tauri init
```

Configure `src-tauri/tauri.conf.json`:
- Window title, size, icon
- Sidecar configuration pointing to the Python bundle
- Allowed API permissions

### 2. Bundle the Python backend with PyInstaller

```bash
cd services/processor
pip install pyinstaller
pyinstaller --onedir --name Vimix-processor app/main.py
```

This creates a standalone directory with the Python interpreter, all dependencies, and the ONNX models baked in. No Python installation required on the user's machine.

Key PyInstaller considerations:
- Include ONNX model files as data files
- Include FFmpeg and img2webp binaries
- Test on each target OS separately
- Use `--onedir` (not `--onefile`) for faster startup

### 3. Sidecar management in Tauri

In the Tauri Rust code or via the `@tauri-apps/plugin-shell` plugin:
- Find a free port at startup
- Launch the PyInstaller sidecar with `--port {free_port}`
- Pass the port to the frontend via Tauri's IPC or an env variable
- Kill the sidecar on app exit

The FastAPI `main.py` needs a minor change to accept `--port` as a CLI argument:

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port)
```

### 4. Bundle FFmpeg and img2webp

These need to be included per-platform:
- **macOS**: download static builds, include in the app bundle
- **Windows**: download static `.exe` builds
- **Linux**: download static builds or document as a prerequisite

The processor code should resolve binary paths relative to the app bundle instead of relying on system PATH.

### 5. Auto-updates

Tauri has built-in updater support (`@tauri-apps/plugin-updater`):
- Host update manifests on GitHub Releases
- The app checks for updates on startup
- Users get prompted to update

## Installer sizes (estimated)

| Component | Size |
|-----------|------|
| Tauri shell + frontend | ~10-15 MB |
| Python sidecar (PyInstaller) | ~150-200 MB |
| ONNX model (u2net) | ~170 MB |
| ONNX model (u2netp) | ~5 MB |
| FFmpeg static build | ~80-100 MB |
| img2webp | ~2 MB |
| **Total (with u2netp only)** | **~250-320 MB** |
| **Total (with all models)** | **~450-500 MB** |

Consider downloading larger models on first use instead of bundling them to keep the installer smaller.

## Build commands per platform

```bash
# Development
cd apps/web
pnpm tauri dev

# Build for current platform
pnpm tauri build

# Output locations
# macOS: src-tauri/target/release/bundle/dmg/
# Windows: src-tauri/target/release/bundle/msi/
# Linux: src-tauri/target/release/bundle/appimage/
```

## Implementation checklist

- [ ] Install Tauri CLI and initialize in `apps/web/`
- [ ] Create PyInstaller spec for the Python backend
- [ ] Add `--port` CLI argument to `main.py` for dynamic port binding
- [ ] Configure Tauri sidecar to launch and manage the Python process
- [ ] Bundle FFmpeg and img2webp per platform
- [ ] Update binary path resolution in processors to support bundled binaries
- [ ] Configure app icon, name, and window settings
- [ ] Test on macOS
- [ ] Test on Windows
- [ ] Test on Linux
- [ ] Set up auto-updater with GitHub Releases
- [ ] Optional: download large models on first use instead of bundling
