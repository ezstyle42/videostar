import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from videostar.library import LibraryStore  # noqa: E402
from videostar.paths import AppPaths  # noqa: E402
from videostar.settings import SettingsStore  # noqa: E402


@pytest.fixture()
def paths(tmp_path):
    p = AppPaths(
        config_root=tmp_path / "config",
        data_root=tmp_path / "data",
        cache_root=tmp_path / "cache",
    )
    p.ensure_dirs()
    return p


@pytest.fixture()
def settings_store(paths):
    return SettingsStore(paths.settings_file)


@pytest.fixture()
def library(paths):
    return LibraryStore(paths.library_file)
