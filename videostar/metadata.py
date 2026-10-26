"""Media metadata helpers: thumbnails and durations.

Thumbnails are fetched for remote URLs with yt-dlp (or downloaded directly),
cached on disk, and probed for duration with ffprobe or mutagen. Everything
degrades gracefully: a missing thumbnail or ffprobe just means less info.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from .bundled import find_ffprobe
from .settings import AUDIO_EXTS


def _safe_name(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def download_thumbnail(url: str, dest_dir: Path, source_url: str = "") -> Path | None:
    """Download the best thumbnail for a media URL into dest_dir. Returns the path or None."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_safe_name(source_url or url)}.jpg"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        import yt_dlp

        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writethumbnail": True,
            "outtmpl": str(dest_dir / f"{_safe_name(source_url or url)}.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        thumb = info.get("thumbnail") if info else None
        # yt-dlp writes the thumbnail next to outtmpl; find whatever it wrote.
        written = sorted(dest_dir.glob(f"{_safe_name(source_url or url)}.*"))
        written = [p for p in written if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        if written:
            chosen = written[0]
            if chosen != dest:
                chosen.rename(dest)
            return dest if dest.exists() else chosen
        if thumb and thumb.startswith("http"):
            import urllib.request

            urllib.request.urlretrieve(thumb, dest)
            return dest if dest.exists() and dest.stat().st_size > 0 else None
    except Exception:
        return None
    return None


def probe_duration(path: Path) -> int:
    """Best-effort duration in seconds for a media file. 0 when unknown."""
    try:
        if path.suffix.lower() in AUDIO_EXTS:
            from mutagen import File as MutagenFile  # type: ignore

            audio = MutagenFile(path)
            if audio is not None and getattr(audio, "info", None) is not None:
                return int(getattr(audio.info, "length", 0) or 0)
    except Exception:
        pass
    ffprobe = find_ffprobe()
    if ffprobe:
        try:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, timeout=30,
            )
            return int(float(out.stdout.strip() or 0))
        except Exception:
            pass
    return 0


def probe_audio(path: Path) -> dict[str, Any]:
    """Return mutagen/ffprobe audio info, or an empty dict."""
    info: dict[str, Any] = {}
    try:
        from mutagen import File as MutagenFile  # type: ignore

        audio = MutagenFile(path)
        if audio is not None and getattr(audio, "info", None) is not None:
            info["duration"] = int(getattr(audio.info, "length", 0) or 0)
            info["bitrate"] = int(getattr(audio.info, "bitrate", 0) or 0)
            info["sample_rate"] = int(getattr(audio.info, "sample_rate", 0) or 0)
    except Exception:
        pass
    return info
