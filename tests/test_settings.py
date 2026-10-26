import json

from videostar.settings import Settings, SettingsStore, quality_to_format


def test_defaults(settings_store):
    s = settings_store.settings
    assert s.mode == "video"
    assert s.audio_format == "mp3"
    assert s.quality == "best"
    assert s.theme == "dark"
    assert s.concurrent_downloads == 2


def test_update_persists(settings_store, paths):
    settings_store.update(mode="audio", audio_format="flac", concurrent_downloads=4)
    reloaded = SettingsStore(paths.settings_file)
    assert reloaded.settings.mode == "audio"
    assert reloaded.settings.audio_format == "flac"
    assert reloaded.settings.concurrent_downloads == 4


def test_unknown_setting_rejected(settings_store):
    try:
        settings_store.update(not_a_setting=1)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")


def test_unknown_keys_preserved(settings_store, paths):
    paths.settings_file.write_text(json.dumps({"mode": "audio", "future_key": 42}))
    store = SettingsStore(paths.settings_file)
    assert store.settings.mode == "audio"
    store.save()
    data = json.loads(paths.settings_file.read_text())
    assert data["future_key"] == 42


def test_corrupt_settings_file_falls_back_to_defaults(settings_store, paths):
    paths.settings_file.write_text("{ not json")
    store = SettingsStore(paths.settings_file)
    assert store.settings == Settings()


def test_quality_to_format():
    assert quality_to_format("best") == "bv*+ba/b"
    assert "height<=?1080" in quality_to_format("1080p")
    assert "height<=?720" in quality_to_format("720p")
    assert "height<=?480" in quality_to_format("480p")
    assert "height<=?360" in quality_to_format("360p")
