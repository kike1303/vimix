# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
