# ⚡ YT-DLP Media Downloader for Windows 11

A modern, professional desktop video and audio downloader for Windows 11 built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp) with an integrated FFmpeg engine.

[![Release](https://img.shields.io/github/v/release/Neda-Alipour/YT-Downloader?include_prereleases&style=flat-square&color=0078D4&label=Latest%20Release)](../../releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?style=flat-square&logo=windows)](../../releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## 📥 Download Standalone App (No Installation Needed)

If you just want to use the app, **you do not need Python or FFmpeg installed**:

👉 **[Download the Latest Release (`YT-Downloader.exe`)](../../releases/latest)**

1. Download `YT-Downloader.exe` from the latest release.
2. Double-click to run. (The `.exe` is 100% self-contained with bundled FFmpeg & FFprobe).

---

## 🌟 Key Features

- **Windows 11 Fluent UI**: Clean, modern dark/light mode interface designed with Fluent UI principles, rounded cards, and high-DPI Segoe UI typography.
- **Standalone Portable App**: Single `.exe` bundle with zero external dependencies.
- **Integrated FFmpeg & FFprobe Engine**: Automatically merges separate video and audio streams (1080p, 1440p, 4K, 8K), extracts audio (MP3, FLAC, M4A), and embeds cover thumbnails and chapter metadata.
- **Quality & Resolution Selection**:
  - **Video**: Best Available, 4K (2160p), 2K (1440p), 1080p Full HD, 720p HD, 480p, 360p.
  - **Containers**: MP4, MKV, WEBM.
  - **Audio Extraction**: MP3, M4A, WAV, FLAC, OPUS with custom bitrates (320kbps, 256kbps, 192kbps, 128kbps).
- **YouTube Playlist & Batch Downloader**:
  - Rapid playlist inspection displaying all videos, titles, and durations without downloading upfront.
  - Granular selection: Checkboxes for individual videos, "Select All", "Deselect All", or index range expressions (e.g., `1-5, 8, 12-15`).
  - Batch progress tracking with item counters and current download metrics.
- **Metadata & Subtitles**:
  - Embed subtitles (with customizable language preferences and auto-generated subtitle support). Gracefully handles missing subtitles without failing.
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

## 🛠️ Running from Source (For Developers)

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone and Install Dependencies