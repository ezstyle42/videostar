import pytest

from videostar.metadata import download_thumbnail, probe_duration


@pytest.mark.network
def test_download_thumbnail_caches(paths):
    pytest.importorskip("yt_dlp")
    url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
    thumb = download_thumbnail(url, paths.thumbnails_dir, source_url=url)
    # may be None if the site exposes no thumbnail; must not raise
    if thumb is not None:
        assert thumb.exists()
        first = thumb
        again = download_thumbnail(url, paths.thumbnails_dir, source_url=url)
        assert again == first


def test_probe_duration_missing_file(paths):
    assert probe_duration(paths.downloads_dir / "nope.mp3") == 0


@pytest.mark.network
def test_probe_duration_real_mp3(paths):
    pytest.importorskip("yt_dlp")
    import yt_dlp

    target = paths.downloads_dir / "sample.mp3"
    target.parent.mkdir(parents=True, exist_ok=True)
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True,
                           "outtmpl": str(target.with_suffix(".%(ext)s"))}) as ydl:
        ydl.download(["https://download.samplelib.com/mp3/sample-3s.mp3"])
    if not target.exists():
        pytest.skip("download failed")
    duration = probe_duration(target)
    assert 2 <= duration <= 5
