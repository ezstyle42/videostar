import time
from pathlib import Path

import pytest

from videostar.downloader import DownloadEngine, DownloadJob, JobState, parse_urls
from videostar.settings import Settings

TEST_VIDEO = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"


def make_engine(paths, library, settings=None, workers=1):
    s = settings or Settings(download_dir=str(paths.downloads_dir))
    return DownloadEngine(settings=s, paths=paths, library=library, max_workers=workers)


def wait_for(job, engine, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if job.state in (JobState.DONE, JobState.ERROR, JobState.CANCELLED):
            return job.state
        time.sleep(0.1)
    return job.state


def test_parse_urls():
    text = "check this https://example.com/a and https://youtu.be/b?t=3 out"
    assert parse_urls(text) == ["https://example.com/a", "https://youtu.be/b?t=3"]
    assert parse_urls("no urls here") == []


def test_build_ydl_opts_video(paths, library):
    engine = make_engine(paths, library, Settings(download_dir=str(paths.downloads_dir), quality="720p"))
    job = DownloadJob(url=TEST_VIDEO, kind="video")
    opts = engine.build_ydl_opts(job, paths.videos_dir)
    assert "height<=?720" in opts["format"]
    assert opts["paths"]["home"] == str(paths.videos_dir)
    assert opts["overwrites"] is True


def test_build_ydl_opts_audio(paths, library):
    engine = make_engine(paths, library, Settings(download_dir=str(paths.downloads_dir), audio_format="flac"))
    job = DownloadJob(url=TEST_VIDEO, kind="audio")
    opts = engine.build_ydl_opts(job, paths.audio_dir)
    assert opts["format"] == "bestaudio/best"
    pp = opts["postprocessors"][0]
    assert pp["key"] == "FFmpegExtractAudio"
    assert pp["preferredcodec"] == "flac"


def test_build_ydl_opts_uses_cookies_if_present(paths, library):
    paths.cookies_file.write_text("# Netscape HTTP Cookie File\n")
    engine = make_engine(paths, library)
    opts = engine.build_ydl_opts(DownloadJob(url=TEST_VIDEO, kind="video"), paths.videos_dir)
    assert opts["cookiefile"] == str(paths.cookies_file)


def test_queue_and_cancel(paths, library):
    engine = make_engine(paths, library, workers=1)
    job = engine.queue_job("https://example.com/never-resolves", kind="video")
    assert job.state in (JobState.QUEUED, JobState.FETCHING, JobState.DOWNLOADING)
    engine.cancel_job(job)
    engine.shutdown()


def test_clear_finished(paths, library):
    engine = make_engine(paths, library)
    job = DownloadJob(url="https://example.com/x", kind="video", state=JobState.DONE)
    engine._jobs.append(job)
    engine.clear_finished()
    assert engine.jobs() == []


@pytest.mark.network
def test_real_download_video(paths, library):
    pytest.importorskip("yt_dlp")
    from videostar import bundled

    if not bundled.ffmpeg_available():
        pytest.skip("ffmpeg not available")
    engine = make_engine(paths, library)
    finished = []
    engine.signals.job_finished.connect(lambda j: finished.append(j))
    job = engine.queue_job(TEST_VIDEO, kind="video")
    state = wait_for(job, engine, timeout=120)
    engine.shutdown()
    assert state == JobState.DONE, job.error
    assert Path(job.file_path).exists()
    assert len(library) == 1
    entry = library.all()[0]
    assert entry.kind == "video"
    assert entry.title
    assert entry.size > 0
    assert job.entry_id == entry.id


@pytest.mark.network
def test_real_download_audio(paths, library):
    pytest.importorskip("yt_dlp")
    from videostar import bundled

    if not bundled.ffmpeg_available():
        pytest.skip("ffmpeg not available")
    settings = Settings(download_dir=str(paths.downloads_dir), audio_format="best", mode="audio")
    engine = make_engine(paths, library, settings)
    job = engine.queue_job("https://download.samplelib.com/mp3/sample-3s.mp3", kind="audio")
    state = wait_for(job, engine, timeout=120)
    engine.shutdown()
    assert state == JobState.DONE, job.error
    assert Path(job.file_path).exists()
    assert library.all()[0].kind == "audio"
