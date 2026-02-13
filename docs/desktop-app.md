# Desktop App (Tauri 2)

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
├── Sidecar binary (PyInstaller bundle)
│   ├── FastAPI server (starts on a random local port)
│   ├── rembg + ONNX model (u2netp ~4.4 MB)
│   └── All Python dependencies
└── Resources
    ├── ffmpeg (static, ~59 MB)
    ├── ffprobe (static, ~59 MB)
    └── img2webp (static, ~2.5 MB)
```

On app launch:
1. Tauri finds a free port and starts the sidecar (Python bundle) on it
2. Tauri sets `FFMPEG_BIN`, `FFPROBE_BIN`, and `IMG2WEBP_BIN` env vars pointing to bundled resources
3. Tauri sets `window.__VIMIX_API_PORT__` so the frontend knows where the API lives
4. Tauri opens the webview pointing to the SvelteKit app
5. The frontend talks to the local sidecar API (same as current architecture)
6. On app close, Tauri kills the sidecar process

## Current status

- [x] Tauri CLI and dependencies installed in `apps/web/`
- [x] `src-tauri/` configured: window, capabilities, plugins
- [x] `--port` CLI argument added to `main.py` for dynamic port binding
- [x] `api.ts` detects Tauri mode and uses the dynamic port
- [x] SvelteKit switched to static adapter with SPA fallback
- [x] `+layout.ts` disables SSR (required for Tauri)
- [x] Placeholder app icons generated
- [x] Rust code compiles (`cargo check` passes)
- [x] PyInstaller spec created (`vimix-processor.spec`)
- [x] Python sidecar builds as single binary (~147 MB)
- [x] Sidecar wired up: Tauri spawns it with `--port {random}`
- [x] `binary_paths.py` resolves ffmpeg/ffprobe/img2webp from env vars, `_MEIPASS`, or system PATH
- [x] Static ARM64 macOS builds of ffmpeg, ffprobe, img2webp downloaded and placed in `src-tauri/resources/`
- [x] Tauri bundles resources via `bundle.resources` in `tauri.conf.json`
- [x] Rust code sets env vars before spawning sidecar so processors find bundled binaries
- [x] Download script: `scripts/download-desktop-binaries.sh`

## Building the desktop app

### Prerequisites

- Rust toolchain (install via [rustup](https://rustup.rs/))
- Node.js + pnpm
- Python 3.9+ with venv (for building the sidecar)

### Step 1: Build the Python sidecar

```bash
cd services/processor
source venv/bin/activate
pip install pyinstaller
pyinstaller vimix-processor.spec
```

This creates `dist/Vimix-processor` — a single binary (~147 MB) containing the Python interpreter, FastAPI, rembg, ONNX model, and all dependencies.

Copy it to the Tauri binaries directory with the platform suffix:

```bash
# macOS ARM64
cp dist/Vimix-processor apps/web/src-tauri/binaries/Vimix-processor-aarch64-apple-darwin

# macOS Intel
cp dist/Vimix-processor apps/web/src-tauri/binaries/Vimix-processor-x86_64-apple-darwin
```

### Step 2: Download static binaries

```bash
./scripts/download-desktop-binaries.sh
```

This downloads platform-appropriate static builds of ffmpeg, ffprobe, and img2webp into `apps/web/src-tauri/resources/`.

### Step 3: Build the Tauri app

```bash
# Development (opens desktop window, hot-reloads frontend)
pnpm tauri:dev

