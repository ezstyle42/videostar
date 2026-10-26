"""Persistent user settings.

Settings are stored as JSON in the user config directory and are loaded and
saved through the SettingsStore so the UI never touches the filesystem
directly. Unknown keys are preserved so newer versions don't clobber data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".m4v", ".ts", ".mpg", ".mpeg", ".3gp"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wav", ".wma", ".aiff"}


@dataclass
class Settings:
    """User preferences. All fields have defaults so old settings files keep working."""

    mode: str = "video"  # "video" or "audio"
    video_format: str = "best"  # yt-dlp format selector for video
    audio_format: str = "mp3"  # mp3, m4a, flac, opus, wav, best
    quality: str = "best"  # best, 1080p, 720p, 480p, 360p (video only)
    download_dir: str = ""  # empty -> default per-user downloads dir
    concurrent_downloads: int = 2
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    write_subs: bool = False
    theme: str = "dark"  # dark or light
    start_minimized: bool = False
    gallery_columns: int = 4
    extra_args: str = ""  # raw yt-dlp CLI-style options, for power users

    @classmethod
    def field_names(cls) -> set[str]:
        return {f.name for f in fields(cls)}


class SettingsStore:
    """Loads and saves a Settings object as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.settings = Settings()
        self.load()

    def load(self) -> Settings:
        data: dict[str, Any] = {}
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        known = Settings.field_names()
        values = {k: v for k, v in data.items() if k in known}
        self.settings = Settings(**values)
        self._extra = {k: v for k, v in data.items() if k not in known}
        return self.settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {f.name: getattr(self.settings, f.name) for f in fields(Settings)}
        data.update(getattr(self, "_extra", {}))
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def update(self, **changes: Any) -> Settings:
        known = Settings.field_names()
        for key, value in changes.items():
            if key not in known:
                raise KeyError(f"unknown setting: {key}")
            setattr(self.settings, key, value)
        self.save()
        return self.settings


def quality_to_format(quality: str, base: str = "best") -> str:
    """Translate a friendly quality label into a yt-dlp format selector."""
    if quality in ("best", ""):
        return "bv*+ba/b"
    heights = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
    height = heights.get(quality)
    if height is None:
        return base or "bv*+ba/b"
    return f"bv*[height<=?{height}]+ba/b"
