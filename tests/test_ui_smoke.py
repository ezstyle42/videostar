import os

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.No))
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: None))

from videostar.downloader import DownloadEngine  # noqa: E402
from videostar.settings import Settings  # noqa: E402
from videostar.ui.download_page import DownloadPage  # noqa: E402
from videostar.ui.gallery_page import GalleryPage, format_duration, format_size  # noqa: E402
from videostar.ui.main_window import MainWindow  # noqa: E402
from videostar.ui.settings_page import SettingsPage  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_format_helpers():
    assert format_duration(0) == ""
    assert format_duration(65) == "1:05"
    assert format_duration(3661) == "1:01:01"
    assert format_size(0) == "0 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(5 * 1024 * 1024) == "5.0 MB"


def test_main_window_builds(qapp, paths, settings_store, library):
    window = MainWindow(settings_store=settings_store, library=library, paths=paths)
    assert window.stack.count() == 3
    assert window.download_page is not None
    assert window.gallery_page is not None
    assert window.settings_page is not None
    window.engine.shutdown()
    window.close()


def test_download_page_add_requires_url(qapp, paths, settings_store, library):
    engine = DownloadEngine(Settings(), paths, library)
    page = DownloadPage(engine, settings_store, paths)
    page.url_edit.setText("not a url")
    page._add_current()
    assert engine.jobs() == []
    engine.shutdown()


def test_gallery_lists_entry(qapp, paths, settings_store, library, tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"x" * 100)
    library.add_download(url="https://example.com", title="Clip", kind="video", path=f)
    page = GalleryPage(library, paths, settings_store)
    page.refresh()
    assert page.grid.count() == 1
    page.filter_combo.setCurrentText("Audio")
    assert page.grid.count() == 0
    page.filter_combo.setCurrentText("Videos")
    assert page.grid.count() == 1
    page.search.setText("clip")
    assert page.grid.count() == 1
    page.search.setText("zzz")
    assert page.grid.count() == 0


def test_settings_page_saves(qapp, paths, settings_store, library):
    page = SettingsPage(settings_store, paths, lambda: None)
    page.mode_combo.setCurrentText("Audio")
    assert settings_store.settings.mode == "audio"
    page.theme_combo.setCurrentText("Light")
    assert settings_store.settings.theme == "light"
    page.workers.setValue(5)
    assert settings_store.settings.concurrent_downloads == 5
