
from videostar.library import LibraryEntry, LibraryStore


def make_entry(library, tmp_path, name="song.mp3", kind="audio", title="Song"):
    f = tmp_path / name
    f.write_bytes(b"fake media bytes")
    return library.add_download(url="https://example.com/x", title=title, kind=kind, path=f)


def test_add_and_list(library, tmp_path):
    e = make_entry(library, tmp_path)
    assert len(library) == 1
    assert library.get(e.id).title == "Song"
    assert library.get(e.id).exists


def test_persistence(library, paths, tmp_path):
    make_entry(library, tmp_path)
    reloaded = LibraryStore(paths.library_file)
    assert len(reloaded) == 1
    assert reloaded.all()[0].kind == "audio"


def test_remove_with_file(library, tmp_path):
    e = make_entry(library, tmp_path)
    assert e.file_path.exists()
    assert library.remove(e.id, delete_file=True)
    assert not e.file_path.exists()
    assert len(library) == 0


def test_remove_missing_id(library):
    assert library.remove("nope") is False


def test_prune_missing(library, tmp_path):
    e = make_entry(library, tmp_path)
    e.file_path.unlink()
    assert library.prune_missing() == 1
    assert len(library) == 0


def test_filter_by_kind_and_query(library, tmp_path):
    make_entry(library, tmp_path, "a.mp3", "audio", "Cool Song")
    make_entry(library, tmp_path, "b.mp4", "video", "Cool Video")
    make_entry(library, tmp_path, "c.mp3", "audio", "Other")
    assert len(library.filter(kind="audio")) == 2
    assert len(library.filter(kind="video")) == 1
    assert len(library.filter(query="cool")) == 2
    assert len(library.filter(query="song")) == 1


def test_scan_directory_imports_media(library, tmp_path):
    d = tmp_path / "imports"
    (d / "sub").mkdir(parents=True)
    (d / "one.mp4").write_bytes(b"x")
    (d / "sub" / "two.mp3").write_bytes(b"x")
    (d / "notes.txt").write_text("not media")
    assert library.scan_directory(d) == 2
    kinds = sorted(e.kind for e in library)
    assert kinds == ["audio", "video"]


def test_scan_directory_skips_tracked(library, tmp_path):
    d = tmp_path / "imports"
    d.mkdir()
    (d / "one.mp4").write_bytes(b"x")
    assert library.scan_directory(d) == 1
    assert library.scan_directory(d) == 0


def test_newest_first(library, tmp_path):
    import time

    e1 = make_entry(library, tmp_path, "a.mp3", title="old")
    e1.added_at = time.time() - 100
    e2 = make_entry(library, tmp_path, "b.mp3", title="new")
    e2.added_at = time.time()
    library._save()
    assert library.all()[0].title == "new"


def test_entry_roundtrip_dict():
    e = LibraryEntry(id="x", url="u", title="t", kind="video", path="/tmp/a.mp4")
    e2 = LibraryEntry.from_dict(e.to_dict())
    assert e2 == e
    # unknown keys ignored
    e3 = LibraryEntry.from_dict({**e.to_dict(), "mystery": 1})
    assert e3.id == "x"
