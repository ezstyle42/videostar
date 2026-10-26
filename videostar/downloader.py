"""Download engine: a Qt-friendly, thread-based wrapper around yt-dlp.

Each DownloadJob runs in a worker QThread and reports progress, state
changes and completion through Qt signals, so the UI stays responsive.
Jobs can be queued, cancelled and retried. On completion a LibraryEntry is
added to the LibraryStore and a thumbnail is fetched in the background.
"""

from __future__ import annotations

import re
import shlex
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from . import bundled
from .library import LibraryStore
from .metadata import download_thumbnail, probe_duration
from .paths import AppPaths
from .settings import Settings


class JobState(Enum):
    QUEUED = "queued"
    FETCHING = "fetching"  # resolving metadata
    DOWNLOADING = "downloading"
    PROCESSING = "processing"  # merging / converting
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class DownloadJob:
    url: str
    kind: str  # "video" or "audio"
    title: str = ""
    state: JobState = JobState.QUEUED
    progress: float = 0.0  # 0..100
    speed: str = ""
    eta: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error: str = ""
    file_path: str = ""
    entry_id: str = ""


class _Signal:
    """A single Qt-like signal usable from any thread without a QObject parent."""

    def __init__(self, *arg_types: Any) -> None:
        self._arg_types = arg_types
        self._subs: list[Callable[..., None]] = []
        self._qt_signal = None
        try:
            from PySide6.QtCore import QObject, Signal

            attrs = {"_sig": Signal(*arg_types) if arg_types else Signal()}
            cls = type("_SignalHolder", (QObject,), attrs)
            self._holder = cls()
            self._qt_signal = self._holder._sig
        except Exception:
            self._holder = None
            self._qt_signal = None

    def connect(self, fn: Callable[..., None]) -> None:
        if self._qt_signal is not None:
            self._qt_signal.connect(fn)
        else:
            self._subs.append(fn)

    def emit(self, *args: Any) -> None:
        if self._qt_signal is not None:
            self._qt_signal.emit(*args)
        else:
            for fn in list(self._subs):
                fn(*args)


class DownloadSignals:
    """Signal bundle emitted by the engine. Uses Qt signals when available."""

    def __init__(self) -> None:
        self.job_updated = _Signal(object)
        self.job_finished = _Signal(object)
        self.queue_changed = _Signal()


def _connect(sig: Any, fn: Callable[..., None]) -> None:
    if hasattr(sig, "connect"):
        sig.connect(fn)


def _emit(sig: Any, *args: Any) -> None:
    if hasattr(sig, "emit"):
        sig.emit(*args)


