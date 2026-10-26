"""Settings page: every preference, persisted immediately."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import bundled
from ..paths import AppPaths
from ..settings import SettingsStore
from .download_page import AUDIO_FORMATS, QUALITIES


class SettingsPage(QWidget):
    def __init__(self, settings_store: SettingsStore, paths: AppPaths,
                 on_changed: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings_store = settings_store
        self.paths = paths
        self.on_changed = on_changed
        s = settings_store.settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        heading = QLabel("Settings")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        form = QFormLayout()
        form.setSpacing(12)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Video", "Audio"])
        self.mode_combo.setCurrentText("Video" if s.mode == "video" else "Audio")
        self.mode_combo.currentTextChanged.connect(
            lambda t: self._save(mode=t.lower()))
        form.addRow("Default download type", self.mode_combo)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(QUALITIES)
        self.quality_combo.setCurrentText(s.quality)
        self.quality_combo.currentTextChanged.connect(
            lambda t: self._save(quality=t))
        form.addRow("Video quality", self.quality_combo)

        self.audio_combo = QComboBox()
        self.audio_combo.addItems(AUDIO_FORMATS)
        self.audio_combo.setCurrentText(s.audio_format)
        self.audio_combo.currentTextChanged.connect(
            lambda t: self._save(audio_format=t))
        form.addRow("Audio format", self.audio_combo)

        dir_row = QHBoxLayout()
        self.dir_edit = QLineEdit(s.download_dir)
        self.dir_edit.setPlaceholderText(str(paths.downloads_dir))
        self.dir_edit.textChanged.connect(lambda t: self._save(download_dir=t))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_dir)
        clear = QPushButton("Reset")
        clear.clicked.connect(lambda: (self.dir_edit.setText(""), self._save(download_dir="")))
        dir_row.addWidget(self.dir_edit, stretch=1)
        dir_row.addWidget(browse)
        dir_row.addWidget(clear)
        form.addRow("Download folder", dir_row)

        self.workers = QSpinBox()
        self.workers.setRange(1, 8)
        self.workers.setValue(s.concurrent_downloads)
        self.workers.valueChanged.connect(lambda v: self._save(concurrent_downloads=v))
        form.addRow("Concurrent downloads", self.workers)

        self.columns = QSpinBox()
        self.columns.setRange(2, 8)
        self.columns.setValue(s.gallery_columns)
        self.columns.valueChanged.connect(lambda v: self._save(gallery_columns=v))
        form.addRow("Gallery columns", self.columns)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText("Dark" if s.theme == "dark" else "Light")
        self.theme_combo.currentTextChanged.connect(lambda t: self._save(theme=t.lower()))
        form.addRow("Theme", self.theme_combo)

        self.checks = {}
        for key, label in (
            ("embed_thumbnail", "Embed thumbnail into video files"),
            ("embed_metadata", "Embed metadata into files"),
            ("write_subs", "Download subtitles (video)"),
            ("start_minimized", "Start minimized to tray"),
        ):
            cb = QCheckBox(label)
            cb.setChecked(getattr(s, key))
            cb.toggled.connect(lambda checked, k=key: self._save(**{k: checked}))
            self.checks[key] = cb
            form.addRow(cb)

        self.extra_args = QLineEdit(s.extra_args)
        self.extra_args.setPlaceholderText("Extra yt-dlp options, e.g. --cookies-from-browser chrome")
        self.extra_args.textChanged.connect(lambda t: self._save(extra_args=t))
        form.addRow("Extra yt-dlp options", self.extra_args)

        layout.addLayout(form)
        layout.addStretch(1)

        status = QLabel(self._status_text())
        status.setProperty("subtle", True)
        status.setWordWrap(True)
        layout.addWidget(status)

    def _status_text(self) -> str:
        ffmpeg = bundled.find_ffmpeg() or "not found"
        js = bundled.find_js_runtime()
        js_text = f"{js[0]} ({js[1]})" if js else "not found (YouTube may be limited)"
        cookies = "yes" if self.paths.cookies_file.exists() else "no"
        return (f"FFmpeg: {ffmpeg}\nJavaScript runtime: {js_text}\n"
                f"Cookies file: {self.paths.cookies_file} (present: {cookies})\n"
                f"Settings saved to: {self.settings_store.path}")

    def _browse_dir(self) -> None:
        start = self.dir_edit.text() or str(self.paths.downloads_dir)
        chosen = QFileDialog.getExistingDirectory(self, "Choose download folder", start)
        if chosen:
            self.dir_edit.setText(chosen)

    def _save(self, **changes) -> None:
        self.settings_store.update(**changes)
        self.on_changed()
