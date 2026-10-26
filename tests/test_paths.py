

def test_ensure_dirs_creates_everything(paths):
    for p in (paths.config_root, paths.data_root, paths.cache_root,
              paths.videos_dir, paths.audio_dir, paths.thumbnails_dir):
        assert p.is_dir(), p


def test_settings_and_library_locations(paths):
    assert paths.settings_file == paths.config_root / "settings.json"
    assert paths.library_file == paths.data_root / "library.json"
    assert paths.videos_dir.name == "videos"
    assert paths.audio_dir.name == "audio"
