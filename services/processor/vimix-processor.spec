# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Vimix Processor sidecar binary.

Build with:
    cd services/processor
    source venv/bin/activate
    pyinstaller vimix-processor.spec

Output: dist/Vimix-processor/ (one-directory bundle)
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# Paths
spec_dir = os.path.dirname(os.path.abspath(SPEC))
home = Path.home()
u2net_dir = home / ".u2net"

# Collect rembg hidden imports (ONNX runtime, sessions, etc.)
rembg_hidden = collect_submodules("rembg")
onnx_hidden = collect_submodules("onnxruntime")

# Data files: rembg needs its bundled resources
rembg_data = collect_data_files("rembg")

# Package metadata needed at runtime (importlib.metadata.version() calls)
pkg_metadata = []
for pkg in ["pymatting", "rembg", "scikit-image", "onnxruntime", "pillow",
            "opencv-python-headless", "numpy", "scipy", "PyMuPDF", "tqdm",
            "pooch", "certifi"]:
    try:
        pkg_metadata += copy_metadata(pkg)
    except Exception:
        pass

# MCP registration module (bundled so sidecar can auto-register on startup)
mcp_dir = os.path.join(spec_dir, "..", "mcp")
mcp_datas = []
if os.path.isfile(os.path.join(mcp_dir, "register.py")):
    mcp_datas.append((os.path.join(mcp_dir, "register.py"), "mcp"))

# Bundle libomp on macOS so the desktop app doesn't require homebrew.
# On Windows the MSVC OpenMP runtime is picked up automatically by PyInstaller.
# On Linux libgomp is typically system-provided and PyInstaller bundles it.
libomp_binaries = []
if sys.platform == "darwin":
    for libomp_path in [
        "/opt/homebrew/opt/libomp/lib/libomp.dylib",
        "/opt/homebrew/lib/libomp.dylib",
        "/usr/local/lib/libomp.dylib",
    ]:
        if os.path.isfile(libomp_path):
            libomp_binaries.append((libomp_path, "."))
            break

# Include the small ONNX model (u2netp ~4.4 MB) for offline use
# Larger models (u2net ~168 MB, isnet ~170 MB) can be downloaded on first use
model_datas = []
u2netp_path = u2net_dir / "u2netp.onnx"
if u2netp_path.exists():
    model_datas.append((str(u2netp_path), ".u2net"))

a = Analysis(
    ["app/main.py"],
    pathex=[spec_dir],
    binaries=libomp_binaries,
    datas=rembg_data + model_datas + mcp_datas + pkg_metadata,
    hiddenimports=[
        *rembg_hidden,
        *onnx_hidden,
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvloop",
        "httptools",
        "app",
        "app.main",
        "app.routers",
        "app.routers.jobs",
        "app.routers.processors",
        "app.processors",
        "app.processors.registry",
        "app.processors.base",
        "app.processors.video_bg_remove",
        "app.processors.image_bg_remove",
        "app.processors.image_convert",
        "app.processors.video_convert",
        "app.processors.video_to_gif",
        "app.processors.image_compress",
        "app.processors.video_trim",
        "app.processors.audio_extract",
        "app.processors.video_compress",
        "app.processors.image_watermark",
        "app.processors.pdf_to_image",
        "app.processors.video_thumbnail",
        "app.services",
        "app.services.job_manager",
        "app.services.file_manager",
        "app.services.binary_paths",
        "multipart",
        "multipart.multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="Vimix-processor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
