# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
