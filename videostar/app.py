"""Qt application bootstrap."""

from __future__ import annotations

from .paths import get_paths
from .settings import SettingsStore


def run(argv: list[str]) -> int:
    from PySide6.QtWidgets import QApplication

    from .library import LibraryStore
    from .ui.main_window import MainWindow
    from .ui.theme import apply_theme

    app = QApplication(argv)
    app.setApplicationName("VideoStar")
    app.setOrganizationName("videostar")

    paths = get_paths()
    paths.ensure_dirs()
    store = SettingsStore(paths.settings_file)
    library = LibraryStore(paths.library_file)
    library.prune_missing()

    apply_theme(app, store.settings.theme)

    window = MainWindow(settings_store=store, library=library, paths=paths)
    if not store.settings.start_minimized:
        window.show()

    # Single-instance guard: a second launch just re-shows the window.
    app.aboutToQuit.connect(window.shutdown)

    return app.exec()
