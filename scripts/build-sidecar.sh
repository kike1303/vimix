#!/usr/bin/env bash
set -euo pipefail

# Build the Python sidecar binary and copy it to the Tauri binaries directory.
# Supports macOS, Linux, and Windows (Git Bash / MSYS2).

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROCESSOR_DIR="$REPO_ROOT/services/processor"
TAURI_BIN_DIR="$REPO_ROOT/apps/web/src-tauri/binaries"

# Detect Rust host triple (e.g. aarch64-apple-darwin)
HOST_TRIPLE=$(rustc -vV | grep '^host:' | awk '{print $2}')
if [ -z "$HOST_TRIPLE" ]; then
  echo "Error: Could not detect Rust host triple. Is rustc installed?" >&2
  exit 1
fi

echo "==> Building sidecar for $HOST_TRIPLE"

OS="$(uname -s)"

# Activate venv and run PyInstaller
cd "$PROCESSOR_DIR"

case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows: venv uses Scripts/ directory
    # shellcheck disable=SC1091
    source venv/Scripts/activate
    ;;
  *)
    # macOS / Linux
    # shellcheck disable=SC1091
    source venv/bin/activate
    ;;
esac

pyinstaller vimix-processor.spec --noconfirm

# Copy to Tauri binaries with platform suffix
mkdir -p "$TAURI_BIN_DIR"

case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    cp dist/Vimix-processor.exe "$TAURI_BIN_DIR/Vimix-processor-$HOST_TRIPLE.exe"
    echo "==> Sidecar built: Vimix-processor-$HOST_TRIPLE.exe"
    ;;
  *)
    cp dist/Vimix-processor "$TAURI_BIN_DIR/Vimix-processor-$HOST_TRIPLE"
    echo "==> Sidecar built: Vimix-processor-$HOST_TRIPLE"
    ;;
esac
