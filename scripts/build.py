#!/usr/bin/env python3
"""Build a VideoStar release binary with PyInstaller for the current platform.

Prerequisites:
    pip install -e ".[build]"
    python scripts/fetch_binaries.py   # downloads ffmpeg + deno into build/binaries

Output:
    dist/VideoStar (one-file executable). The FFmpeg/deno binaries are bundled
    alongside so the app is fully self-contained.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onedir", action="store_true", help="build a folder instead of one file")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    system = platform.system()
    exe_suffix = ".exe" if system == "Windows" else ""
    name = args.name or f"VideoStar-{system.lower()}"

    binaries = ROOT / "build" / "binaries"
    datas = []
    if binaries.is_dir():
        for binary in sorted(binaries.iterdir()):
            if binary.is_file():
                datas.append(f"--add-data={binary}{os.pathsep}.")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        f"--name={name}",
        "--windowed" if system != "Linux" else "--noconsole",
        "--onefile" if not args.onedir else "--onedir",
        "--additional-hooks-dir=pyinstaller_hooks",
        "--collect-submodules=yt_dlp",
        "--collect-data=yt_dlp",
        "--collect-submodules=yt_dlp_ejs",
        "--collect-data=yt_dlp_ejs",
        "--collect-submodules=PySide6",
        "--collect-data=PySide6",
        "--hidden-import=mutagen",
        "--hidden-import=brotli",
        "--hidden-import=websockets",
        "--hidden-import=certifi",
        "--hidden-import=imageio_ffmpeg",
        "--exclude-module=tkinter",
        "--exclude-module=setuptools",
        "--exclude-module=pkg_resources",
        *datas,
        str(ROOT / "videostar_launcher.py"),
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        dist = ROOT / "dist"
        print(f"\nBuild complete: {dist / (name + exe_suffix)}")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
