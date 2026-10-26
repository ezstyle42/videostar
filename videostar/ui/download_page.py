"""Download page: URL input, video/audio toggle, options and the job queue."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..downloader import DownloadEngine, DownloadJob, parse_urls
from ..paths import AppPaths
from ..settings import SettingsStore

QUALITIES = ["best", "1080p", "720p", "480p", "360p"]
AUDIO_FORMATS = ["mp3", "m4a", "flac", "opus", "wav", "best"]


class DownloadPage(QWidget):
    def __init__(self, engine: DownloadEngine, settings_store: SettingsStore,
                 paths: AppPaths, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.settings_store = settings_store
        self.paths = paths

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        heading = QLabel("Download")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        layout.addWidget(self._build_input_area())
        layout.addWidget(self._build_options_area())

        queue_label = QLabel("Queue")
        queue_label.setProperty("heading", True)
        queue_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(queue_label)

        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(160)
        layout.addWidget(self.queue_list, stretch=1)

        buttons = QHBoxLayout()
        self.clear_btn = QPushButton("Clear finished")
        self.clear_btn.clicked.connect(self._clear_finished)
        self.cancel_all_btn = QPushButton("Cancel all")
        self.cancel_all_btn.clicked.connect(self.engine.cancel_all)
        buttons.addWidget(self.clear_btn)
        buttons.addWidget(self.cancel_all_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.engine.signals.job_updated.connect(self._on_job_updated)
        self.engine.signals.queue_changed.connect(self._rebuild_queue)
        self._rebuild_queue()

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._rebuild_queue)
        self._timer.start()

    # ------------------------------------------------------------- builders

    def _build_input_area(self) -> QFrame:
        frame = QFrame(objectName="dropZone")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a video or audio URL here…")
        self.url_edit.returnPressed.connect(self._add_current)
        layout.addWidget(self.url_edit)

        row = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Video", "Audio"])
        self.mode_combo.setCurrentText("Video" if self.settings_store.settings.mode == "video" else "Audio")
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        row.addWidget(QLabel("Type:"))
        row.addWidget(self.mode_combo)
        row.addStretch(1)

        self.add_btn = QPushButton("Add to queue")
        self.add_btn.clicked.connect(self._add_current)
        row.addWidget(self.add_btn)
        layout.addLayout(row)

        hint = QLabel("Tip: you can paste several URLs at once, or a whole playlist.")
        hint.setProperty("subtle", True)
        layout.addWidget(hint)
        return frame

    def _build_options_area(self) -> QWidget:
        widget = QWidget()
        row = QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(18)

        row.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(QUALITIES)
        self.quality_combo.setCurrentText(self.settings_store.settings.quality)
        self.quality_combo.currentTextChanged.connect(
            lambda t: self.settings_store.update(quality=t))
        row.addWidget(self.quality_combo)

        row.addWidget(QLabel("Audio format:"))
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(AUDIO_FORMATS)
        self.audio_format_combo.setCurrentText(self.settings_store.settings.audio_format)
        self.audio_format_combo.currentTextChanged.connect(
            lambda t: self.settings_store.update(audio_format=t))
        row.addWidget(self.audio_format_combo)

        row.addStretch(1)

        self.dir_label = QLabel(self._dir_text())
        self.dir_label.setProperty("subtle", True)
        row.addWidget(self.dir_label)
        pick = QPushButton("Change…")
        pick.setProperty("flat", True)
        pick.clicked.connect(self._pick_dir)
        row.addWidget(pick)
        return widget

    def _dir_text(self) -> str:
        s = self.settings_store.settings
        if s.download_dir:
            return s.download_dir
        return str(self.paths.videos_dir if s.mode == "video" else self.paths.audio_dir)

    # -------------------------------------------------------------- actions

    def _on_mode_changed(self, text: str) -> None:
        self.settings_store.update(mode=text.lower())
        self.dir_label.setText(self._dir_text())

    def _pick_dir(self) -> None:
        start = self.settings_store.settings.download_dir or str(self.paths.downloads_dir)
        chosen = QFileDialog.getExistingDirectory(self, "Choose download folder", start)
        if chosen:
            self.settings_store.update(download_dir=chosen)
            self.dir_label.setText(chosen)

    def _add_current(self) -> None:
        text = self.url_edit.text()
        urls = parse_urls(text)
        if not urls:
            QMessageBox.information(self, "No URL", "Please paste at least one http(s) URL.")
            return
        kind = self.settings_store.settings.mode
        for url in urls:
            self.engine.queue_job(url, kind)
        self.url_edit.clear()

    def _clear_finished(self) -> None:
        self.engine.clear_finished()

    # -------------------------------------------------------------- rendering

    def _rebuild_queue(self) -> None:
        jobs = self.engine.jobs()
        selected = self.queue_list.currentRow()
        self.queue_list.clear()
        for job in jobs:
            item = QListWidgetItem(self._job_text(job))
            item.setData(Qt.ItemDataRole.UserRole, id(job))
            self.queue_list.addItem(item)
        if 0 <= selected < self.queue_list.count():
            self.queue_list.setCurrentRow(selected)
        if not jobs:
            self.queue_list.addItem("No downloads yet — paste a URL above.")

    def _job_text(self, job: DownloadJob) -> str:
        state = job.state.value
        if state == "downloading":
            return (f"⬇ {job.url}  —  {job.progress:5.1f}%  "
                    f"({job.speed} ETA {job.eta})")
        if state == "fetching":
            return f"… resolving {job.url}"
        if state == "processing":
            return f"⚙ processing {job.title or job.url}"
        if state == "done":
            return f"✔ {job.title or job.url}"
        if state == "error":
            return f"✖ {job.url} — {job.error}"
        if state == "cancelled":
            return f"⊘ {job.url} — cancelled"
        return f"• queued {job.url}"

    def _on_job_updated(self, job: DownloadJob) -> None:
        self._rebuild_queue()