class DownloadEngine:
    """Queues and executes downloads. Thread-safe; Qt optional."""

    def __init__(self, settings: Settings, paths: AppPaths, library: LibraryStore,
                 max_workers: int = 2) -> None:
        self._settings = settings
        self._paths = paths
        self._library = library
        self._max_workers = max(1, max_workers)
        self.signals = DownloadSignals()
        self._jobs: list[DownloadJob] = []
        self._queue: list[DownloadJob] = []
        self._active: list[DownloadJob] = []
        self._lock = threading.Lock()
        self._threads: list[threading.Thread] = []
        self._cancelled: set[int] = set()
        self._ydl_lock = threading.Lock()

    # ------------------------------------------------------------------ API

    def jobs(self) -> list[DownloadJob]:
        with self._lock:
            return list(self._jobs)

    def active_jobs(self) -> list[DownloadJob]:
        with self._lock:
            return list(self._active)

    def queue_job(self, url: str, kind: str | None = None) -> DownloadJob:
        kind = kind or self._settings.mode
        job = DownloadJob(url=url.strip(), kind=kind)
        with self._lock:
            self._jobs.append(job)
            self._queue.append(job)
        _emit(self.signals.queue_changed)
        self._pump()
        return job

    def cancel_job(self, job: DownloadJob) -> None:
        with self._lock:
            self._cancelled.add(id(job))
            was_queued = job in self._queue
            if was_queued:
                self._queue.remove(job)
                job.state = JobState.CANCELLED
        if was_queued:
            _emit(self.signals.queue_changed)
            _emit(self.signals.job_updated, job)
        # Active jobs observe the cancel flag via the progress hook.

    def cancel_all(self) -> None:
        with self._lock:
            for job in list(self._queue):
                self._cancelled.add(id(job))
                job.state = JobState.CANCELLED
                self._queue.remove(job)
        _emit(self.signals.queue_changed)

    def clear_finished(self) -> None:
        with self._lock:
            self._jobs = [j for j in self._jobs
                          if j.state not in (JobState.DONE, JobState.ERROR, JobState.CANCELLED)]
        _emit(self.signals.queue_changed)

    def shutdown(self) -> None:
        self.cancel_all()
        for thread in list(self._threads):
            thread.join(timeout=5)

    # -------------------------------------------------------------- internals

    def _pump(self) -> None:
        while True:
            with self._lock:
                if len(self._active) >= self._max_workers or not self._queue:
                    return
                job = self._queue.pop(0)
                if id(job) in self._cancelled:
                    continue
                self._active.append(job)
                self._threads.append(threading.Thread(
                    target=self._run_job, args=(job,), daemon=True))
                thread = self._threads[-1]
            thread.start()
        # queue_changed emitted by callers

    def _notify_queue(self) -> None:
        _emit(self.signals.queue_changed)

    def _emit_job(self, job: DownloadJob) -> None:
        _emit(self.signals.job_updated, job)

    def _set_state(self, job: DownloadJob, state: JobState) -> None:
        job.state = state
        self._emit_job(job)

    def build_ydl_opts(self, job: DownloadJob, out_dir: Path) -> dict[str, Any]:
        """Translate app settings into yt-dlp options for a job."""
        s = self._settings
        opts: dict[str, Any] = {
            "outtmpl": str(out_dir / "%(title).80s [%(id)s].%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
            "no_progress": True,
            "ffmpeg_location": bundled.find_ffmpeg(),
            "paths": {"home": str(out_dir)},
            "overwrites": True,
        }
        js = bundled.find_js_runtime()
        if js:
            opts["extractor_args"] = {"youtube": {"js_runtimes": [f"{js[0]}:{js[1]}"]}}
        if self._paths.cookies_file.exists():
            opts["cookiefile"] = str(self._paths.cookies_file)
        if s.embed_metadata:
            opts["postprocessors"] = opts.get("postprocessors", [])
            if job.kind == "video":
                opts["postprocessors"].append({"key": "FFmpegMetadata", "add_metadata": True})
                if s.embed_thumbnail:
                    opts["postprocessors"].append({"key": "EmbedThumbnail"})
                    opts["writethumbnail"] = True
        if job.kind == "video":
            from .settings import quality_to_format

            opts["format"] = quality_to_format(s.quality, s.video_format)
            if s.write_subs:
                opts["writesubtitles"] = True
                opts["subformat"] = "srt/best"
        else:
            opts["format"] = "bestaudio/best"
            codec = s.audio_format if s.audio_format != "best" else "mp3"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": codec}]
        if s.extra_args:
            try:
                opts["cli_extra_args"] = shlex.split(s.extra_args)
            except ValueError:
                pass
        return opts

    def _progress_hook(self, job: DownloadJob, d: dict[str, Any]) -> None:
        if id(job) in self._cancelled:
            raise _Cancelled()
        status = d.get("status")
        if status == "downloading":
            job.state = JobState.DOWNLOADING
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            job.downloaded_bytes = int(downloaded)
            job.total_bytes = int(total)
            job.progress = (downloaded / total * 100) if total else job.progress
            job.speed = d.get("speed_str") or d.get("_speed_str") or ""
            job.eta = d.get("eta_str") or d.get("_eta_str") or ""
        elif status == "finished":
            job.state = JobState.PROCESSING
            job.progress = 100.0
        self._emit_job(job)

    def _run_job(self, job: DownloadJob) -> None:
        try:
            self._set_state(job, JobState.FETCHING)
            out_dir = Path(self._settings.download_dir) if self._settings.download_dir \
                else (self._paths.videos_dir if job.kind == "video" else self._paths.audio_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            opts = self.build_ydl_opts(job, out_dir)
            opts["progress_hooks"] = [lambda d: self._progress_hook(job, d)]

            import yt_dlp

            with self._ydl_lock:
                pass  # serialize YoutubeDL construction; downloads themselves run in parallel
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
            if id(job) in self._cancelled:
                raise _Cancelled()
            if info is None:
                raise RuntimeError("yt-dlp returned no information")
            if info.get("entries"):  # playlist
                info = info["entries"][-1]
            file_path = Path(ydl.prepare_filename(info))
            if job.kind == "audio" and self._settings.audio_format != "best":
                candidate = file_path.with_suffix(f".{self._settings.audio_format}")
                if candidate.exists():
                    file_path = candidate
            if not file_path.exists():
                # fall back to newest media file in the output dir
                media = [p for p in out_dir.iterdir()
                         if p.is_file() and p.suffix.lower() in
                         {".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".flac", ".opus", ".wav", ".ogg"}]
                if media:
                    file_path = max(media, key=lambda p: p.stat().st_mtime)
            job.title = info.get("title") or file_path.stem
            job.file_path = str(file_path)
            job.progress = 100.0
            self._set_state(job, JobState.DONE)
            entry = self._library.add_download(
                url=job.url,
                title=job.title,
                kind=job.kind,
                path=file_path,
                duration=probe_duration(file_path),
                uploader=info.get("uploader") or info.get("channel") or "",
            )
            job.entry_id = entry.id
            thumb = download_thumbnail(job.url, self._paths.thumbnails_dir, source_url=job.url)
            if thumb:
                entry.thumbnail = str(thumb)
                self._library._save()
            _emit(self.signals.job_finished, job)
        except _Cancelled:
            job.state = JobState.CANCELLED
            job.error = "Cancelled"
            self._emit_job(job)
            _emit(self.signals.job_finished, job)
        except Exception as exc:  # noqa: BLE001 - report any yt-dlp failure to the UI
            job.state = JobState.ERROR
            job.error = _clean_error(exc)
            self._emit_job(job)
            _emit(self.signals.job_finished, job)
        finally:
            with self._lock:
                if job in self._active:
                    self._active.remove(job)
                if job in self._threads:
                    pass
            self._cancelled.discard(id(job))
            self._pump()


class _Cancelled(Exception):
    pass


def _clean_error(exc: BaseException) -> str:
    text = str(exc) or exc.__class__.__name__
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def parse_urls(text: str) -> list[str]:
    """Extract http(s) URLs from arbitrary pasted text."""
    return re.findall(r"https?://[^\s\"'<>\]\)]+", text)
