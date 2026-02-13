#!/usr/bin/env bash
# Download static binaries required for the Tauri desktop build.
#
# Usage:
#   ./scripts/download-desktop-binaries.sh
#
# This script downloads platform-specific static builds of ffmpeg, ffprobe,
# and img2webp into apps/web/src-tauri/resources/. Currently supports macOS
# (arm64 and x86_64).

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

case "$OS" in
    Darwin)
        case "$ARCH" in
            arm64)  download_macos "arm64" ;;
            x86_64) download_macos "x86-64" ;;
            *)      echo "Unsupported macOS architecture: $ARCH"; exit 1 ;;
        esac
        ;;
    Linux)
        echo "Linux static binaries are not yet configured."
        echo "Please download ffmpeg, ffprobe, and img2webp for Linux $ARCH"
        echo "and place them in: $RESOURCES_DIR/"
        exit 1
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac
