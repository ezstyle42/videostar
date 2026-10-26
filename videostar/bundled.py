"""Locate yt-dlp, FFmpeg and a JavaScript runtime across dev, frozen and portable layouts.

Resolution order for each binary:
  1. A sibling directory next to the executable (portable layout / PyInstaller bundle).
  2. The PATH (system install).
  3. Packaged Python wheels (imageio-ffmpeg for FFmpeg, deno for the JS runtime).

The yt-dlp Python package itself is always bundled with the app, so no
yt-dlp binary is ever needed.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _exe(name: str) -> str:
    return f"{name}.exe" if sys.platform == "win32" else name


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_root() -> Path:
    """Directory that holds bundled binaries when frozen (PyInstaller _MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def _candidate_dirs() -> list[Path]:
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(Path(sys.executable).parent)
    dirs.append(_bundle_root())
    return dirs


def _find_in_dirs(name: str, dirs: list[Path]) -> str | None:
    exe = _exe(name)
    for d in dirs:
        for sub in (d, d / "bin", d / "ffmpeg", d / "deno"):
            candidate = sub / exe
            if candidate.is_file():
                return str(candidate)
    return None


def find_ffmpeg() -> str | None:
    """Return the path to an ffmpeg binary, or None."""
    found = _find_in_dirs("ffmpeg", _candidate_dirs())
    if found:
        return found
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_ffprobe() -> str | None:
    """Return the path to an ffprobe binary, or None."""
    found = _find_in_dirs("ffprobe", _candidate_dirs())
    if found:
        return found
    found = shutil.which("ffprobe")
    if found:
        return found
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        sibling = Path(ffmpeg).parent / _exe("ffprobe")
        if sibling.is_file():
            return str(sibling)
    return None


def find_js_runtime() -> tuple[str, str] | None:
    """Return (runtime_name, path) for a JS runtime usable by yt-dlp, or None."""
    found = _find_in_dirs("deno", _candidate_dirs())
    if found:
        return "deno", found
    found = shutil.which("deno")
    if found:
        return "deno", found
    try:
        from deno import _find_deno  # type: ignore

        path = _find_deno.find_deno_binary()
        if path:
            return "deno", str(path)
    except Exception:
        pass
    return None


def ffmpeg_available() -> bool:
    return find_ffmpeg() is not None


def environment_for_yt_dlp() -> dict[str, str]:
    """Environment overrides (PATH additions) so yt-dlp finds bundled tools."""
    env = dict(os.environ)
    additions = []
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        additions.append(str(Path(ffmpeg).parent))
    js = find_js_runtime()
    if js:
        additions.append(str(Path(js[1]).parent))
    if additions:
        env["PATH"] = os.pathsep.join(additions + [env.get("PATH", "")])
    return env
