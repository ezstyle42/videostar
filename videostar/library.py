"""Library of previously downloaded media.

A small JSON-backed store that records every completed download with its
metadata and on-disk location. The gallery UI reads from this store; the
store itself is UI-agnostic and fully unit-testable.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .settings import AUDIO_EXTS, VIDEO_EXTS

MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS


@dataclass
class LibraryEntry:
    id: str
    url: str
    title: str
    kind: str  # "video" or "audio"
    path: str  # absolute path to the downloaded file
    thumbnail: str = ""  # path to a cached thumbnail image, if any
    duration: int = 0  # seconds
    uploader: str = ""
    ext: str = ""
    size: int = 0  # bytes
    added_at: float = field(default_factory=time.time)

    @property
    def file_path(self) -> Path:
        return Path(self.path)

    @property
    def exists(self) -> bool:
        return self.file_path.exists()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LibraryEntry:
        known = {f.name for f in LibraryEntry.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class LibraryStore:
    """JSON-backed collection of LibraryEntry records."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._entries: list[LibraryEntry] = []
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self._entries = [LibraryEntry.from_dict(e) for e in data.get("entries", [])]
        except (OSError, json.JSONDecodeError):
            self._entries = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": [e.to_dict() for e in self._entries]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def all(self) -> list[LibraryEntry]:
        """All entries, newest first."""
        return sorted(self._entries, key=lambda e: e.added_at, reverse=True)

    def get(self, entry_id: str) -> LibraryEntry | None:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def add(self, entry: LibraryEntry) -> LibraryEntry:
        self._entries.append(entry)
        self._save()
        return entry

    def add_download(self, *, url: str, title: str, kind: str, path: Path,
                     thumbnail: Path | None = None, duration: int = 0,
                     uploader: str = "") -> LibraryEntry:
        entry = LibraryEntry(
            id=uuid.uuid4().hex,
            url=url,
            title=title,
            kind=kind,
            path=str(path),
            thumbnail=str(thumbnail) if thumbnail else "",
            duration=int(duration or 0),
            uploader=uploader,
            ext=path.suffix.lower(),
            size=path.stat().st_size if path.exists() else 0,
        )
        return self.add(entry)

    def remove(self, entry_id: str, delete_file: bool = False) -> bool:
        entry = self.get(entry_id)
        if entry is None:
            return False
        self._entries.remove(entry)
        if delete_file and entry.exists:
            try:
                entry.file_path.unlink()
            except OSError:
                pass
        if entry.thumbnail:
            try:
                Path(entry.thumbnail).unlink(missing_ok=True)
            except OSError:
                pass
        self._save()
        return True

    def prune_missing(self) -> int:
        """Drop entries whose files were deleted externally. Returns count removed."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.exists]
        if len(self._entries) != before:
            self._save()
        return before - len(self._entries)

    def filter(self, kind: str | None = None, query: str = "") -> list[LibraryEntry]:
        entries = self.all()
        if kind in ("video", "audio"):
            entries = [e for e in entries if e.kind == kind]
        if query:
            q = query.casefold()
            entries = [e for e in entries
                       if q in e.title.casefold() or q in e.uploader.casefold()]
        return entries

    def scan_directory(self, directory: Path) -> int:
        """Import media files found on disk that are not yet tracked. Returns count added."""
        if not directory.exists():
            return 0
        known = {e.path for e in self._entries}
        added = 0
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in MEDIA_EXTS:
                continue
            if str(path) in known:
                continue
            kind = "audio" if path.suffix.lower() in AUDIO_EXTS else "video"
            self.add_download(url="", title=path.stem, kind=kind, path=path)
            added += 1
        return added

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterable[LibraryEntry]:
        return iter(self.all())
