#!/usr/bin/env python3
"""Download FFmpeg and deno binaries for bundling into release builds.

Usage:
    python scripts/fetch_binaries.py [--dest build/binaries] [--platform linux|windows|macos] [--arch x64|arm64]

Linux/Windows fetch static FFmpeg builds from johnvansickle.com / BtbN and
deno from GitHub releases. macOS uses the system tools (brew) by default;
pass --platform macos to fetch deno only.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

FFMPEG_URLS = {
    ("linux", "x64"): "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    ("windows", "x64"): "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
}
DENO_VERSION = "2.5.6"
DENO_URLS = {
    ("linux", "x64"): f"https://github.com/denoland/deno/releases/download/v{DENO_VERSION}/deno-x86_64-unknown-linux-gnu.zip",
    ("windows", "x64"): f"https://github.com/denoland/deno/releases/download/v{DENO_VERSION}/deno-x86_64-pc-windows-msvc.zip",
    ("macos", "x64"): f"https://github.com/denoland/deno/releases/download/v{DENO_VERSION}/deno-x86_64-apple-darwin.zip",
    ("macos", "arm64"): f"https://github.com/denoland/deno/releases/download/v{DENO_VERSION}/deno-aarch64-apple-darwin.zip",
}


def detect() -> tuple[str, str]:
    system = {"Linux": "linux", "Windows": "windows", "Darwin": "macos"}[platform.system()]
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    return system, arch


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)


def extract(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif archive.name.endswith((".tar.xz", ".txz", ".tar.gz", ".tgz")):
        with tarfile.open(archive) as tf:
            tf.extractall(dest, filter="data")
    else:
        subprocess.run(["tar", "-xf", str(archive), "-C", str(dest)], check=True)


def fetch_ffmpeg(system: str, arch: str, dest: Path) -> list[Path]:
    if system == "macos":
        # macOS builds rely on the system ffmpeg (brew install ffmpeg); nothing to bundle.
        return []
    url = FFMPEG_URLS[(system, arch)]
    archive = dest / "ffmpeg-dl" / Path(url).name
    download(url, archive)
    extract_dir = dest / "ffmpeg-extract"
    extract(archive, extract_dir)
    found = []
    for name in ("ffmpeg", "ffprobe", "ffmpeg.exe", "ffprobe.exe"):
        for candidate in extract_dir.rglob(name):
            target = dest / name
            shutil.copy2(candidate, target)
            target.chmod(target.stat().st_mode | stat.S_IEXEC)
            found.append(target)
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(dest / "ffmpeg-dl", ignore_errors=True)
    return found


def fetch_deno(system: str, arch: str, dest: Path) -> list[Path]:
    url = DENO_URLS[(system, arch)]
    archive = dest / "deno-dl" / Path(url).name
    download(url, archive)
    extract_dir = dest / "deno-extract"
    extract(archive, extract_dir)
    found = []
    for candidate in extract_dir.rglob("deno*"):
        if candidate.is_file() and candidate.suffix in ("", ".exe"):
            target = dest / candidate.name
            shutil.copy2(candidate, target)
            target.chmod(target.stat().st_mode | stat.S_IEXEC)
            found.append(target)
    shutil.rmtree(extract_dir, ignore_errors=True)
    shutil.rmtree(dest / "deno-dl", ignore_errors=True)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default="build/binaries")
    parser.add_argument("--platform", choices=["linux", "windows", "macos"])
    parser.add_argument("--arch", choices=["x64", "arm64"])
    args = parser.parse_args()

    system, arch = args.platform, args.arch
    if not system or not arch:
        system, arch = detect()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    ffmpeg = fetch_ffmpeg(system, arch, dest)
    deno = fetch_deno(system, arch, dest)
    print(f"ffmpeg: {[str(p) for p in ffmpeg]}")
    print(f"deno:   {[str(p) for p in deno]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
