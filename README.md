# ⚡ YT-DLP Media Downloader for Windows 11

A modern, professional desktop video and audio downloader for Windows 11 built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp) with an integrated FFmpeg engine.

---

## 🌟 Key Features

- **Windows 11 Fluent UI**: Clean, modern dark/light mode interface designed with Fluent UI principles, rounded geometry, and Segoe UI typography.
- **Standalone `.exe`**: Ready-to-run Windows 11 executable (`dist/YT-Downloader.exe`) with zero prerequisites. Python or external tools do NOT need to be installed on target machines.
- **Integrated FFmpeg Engine**: Bundled static FFmpeg automatically handles 1080p, 1440p, 4K, 8K stream merging, audio extraction (MP3, FLAC, M4A), and thumbnail/chapter embedding.
- **Quality & Resolution Selection**:
  - **Video**: Best Available, 4K (2160p), 2K (1440p), 1080p Full HD, 720p HD, 480p, 360p.
  - **Containers**: MP4, MKV, WEBM.
  - **Audio Extraction**: MP3, M4A, WAV, FLAC, OPUS with adjustable bitrates (320kbps, 256kbps, 192kbps, 128kbps).
- **YouTube Playlist & Batch Downloader**:
  - Instant metadata inspection displaying all playlist items without downloading files upfront.
  - Granular selection: Checkboxes for individual videos, "Select All", "Deselect All", or index range expressions (e.g., `1-5, 8, 12-15`).
  - Batch progress tracking with item counters and current download metrics.
- **Metadata & Subtitles**:
  - Embed subtitles (with customizable language preferences and auto-generated subtitle support).
  - Embed official video thumbnails into audio and video containers.
  - Embed chapter markers and metadata tags.
- **Authentication & Bypassing**:
  - One-click browser cookie extraction (Chrome, Edge, Firefox, Brave, Opera, Vivaldi) for member-only and age-restricted videos.
  - Custom HTTP/SOCKS5 proxy configuration.
  - Configurable download speed limiters.
- **Real-Time Telemetry & Diagnostics**:
  - Live percentage, download speed (MB/s), total file size, and ETA calculation.
  - Live console logs viewer with auto-scroll and clipboard copying.

---

## 🚀 Running the Application

### 1. Standalone Executable (Recommended)
Simply double-click:
```
dist/YT-Downloader.exe
```

### 2. Running from Source
If running in Python 3.10+:
```bash
pip install -r requirements.txt
python app.py
```

### 3. Rebuilding the Executable
To regenerate the standalone `.exe`:
```bash
python build/build_exe.py
```

---

## 📁 Project Architecture

```
ytdlp-gui-windows/
├── app.py                     # High-DPI application entry point
├── requirements.txt           # Python dependencies
├── core/
│   ├── ffmpeg_helper.py       # Auto-locates bundled or system FFmpeg binary
│   ├── downloader.py          # yt-dlp asynchronous download engine & progress hooks
│   └── playlist.py            # Playlist metadata extraction and range parser
├── ui/
│   ├── main_window.py         # Main Fluent window & tab coordinator
│   ├── components/
│   │   └── video_card.py      # Video preview card with thumbnail loader
│   └── tabs/
│       ├── single_download.py # Single video downloader tab
│       ├── playlist_tab.py    # Selective playlist downloader tab
│       ├── settings_tab.py    # Cookies, proxy, speed limits, and FFmpeg status
│       └── logs_tab.py        # Real-time console diagnostics
├── build/
│   ├── app_icon.ico           # Windows application multi-resolution icon
│   ├── create_icon.py         # Script that generated the icon
│   └── build_exe.py           # PyInstaller build automation script
└── dist/
    └── YT-Downloader.exe      # Compiled standalone Windows 11 executable
```
