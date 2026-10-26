
from videostar import bundled


def test_find_ffmpeg_returns_path_or_none():
    result = bundled.find_ffmpeg()
    if result is not None:
        from pathlib import Path

        assert Path(result).exists()


def test_find_js_runtime_shape():
    result = bundled.find_js_runtime()
    if result is not None:
        name, path = result
        assert name == "deno"
        from pathlib import Path

        assert Path(path).exists()


def test_environment_for_yt_dlp_has_path():
    env = bundled.environment_for_yt_dlp()
    assert "PATH" in env


def test_is_frozen_false_in_dev():
    assert bundled.is_frozen() is False
