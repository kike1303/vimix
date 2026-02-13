#!/usr/bin/env bash
# Download static binaries required for the Tauri desktop build.
#
# Usage:
#   ./scripts/download-desktop-binaries.sh
#
# This script downloads platform-specific static builds of ffmpeg, ffprobe,
# and img2webp into apps/web/src-tauri/resources/.
#
# Supported platforms:
#   - macOS (arm64, x86_64)
#   - Linux (x86_64)
#   - Windows (x86_64, via Git Bash / MSYS2 on GitHub Actions)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESOURCES_DIR="$PROJECT_ROOT/apps/web/src-tauri/resources"

mkdir -p "$RESOURCES_DIR"

OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected platform: $OS $ARCH"

download_macos() {
    local arch="$1"
    local tmpdir
    tmpdir="$(mktemp -d)"

    echo ""
    echo "=== Downloading ffmpeg (macOS $arch) ==="
    curl -L -o "$tmpdir/ffmpeg.zip" \
        "https://ffmpeg.martin-riedl.de/redirect/latest/macos/$arch/snapshot/ffmpeg.zip"
    unzip -o "$tmpdir/ffmpeg.zip" -d "$tmpdir/ffmpeg"
    cp "$tmpdir/ffmpeg/ffmpeg" "$RESOURCES_DIR/ffmpeg"

    echo ""
    echo "=== Downloading ffprobe (macOS $arch) ==="
    curl -L -o "$tmpdir/ffprobe.zip" \
        "https://ffmpeg.martin-riedl.de/redirect/latest/macos/$arch/snapshot/ffprobe.zip"
    unzip -o "$tmpdir/ffprobe.zip" -d "$tmpdir/ffprobe"
    cp "$tmpdir/ffprobe/ffprobe" "$RESOURCES_DIR/ffprobe"

    echo ""
    echo "=== Downloading img2webp (macOS $arch) ==="
    local webp_arch
    if [ "$arch" = "arm64" ]; then
        webp_arch="mac-arm64"
    else
        webp_arch="mac-x86-64"
    fi
    curl -L -o "$tmpdir/libwebp.tar.gz" \
        "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-${webp_arch}.tar.gz"
    tar xzf "$tmpdir/libwebp.tar.gz" -C "$tmpdir"
    cp "$tmpdir/libwebp-1.6.0-${webp_arch}/bin/img2webp" "$RESOURCES_DIR/img2webp"

    chmod +x "$RESOURCES_DIR/ffmpeg" "$RESOURCES_DIR/ffprobe" "$RESOURCES_DIR/img2webp"

    rm -rf "$tmpdir"

    echo ""
    echo "=== Done ==="
    ls -lh "$RESOURCES_DIR/"
}

download_linux() {
    local tmpdir
    tmpdir="$(mktemp -d)"

    echo ""
    echo "=== Downloading ffmpeg + ffprobe (Linux x86_64) ==="
    curl -L -o "$tmpdir/ffmpeg.tar.xz" \
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    tar xJf "$tmpdir/ffmpeg.tar.xz" -C "$tmpdir"
    cp "$tmpdir/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg" "$RESOURCES_DIR/ffmpeg"
    cp "$tmpdir/ffmpeg-master-latest-linux64-gpl/bin/ffprobe" "$RESOURCES_DIR/ffprobe"

    echo ""
    echo "=== Downloading img2webp (Linux x86_64) ==="
    curl -L -o "$tmpdir/libwebp.tar.gz" \
        "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-linux-x86-64.tar.gz"
    tar xzf "$tmpdir/libwebp.tar.gz" -C "$tmpdir"
    cp "$tmpdir/libwebp-1.6.0-linux-x86-64/bin/img2webp" "$RESOURCES_DIR/img2webp"

    chmod +x "$RESOURCES_DIR/ffmpeg" "$RESOURCES_DIR/ffprobe" "$RESOURCES_DIR/img2webp"

    rm -rf "$tmpdir"

    echo ""
    echo "=== Done ==="
    ls -lh "$RESOURCES_DIR/"
}

download_windows() {
    local tmpdir
    tmpdir="$(mktemp -d)"

    echo ""
    echo "=== Downloading ffmpeg + ffprobe (Windows x86_64) ==="
    curl -L -o "$tmpdir/ffmpeg.zip" \
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    unzip -o "$tmpdir/ffmpeg.zip" -d "$tmpdir"
    cp "$tmpdir/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe" "$RESOURCES_DIR/ffmpeg.exe"
    cp "$tmpdir/ffmpeg-master-latest-win64-gpl/bin/ffprobe.exe" "$RESOURCES_DIR/ffprobe.exe"

    echo ""
    echo "=== Downloading img2webp (Windows x86_64) ==="
    curl -L -o "$tmpdir/libwebp.zip" \
        "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-windows-x64.zip"
    unzip -o "$tmpdir/libwebp.zip" -d "$tmpdir"
    cp "$tmpdir/libwebp-1.6.0-windows-x64/bin/img2webp.exe" "$RESOURCES_DIR/img2webp.exe"

    rm -rf "$tmpdir"

    echo ""
    echo "=== Done ==="
    ls -lh "$RESOURCES_DIR/"
}

case "$OS" in
    Darwin)
        case "$ARCH" in
            arm64)  download_macos "arm64" ;;
            x86_64) download_macos "x86-64" ;;
            *)      echo "Unsupported macOS architecture: $ARCH"; exit 1 ;;
        esac
        ;;
    Linux)
        case "$ARCH" in
            x86_64) download_linux ;;
            *)      echo "Unsupported Linux architecture: $ARCH"; exit 1 ;;
        esac
        ;;
    MINGW*|MSYS*|CYGWIN*)
        download_windows
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac
