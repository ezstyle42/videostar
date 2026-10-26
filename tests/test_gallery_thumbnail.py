import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from videostar.ui.gallery_page import GalleryCard, GalleryPage  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def make_png(path: Path, w=64, h=64) -> Path:
    img = QImage(w, h, QImage.Format.Format_RGB32)
    img.fill(0xFF7C5CFF)
    img.save(str(path))
    return path


def test_card_loads_thumbnail_without_crashing(qapp, tmp_path, paths, settings_store, library):
    thumb = make_png(tmp_path / "thumb.jpg")
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x" * 50)
    entry = library.add_download(
        url="https://example.com", title="Clip", kind="video", path=media,
        thumbnail=thumb)
    gallery = GalleryPage(library, paths, settings_store)
    card = GalleryCard(entry, gallery)
    assert not card.thumb.pixmap().isNull(), "thumbnail pixmap should be set"


def test_card_without_thumbnail_does_not_crash(qapp, tmp_path, paths, settings_store, library):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x" * 50)
    entry = library.add_download(url="https://example.com", title="Clip", kind="video", path=media)
    gallery = GalleryPage(library, paths, settings_store)
    card = GalleryCard(entry, gallery)
    assert card.thumb.pixmap() is None or card.thumb.pixmap().isNull()


def test_gallery_refresh_with_existing_entry(qapp, tmp_path, paths, settings_store, library):
    thumb = make_png(tmp_path / "t.png")
    media = tmp_path / "a.mp3"
    media.write_bytes(b"x" * 10)
    library.add_download(url="u", title="Song", kind="audio", path=media, thumbnail=thumb)
    gallery = GalleryPage(library, paths, settings_store)
    gallery.refresh()
    assert gallery.grid.count() == 1
