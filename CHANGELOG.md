# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2] - 2026-02-18

### Fixed

- Release pipeline broken by incorrect Tauri permission name (`process:allow-relaunch` → `process:allow-restart`)

## [0.7.1] - 2026-02-18

### Fixed

- OAuth sign-in (ChatGPT) button stayed in loading state indefinitely in the distributed desktop app — the OAuth API calls used a hardcoded port `:8787` instead of the dynamic port assigned to the sidecar at runtime
- Auto-updater "Restarting..." state never actually restarted the app — `downloadAndInstall()` does not relaunch automatically; now calls `relaunch()` explicitly after install

## [0.7.0] - 2026-02-17

### Added

- OpenAI OAuth sign-in: ChatGPT Plus/Pro subscribers can now sign in with their OpenAI account instead of an API key (OAuth PKCE flow)
- Automatic token refresh for OAuth sessions before expiry
- User-friendly error messages in chat for API failures (429 rate limit, invalid key, model not found, provider down, network errors)
- AI chat banner on home page promoting the chat feature
- MCP info hint on home page explaining automatic agent connectivity (Claude Code, Cursor, etc.)

### Improved

- AI assistant now follows processor options precisely (format, resolution, etc.) without asking unnecessary questions
- Attached files persist across conversation turns — follow-up messages can reference files from earlier in the chat
- Refined AI system prompt with stricter behavioral rules for more reliable single-pass processing

### Fixed

- Provider card: API key placeholder no longer assumes "sk-..." prefix
- Provider card: show/hide password toggle vertically centered in input
- Spanish i18n: fixed missing accents and opening punctuation marks (¿Qué, ¡Hola, imágenes, Configuración)
- Stop streaming button restyled to match app palette (was red with black square)
- Removed "Claude Pro / Max — Coming Soon" placeholder from settings

## [0.6.0] - 2026-02-16

### Added

- AI Chat assistant: in-app chat interface where users can describe what they want and the AI executes it using Vimix processors
- Multi-provider support: Ollama (local/free), Google Gemini (free API key), Anthropic, OpenAI, and OpenRouter
- Tool execution: AI can list processors, process files, and run batch operations directly from the chat
- Real-time progress tracking for AI-initiated processing jobs
- Provider settings dialog with connection testing, model selection, and API key management
- Automatic Ollama detection on localhost
- Chat history persistence in localStorage
- Full i18n support (English and Spanish) for all chat and settings UI
- Nav toggle in header to switch between Tools and Chat views

## [0.5.0] - 2026-02-15

### Added

- MCP server (`services/mcp/`) — exposes Vimix processing tools to LLM agents via the Model Context Protocol (Streamable HTTP on port 8788). Tools: `list_processors`, `process_file`, `batch_process`
- Auto-registration: on app startup, Vimix automatically registers its MCP server in all detected AI agents (Claude Code, Cursor, Windsurf, Codex, Gemini CLI, Kiro, OpenCode, VS Code, Copilot CLI, Antigravity)

## [0.4.0] - 2026-02-15

### Added

- Favorite processors: mark any tool with a heart icon to save it as a favorite, persisted in localStorage
- Favorites section on the home screen: favorited tools appear above categories for quick access, skipping category navigation
- Visual separator and "Categories" subtitle to distinguish favorites from category grid

## [0.3.0] - 2026-02-15

### Added

- Category navigation: processors are now grouped into Video, Image, PDF, and Audio categories with a two-step selection flow
- Download toast notifications: success/error feedback when downloading processed files (single and batch)
- File reordering for multi-file processors (e.g. PDF Merge): drag-and-drop and arrow buttons to choose merge order before processing
- Back-to-processor navigation: the back button on job/batch result pages now returns to the processor's tool view instead of the home screen

### Changed

- Home page flow updated from 2 states to 3 (categories → processors → tool view)
- Batch "Download All" now uses blob-based downloads (Tauri-safe) instead of direct link navigation

### Dependencies

- Added `svelte-sonner` for toast notifications

## [0.2.4] - 2026-02-13

### Fixed

- Add macOS entitlements to allow PyInstaller sidecar to load Python framework with hardened runtime

## [0.2.3] - 2026-02-13

### Fixed

- Import Apple certificate into keychain before signing resource binaries in CI

## [0.2.2] - 2026-02-13

### Fixed

- Sign bundled resource binaries (ffmpeg, ffprobe, img2webp) for macOS notarization

## [0.2.1] - 2026-02-13

### Added

- Auto-updater: the desktop app now checks for new versions on startup and prompts the user to update in-place
- macOS code signing and notarization support in release workflow

### Changed

- Disabled Linux build in CI (takes 1h+, re-enable later)

## [0.2.0] - 2026-02-13

### Added

- Windows x64 desktop build support
- Tauri updater plugin with signed artifacts and `latest.json` for GitHub Releases

### Fixed

- Filter `uvloop` from Python requirements on Windows to prevent installation failure

### Changed

- Removed macOS Intel build (runner unavailable)
- Slider component updated for bits-ui v2.15+ compatibility
- Set "Quality" as default background removal model

## [0.1.0] - 2025-06-01

### Added

- SvelteKit 2 frontend with Svelte 5, TailwindCSS v4, and shadcn-svelte
- FastAPI backend with extensible processor system
- Tauri 2 desktop app shell (macOS)
- Batch job processing with multi-file upload
- Real-time SSE progress tracking
- i18n support (English and Spanish)
- Dark/light theme with mode toggle
- 13 processors:
  - **Video:** compress, convert, trim, background removal, to GIF, thumbnail extraction
  - **Image:** compress, convert, background removal, watermark
  - **Audio:** extract from video
  - **PDF:** to image conversion
- PyInstaller sidecar binary for desktop distribution
- Bundled static binaries (ffmpeg, ffprobe, img2webp) for macOS
- Download script for desktop binary dependencies
- Documentation: architecture, API reference, adding processors, desktop app guide
