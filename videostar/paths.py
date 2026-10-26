"""Filesystem locations used by VideoStar.

All user data lives under a per-user config directory so the app works the
same on Windows, macOS and Linux and survives being frozen with PyInstaller.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "videostar"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _base_config_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / APP_NAME


def _base_data_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / APP_NAME


def _base_cache_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / APP_NAME


class AppPaths:
    """Resolved per-user directories for config, data and cache."""

    def __init__(self, config_root: Path | None = None, data_root: Path | None = None,
                 cache_root: Path | None = None) -> None:
        self.config_root = config_root or _base_config_dir()
        self.data_root = data_root or _base_data_dir()
        self.cache_root = cache_root or _base_cache_dir()

    @property
    def settings_file(self) -> Path:
        return self.config_root / "settings.json"

    @property
    def library_file(self) -> Path:
        return self.data_root / "library.json"

    @property
    def downloads_dir(self) -> Path:
        return self.data_root / "downloads"

    @property
    def videos_dir(self) -> Path:
        return self.downloads_dir / "videos"

    @property
    def audio_dir(self) -> Path:
        return self.downloads_dir / "audio"

    @property
    def thumbnails_dir(self) -> Path:
        return self.cache_root / "thumbnails"

    @property
    def cookies_file(self) -> Path:
        return self.config_root / "cookies.txt"

    def ensure_dirs(self) -> None:
        for path in (self.config_root, self.data_root, self.cache_root,
                     self.videos_dir, self.audio_dir, self.thumbnails_dir):
            path.mkdir(parents=True, exist_ok=True)


_default_paths: AppPaths | None = None


def get_paths() -> AppPaths:
    """Return the process-wide default AppPaths, creating it on first use."""
    global _default_paths
    if _default_paths is None:
        _default_paths = AppPaths()
        _default_paths.ensure_dirs()
    return _default_paths


def set_paths(paths: AppPaths) -> None:
    """Override the process-wide default paths (used by tests)."""
    global _default_paths
    _default_paths = paths
