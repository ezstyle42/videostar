# VideoStar

A cross-platform **video & audio download** desktop application with a beautiful,
easy-to-navigate interface — powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

![VideoStar](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)
![License](https://img.shields.io/badge/license-Unlicense-green)

## Features

- **Video or audio** — pick per download or set a default; audio is converted to MP3, M4A, FLAC, Opus or WAV.
- **Quality picker** — best, 1080p, 720p, 480p, 360p.
- **Concurrent downloads** — a live queue with progress, speed and ETA; cancel anytime.
- **Library gallery** — every finished download appears as a card with a thumbnail, duration and size. Search, filter by type, open the file or reveal it in your file manager, or import an existing folder of media.
- **Settings are remembered** — download folder, type, quality, theme (dark/light), concurrency, gallery columns, subtitles, metadata/thumbnail embedding, extra yt-dlp options.
- **Self-contained releases** — FFmpeg and a JavaScript runtime (deno) are bundled, so you don't need to install anything. yt-dlp is embedded as a Python package.
- **Playlists & multiple URLs** — paste several links at once.
- **Cookies support** — drop a `cookies.txt` (Netscape format) into the config folder to download age-restricted or members-only content.

## Download

Grab the latest build for your platform from
[Releases](https://github.com/ezstyle42/videostar/releases). One file, no installer,
no dependencies.

| Platform | Artifact |
|---|---|
| Windows (x64) | `videostar-windows-x64.exe` |
| Linux (x64) | `videostar-linux-x64` |
| macOS (Apple Silicon) | `videostar-macos-arm64` |

On macOS you may need to right-click → **Open** the first time (Gatekeeper), and
`brew install ffmpeg` is recommended (the release bundles deno; ffmpeg is used from
the system if present, otherwise the bundled copy).

## Run from source

```bash
git clone https://github.com/ezstyle42/videostar.git
cd videostar
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
python -m videostar
```

FFmpeg is picked up automatically: bundled binary → `PATH` → the `imageio-ffmpeg`
package. Install `ffmpeg` (and optionally `deno` for best YouTube compatibility)
for the smoothest experience.

## Build a release binary

```bash
pip install -e ".[build]"
python scripts/fetch_binaries.py     # downloads ffmpeg + deno into build/binaries
python scripts/build.py              # PyInstaller one-file build into dist/
```

Releases are built automatically for Windows, Linux and macOS by
[GitHub Actions](.github/workflows/release.yml) on every `v*` tag.

## Project layout

```
videostar/
  paths.py        per-user config/data/cache locations (Win/macOS/Linux)
  settings.py     persistent JSON settings store
  library.py      JSON-backed gallery of downloaded media
  downloader.py   threaded yt-dlp engine with progress signals
  bundled.py      finds yt-dlp / ffmpeg / deno (bundled, PATH or wheels)
  metadata.py     thumbnails + duration probing
  ui/             PySide6 interface (main window, download, gallery, settings)
scripts/
  fetch_binaries.py   download ffmpeg + deno for bundling
  build.py            PyInstaller release build
tests/            pytest suite (unit + UI smoke + live network tests)
```

## Tests

```bash
pip install -e ".[dev]"
python -m pytest                 # everything, including live downloads
python -m pytest -m "not network"  # offline only (fast)
```

## Credits

- Download engine: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense)
- UI: [Qt for Python (PySide6)](https://www.qt.io/)
- FFmpeg builds: [johnvansickle.com](https://johnvansickle.com/ffmpeg/) / [BtbN](https://github.com/BtbN/FFmpeg-Builds)
- JavaScript runtime: [deno](https://deno.com/)

## License

[Unlicense](LICENSE)

## Development

All work happens on PR branches off `main`. See the open pull request for the full application.
