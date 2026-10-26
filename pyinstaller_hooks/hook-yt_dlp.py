from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = [
    "yt_dlp.compat._legacy",
    "yt_dlp.compat._deprecated",
    "yt_dlp.utils._legacy",
    "yt_dlp.utils._deprecated",
    "mutagen",
    "brotli",
    "certifi",
    "websockets",
    "requests",
    "urllib3",
    "imageio_ffmpeg",
]
hiddenimports += collect_submodules("websockets")
hiddenimports += collect_submodules("requests")
hiddenimports += collect_submodules("urllib3")
hiddenimports += collect_submodules("yt_dlp_ejs")

datas = collect_data_files("yt_dlp_ejs", includes=["**/*.js"])
datas += collect_data_files("imageio_ffmpeg", includes=["**/ffmpeg*"])
