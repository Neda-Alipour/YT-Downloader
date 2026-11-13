import os
import re
import threading
import traceback
from typing import Callable, Optional, Dict, Any, List

import yt_dlp
from .ffmpeg_helper import get_ffmpeg_location, get_ffmpeg_path

class DownloadCancelledException(Exception):
    """Raised when the user cancels the download."""
    pass

class YTDLPLogger:
    """Redirects yt-dlp internal logs to a callback function."""
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        self.log_callback = log_callback

    def debug(self, msg: str):
        if self.log_callback and not msg.startswith('[download]'):
            self.log_callback("DEBUG", msg)

    def info(self, msg: str):
        if self.log_callback:
            self.log_callback("INFO", msg)

    def warning(self, msg: str):
        if self.log_callback:
            self.log_callback("WARNING", msg)

    def error(self, msg: str):
        if self.log_callback:
            self.log_callback("ERROR", msg)


class Downloader:
    """Manages yt-dlp video/audio downloads in background threads."""
    def __init__(self):
        self.current_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        self.active_ydl: Optional[yt_dlp.YoutubeDL] = None

    def cancel(self):
        """Signals current download to abort."""
        self._cancel_requested = True

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    @staticmethod
    def fetch_info(url: str, cookies_browser: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts metadata for a URL without downloading media.
        Can inspect single videos or playlists.
        """
        ydl_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
        }
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc

        if cookies_browser and cookies_browser.lower() != 'none':
            ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)

        if proxy and proxy.strip():
            ydl_opts['proxy'] = proxy.strip()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return ydl.sanitize_info(info)

    def download_async(
        self,
        urls: List[str],
        output_dir: str,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
        done_callback: Optional[Callable[[bool, Optional[str]], None]] = None,
    ):
        """Launches a download job in a separate worker thread."""
        self._cancel_requested = False

        def _worker():
            success = False
            error_message = None
            try:
                self._run_download(urls, output_dir, options, progress_callback, log_callback)
                success = True
            except DownloadCancelledException:
                error_message = "Download cancelled by user."
                if log_callback:
                    log_callback("WARNING", "Download cancelled by user.")
            except Exception as e:
                error_message = str(e)
                if log_callback:
                    log_callback("ERROR", f"Download failed: {traceback.format_exc()}")
            finally:
                if done_callback:
                    done_callback(success, error_message)

        self.current_thread = threading.Thread(target=_worker, daemon=True)
        self.current_thread.start()

    def _run_download(
        self,
        urls: List[str],
        output_dir: str,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        log_callback: Optional[Callable[[str, str], None]],
    ):
        os.makedirs(output_dir, exist_ok=True)
        outtmpl = os.path.join(output_dir, '%(title)s.%(ext)s')

        # Build options dictionary
        media_type = options.get('media_type', 'video')  # 'video' or 'audio'
        quality = options.get('quality', 'best')         # 'best', '2160', '1440', '1080', '720', '480', '360'
        container = options.get('container', 'mp4')      # 'mp4', 'mkv', 'webm' or audio 'mp3', 'm4a', 'flac', 'wav'
        embed_subs = options.get('embed_subtitles', False)
        sub_langs = options.get('subtitle_langs', ['en'])
        embed_thumb = options.get('embed_thumbnail', False)
        embed_meta = options.get('embed_metadata', True)
        rate_limit = options.get('rate_limit', None)     # bytes/sec or None
        cookies_browser = options.get('cookies_browser', None)
        proxy = options.get('proxy', None)
        playlist_items = options.get('playlist_items', None) # e.g. "1,2,5-8"

        ydl_opts: Dict[str, Any] = {
            'outtmpl': outtmpl,
            'logger': YTDLPLogger(log_callback),
            'nocheckcertificate': options.get('ignore_ssl', False),
            'updatetime': False,
            # Robustness: ignore non-fatal warnings (e.g. missing subtitle track or 429 on auto-subs)
            # so the video download completes successfully without failing
            'ignoreerrors': True,
        }

        # FFmpeg and FFprobe configuration
        ffmpeg_loc = get_ffmpeg_location()
        if ffmpeg_loc:
            ydl_opts['ffmpeg_location'] = ffmpeg_loc
            if log_callback:
                log_callback("INFO", f"Using FFmpeg/FFprobe location: {ffmpeg_loc}")
        else:
            if log_callback:
                log_callback("WARNING", "FFmpeg not detected! Some conversions or quality merges may be limited.")

        # Rate limiting
        if rate_limit:
            ydl_opts['ratelimit'] = rate_limit

        # Cookies & Proxy
        if cookies_browser and cookies_browser.lower() != 'none':
            ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
            if log_callback:
                log_callback("INFO", f"Extracting cookies from browser: {cookies_browser}")

        if proxy and proxy.strip():
            ydl_opts['proxy'] = proxy.strip()

        # Playlist items range if specified
        if playlist_items:
            ydl_opts['playlist_items'] = str(playlist_items)

        # Postprocessors list
        postprocessors: List[Dict[str, Any]] = []

        if media_type == 'audio':
            # Audio-only extraction
            ydl_opts['format'] = 'bestaudio/best'
            audio_codec = container.lower() if container else 'mp3'
            audio_quality = options.get('audio_quality', '320')  # kbps
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_codec,
                'preferredquality': audio_quality,
            })
        else:
            # Video format selection
            if quality == 'best':
                format_spec = 'bestvideo+bestaudio/best'
            else:
                height = quality.replace('p', '')
                format_spec = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'

            ydl_opts['format'] = format_spec
            ydl_opts['merge_output_format'] = container.lower() if container else 'mp4'

        # Subtitles configuration
        if embed_subs:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            
            # Clean and filter subtitle languages.
            # Never set allsubtitles=True or request every auto-language as that causes HTTP 429 Too Many Requests
            cleaned_langs = [
                lang.strip() for lang in sub_langs 
                if lang.strip() and lang.strip().lower() != 'all'
            ]
            if not cleaned_langs:
                cleaned_langs = ['en', 'en.*']
            
            ydl_opts['subtitleslangs'] = cleaned_langs
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
                'already_have_subtitle': False
            })

        # Metadata & Chapters
        if embed_meta:
            postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True, 'add_metadata': True})

        # Thumbnail embedding (requires ffprobe & ffmpeg)
        if embed_thumb and ffmpeg_loc:
            ydl_opts['writethumbnail'] = True
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            })

        ydl_opts['postprocessors'] = postprocessors

        # Progress hook
        def _hook(d: Dict[str, Any]):
            if self._cancel_requested:
                raise DownloadCancelledException("Download aborted by user request.")

            if progress_callback:
                progress_callback(d)

        ydl_opts['progress_hooks'] = [_hook]

        # Post-processor hook for status updates
        def _post_hook(d: Dict[str, Any]):
            if self._cancel_requested:
                raise DownloadCancelledException("Download aborted by user request.")
            status = d.get('status')
            pp_name = d.get('postprocessor')
            if log_callback:
                log_callback("INFO", f"Processing: {pp_name} -> {status}")

        ydl_opts['postprocessor_hooks'] = [_post_hook]

        # Allow custom yt-dlp arguments passed as extra dict
        extra_opts = options.get('extra_opts')
        if isinstance(extra_opts, dict):
            ydl_opts.update(extra_opts)

        self.active_ydl = yt_dlp.YoutubeDL(ydl_opts)
        with self.active_ydl as ydl:
            ydl.download(urls)