# Build for current platform
pnpm tauri:build
```

Output locations:
- macOS: `src-tauri/target/release/bundle/dmg/`
- Windows: `src-tauri/target/release/bundle/msi/`
- Linux: `src-tauri/target/release/bundle/appimage/`

## Binary path resolution

The `binary_paths.py` module resolves ffmpeg/ffprobe/img2webp in this order:

1. **Environment variable** (`FFMPEG_BIN`, `FFPROBE_BIN`, `IMG2WEBP_BIN`) — set by Tauri Rust code pointing to bundled resources
2. **PyInstaller `_MEIPASS` directory** — for binaries bundled inside the sidecar itself
3. **System PATH** (`shutil.which()`) — fallback for development

## Sidecar naming convention

Tauri requires platform-suffixed sidecar binaries:

```
src-tauri/binaries/Vimix-processor-aarch64-apple-darwin   # macOS ARM
src-tauri/binaries/Vimix-processor-x86_64-apple-darwin    # macOS Intel
src-tauri/binaries/Vimix-processor-x86_64-pc-windows-msvc.exe  # Windows
src-tauri/binaries/Vimix-processor-x86_64-unknown-linux-gnu    # Linux
```

## Web vs Desktop

Both modes share 99% of the code. The only difference:

| Aspect | Web (`pnpm dev`) | Desktop (`pnpm tauri dev`) |
|--------|-------------------|---------------------------|
| API URL | `http://localhost:8787` (fixed) | `http://localhost:{random}` (dynamic) |
| Backend | User starts manually | Tauri launches sidecar automatically |
| ffmpeg | System PATH | Bundled in resources |
| Adapter | Static (SPA) | Static (SPA) |
| Distribution | Deploy to Vercel/any host | `.dmg` / `.msi` / `.AppImage` |

Detection in `api.ts`:
```ts
if (window.__VIMIX_API_PORT__) {
  // Desktop mode — use Tauri-injected port
} else {
  // Web mode — use fixed port or env variable
}
```

## Installer sizes (actual)

| Component | Size |
|-----------|------|
| Tauri shell + frontend | ~10-15 MB |
| Python sidecar (PyInstaller onefile) | ~147 MB |
| ffmpeg static | ~59 MB |
| ffprobe static | ~59 MB |
| img2webp static | ~2.5 MB |
| **Total** | **~280 MB** |

The ONNX model (u2netp, ~4.4 MB) is bundled inside the sidecar. Larger models (u2net ~168 MB, isnet ~170 MB) can be downloaded on first use.

## CI/CD and Releases

Desktop builds are automated via GitHub Actions. Pushing a git tag triggers the full pipeline.

### Release workflow

1. Run `./scripts/bump-version.sh 0.2.0` to update version in all 5 config files
2. Update `CHANGELOG.md` with the new version's changes
3. Commit, tag (`git tag v0.2.0`), and push with tags
4. GitHub Actions builds desktop apps for all platforms in parallel
5. A GitHub Release is created with all artifacts attached

### Platform matrix

| Platform | Runner | Triple | Bundle format |
|----------|--------|--------|---------------|
| macOS ARM64 | `macos-latest` | `aarch64-apple-darwin` | `.dmg` |
| macOS Intel | `macos-13` | `x86_64-apple-darwin` | `.dmg` |
| Windows x64 | `windows-latest` | `x86_64-pc-windows-msvc` | NSIS `.exe` |
| Linux x64 | `ubuntu-22.04` | `x86_64-unknown-linux-gnu` | `.AppImage`, `.deb` |

### CI checks (on PRs)

Every pull request runs three checks automatically:
- **Frontend type-check** — `svelte-check` ensures no TypeScript errors
- **Python syntax** — `py_compile` catches syntax errors without installing deps
- **Version sync** — verifies all 4 version files match

### macOS code signing (optional)

To produce signed/notarized macOS builds, add these repository secrets:

| Secret | Description |
|--------|-------------|
| `APPLE_CERTIFICATE` | Base64-encoded .p12 certificate |
| `APPLE_CERTIFICATE_PASSWORD` | Certificate password |
| `APPLE_SIGNING_IDENTITY` | e.g. "Developer ID Application: Your Name (TEAM_ID)" |
| `APPLE_ID` | Apple ID email |
| `APPLE_PASSWORD` | App-specific password |
| `APPLE_TEAM_ID` | 10-character team ID |

Builds work unsigned without these secrets — users will see a Gatekeeper warning on first launch.

## What still needs to happen

- [ ] Design and set real app icon (`npx @tauri-apps/cli icon path/to/icon.png`)
- [ ] End-to-end test: `pnpm tauri:dev` with sidecar and resource binaries
- [ ] Set up auto-updater with GitHub Releases (`@tauri-apps/plugin-updater`)
- [ ] Optional: download large ONNX models on first use instead of bundling
- [ ] Optional: code-sign the app for macOS notarization
