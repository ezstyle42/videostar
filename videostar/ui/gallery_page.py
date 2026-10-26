"""Library page: a gallery of previously downloaded videos and audio."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..library import LibraryEntry, LibraryStore
from ..paths import AppPaths
from ..settings import SettingsStore

CARD_W = 220
CARD_H = 220


def format_duration(seconds: int) -> str:
    if not seconds:
        return ""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


class GalleryCard(QFrame):
    def __init__(self, entry: LibraryEntry, gallery: GalleryPage,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.entry = entry
        self.gallery = gallery
        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(6)

        self.thumb = QLabel()
        self.thumb.setFixedSize(CARD_W, 130)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setStyleSheet("background: #1a1b22; border-radius: 10px 10px 0 0; color: #4a4b5a;")
        self.thumb.setText("♪" if entry.kind == "audio" else "▶")
        self.thumb.setStyleSheet(
            self.thumb.styleSheet() + "font-size: 34px;")
        layout.addWidget(self.thumb)
        self._load_thumbnail()

        title = QLabel(entry.title or Path(entry.path).stem)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(36)
        layout.addWidget(title)

        meta_parts = [entry.kind.upper()]
        if entry.duration:
            meta_parts.append(format_duration(entry.duration))
        if entry.size:
            meta_parts.append(format_size(entry.size))
        meta = QLabel("  •  ".join(meta_parts))
        meta.setObjectName("cardMeta")
        layout.addWidget(meta)

        layout.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(10, 0, 10, 0)
        play = QPushButton("Open")
        play.setProperty("flat", True)
        play.clicked.connect(self._open)
        reveal = QPushButton("Folder")
        reveal.setProperty("flat", True)
        reveal.clicked.connect(self._reveal)
        delete = QPushButton("✕")
        delete.setProperty("flat", True)
        delete.setFixedWidth(30)
        delete.clicked.connect(self._delete)
        buttons.addWidget(play)
        buttons.addWidget(reveal)
        buttons.addStretch(1)
        buttons.addWidget(delete)
        layout.addLayout(buttons)

    def _load_thumbnail(self) -> None:
        if self.entry.thumbnail and Path(self.entry.thumbnail).exists():
            pix = QPixmap(self.entry.thumbnail)
            if not pix.isNull():
                self.thumb.setPixmap(pix.scaled(
                    CARD_W, 130,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation))

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self._open()

    def _open(self) -> None:
        path = self.entry.file_path
        if not path.exists():
            QMessageBox.information(self, "Missing file", "This file no longer exists on disk.")
            return
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _reveal(self) -> None:
        path = self.entry.file_path
        if not path.exists():
            return
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path.parent)])

    def _delete(self) -> None:
        answer = QMessageBox.question(
            self, "Remove from library",
            f"Remove “{self.entry.title}” from the library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete_file = QMessageBox.question(
            self, "Delete file?",
            "Also delete the downloaded file from disk?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.gallery.remove_entry(self.entry, delete_file == QMessageBox.StandardButton.Yes)


class GalleryPage(QWidget):
    def __init__(self, library: LibraryStore, paths: AppPaths,
                 settings_store: SettingsStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.library = library
        self.paths = paths
        self.settings_store = settings_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        heading = QLabel("Library")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search downloads…")
        self.search.textChanged.connect(self.refresh)
        controls.addWidget(self.search, stretch=1)

        controls.addWidget(QLabel("Show:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Videos", "Audio"])
        self.filter_combo.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.filter_combo)

        self.import_btn = QPushButton("Import folder…")
        self.import_btn.clicked.connect(self._import_folder)
        controls.addWidget(self.import_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_btn)
        layout.addLayout(controls)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(16)
        self.scroll.setWidget(self.grid_host)
        layout.addWidget(self.scroll, stretch=1)

        self.empty = QLabel("No downloads yet.\nHead to the Download tab and paste a URL.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setProperty("subtle", True)
        self.empty.setStyleSheet("font-size: 16px; padding: 60px;")
        layout.addWidget(self.empty)

        self.refresh()

    # -------------------------------------------------------------- actions

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        kind_map = {"All": None, "Videos": "video", "Audio": "audio"}
        kind = kind_map.get(self.filter_combo.currentText())
        entries = self.library.filter(kind=kind, query=self.search.text())

        columns = max(1, self.settings_store.settings.gallery_columns)
        for index, entry in enumerate(entries):
            card = GalleryCard(entry, self)
            self.grid.addWidget(card, index // columns, index % columns)

        self.empty.setVisible(not entries)
        self.empty.setParent(self)
        if not entries:
            self.layout().addWidget(self.empty, stretch=1)

    def remove_entry(self, entry: LibraryEntry, delete_file: bool) -> None:
        self.library.remove(entry.id, delete_file=delete_file)
        self.refresh()

    def open_downloads_folder(self) -> None:
        folder = self.paths.downloads_dir
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _import_folder(self) -> None:
        start = self.settings_store.settings.download_dir or str(self.paths.downloads_dir)
        folder = QFileDialog.getExistingDirectory(self, "Import a folder of media", start)
        if folder:
            added = self.library.scan_directory(Path(folder))
            QMessageBox.information(self, "Import complete", f"Imported {added} file(s).")
            self.refresh()
