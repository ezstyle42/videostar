"""Main window: sidebar navigation between Download, Library and Settings pages."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..downloader import DownloadEngine
from ..library import LibraryStore
from ..paths import AppPaths
from ..settings import SettingsStore
from .download_page import DownloadPage
from .gallery_page import GalleryPage
from .settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore, library: LibraryStore,
                 paths: AppPaths, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings_store = settings_store
        self.library = library
        self.paths = paths

        self.engine = DownloadEngine(
            settings=settings_store.settings,
            paths=paths,
            library=library,
            max_workers=settings_store.settings.concurrent_downloads,
        )

        self.setWindowTitle("VideoStar")
        self.resize(1080, 700)
        self.setMinimumSize(860, 560)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.download_page = DownloadPage(self.engine, self.settings_store, self.paths)
        self.gallery_page = GalleryPage(self.library, self.paths, self.settings_store)
        self.settings_page = SettingsPage(self.settings_store, self.paths, self._on_settings_changed)

        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        self.stack.addWidget(self.download_page)
        self.stack.addWidget(self.gallery_page)
        self.stack.addWidget(self.settings_page)

        self.engine.signals.job_finished.connect(self._on_job_finished)
        self._nav_buttons[self.download_page].setChecked(True)

    def _build_sidebar(self) -> QFrame:
        from PySide6.QtWidgets import QLabel, QPushButton

        bar = QFrame(objectName="sidebar")
        bar.setFixedWidth(190)
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(6)

        logo = QLabel("VideoStar")
        logo.setStyleSheet("font-size: 20px; font-weight: 800; color: #7c5cff; padding: 6px;")
        layout.addWidget(logo)
        layout.addSpacing(14)

        self._nav_buttons = {}
        for page, label, icon in (
            (self.download_page, "Download", "⬇"),
            (self.gallery_page, "Library", "▦"),
            (self.settings_page, "Settings", "⚙"),
        ):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setProperty("flat", True)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, p=page: self._switch_to(p))
            self._nav_buttons[page] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        open_folder = QPushButton("  📂  Open downloads")
        open_folder.setProperty("flat", True)
        open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder.clicked.connect(self.gallery_page.open_downloads_folder)
        layout.addWidget(open_folder)

        version = QLabel("powered by yt-dlp")
        version.setProperty("subtle", True)
        version.setStyleSheet("color: #8a8b95; font-size: 11px; padding: 6px;")
        layout.addWidget(version)
        return bar

    def _switch_to(self, page) -> None:
        self.stack.setCurrentWidget(page)
        for p, btn in self._nav_buttons.items():
            btn.setChecked(p is page)
        if page is self.gallery_page:
            self.gallery_page.refresh()

    def _on_job_finished(self, job) -> None:
        if job.state.value == "done":
            self.gallery_page.refresh()

    def _on_settings_changed(self) -> None:
        s = self.settings_store.settings
        self.engine._settings = s
        self.engine._max_workers = max(1, s.concurrent_downloads)
        from PySide6.QtWidgets import QApplication

        from .theme import apply_theme

        apply_theme(QApplication.instance(), s.theme)

    def shutdown(self) -> None:
        self.engine.shutdown()
