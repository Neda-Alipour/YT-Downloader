import os
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.components.video_card import VideoCard
from core.downloader import Downloader

class SingleDownloadTab(ctk.CTkScrollableFrame):
    """
    Tab for downloading individual videos with quality, format, and metadata controls.
    """
    def __init__(self, master, downloader: Downloader, get_settings: Callable[[], Dict[str, Any]], log_callback: Callable[[str, str], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.downloader = downloader
        self.get_settings = get_settings
        self.log_callback = log_callback
        self.cached_info: Optional[Dict[str, Any]] = None
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. URL Input Section
        url_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        url_frame.pack(fill="x", padx=10, pady=(0, 10))

        url_label = ctk.CTkLabel(url_frame, text="Video URL", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        url_label.pack(anchor="w", padx=14, pady=(10, 4))

        input_row = ctk.CTkFrame(url_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste YouTube, Vimeo, Twitter/X, TikTok, or other video URL here...",
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.paste_btn = ctk.CTkButton(
            input_row,
            text="📋 Paste",
            width=80,
            height=36,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._on_paste
        )
        self.paste_btn.pack(side="left", padx=(0, 8))

        self.analyze_btn = ctk.CTkButton(
            input_row,
            text="🔍 Analyze",
            width=95,
            height=36,
            fg_color="#0078D4",
            hover_color="#106EBE",
            command=self._on_analyze
        )
        self.analyze_btn.pack(side="left")

        # 2. Video Preview Card
        self.video_card = VideoCard(self)
        self.video_card.pack(fill="x", padx=10, pady=(0, 10))

        # 3. Format & Quality Settings Card
        opt_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        opt_frame.pack(fill="x", padx=10, pady=(0, 10))

        opt_title = ctk.CTkLabel(opt_frame, text="Download Options & Quality", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        opt_title.pack(anchor="w", padx=14, pady=(10, 6))

        # Media Type (Video vs Audio)
        type_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        type_row.pack(fill="x", padx=14, pady=(0, 8))

        type_label = ctk.CTkLabel(type_row, text="Media Type:", width=110, anchor="w", font=ctk.CTkFont(size=12))
        type_label.pack(side="left")

        self.type_seg = ctk.CTkSegmentedButton(
            type_row,
            values=["Video (Video + Audio)", "Audio Only (Extract MP3/FLAC)"],
            command=self._on_type_changed
        )
        self.type_seg.set("Video (Video + Audio)")
        self.type_seg.pack(side="left", fill="x", expand=True)

        # Quality & Container Row
        qc_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        qc_row.pack(fill="x", padx=14, pady=(0, 8))

        self.quality_label = ctk.CTkLabel(qc_row, text="Resolution:", width=110, anchor="w", font=ctk.CTkFont(size=12))
        self.quality_label.pack(side="left")

        self.quality_combo = ctk.CTkComboBox(
            qc_row,
            values=["Best Available", "4K (2160p)", "2K (1440p)", "1080p Full HD", "720p HD", "480p", "360p"],
            width=160
        )
        self.quality_combo.set("1080p Full HD")
        self.quality_combo.pack(side="left", padx=(0, 16))

        container_label = ctk.CTkLabel(qc_row, text="Format:", width=60, anchor="w", font=ctk.CTkFont(size=12))
        container_label.pack(side="left")

        self.container_combo = ctk.CTkComboBox(
            qc_row,
            values=["mp4", "mkv", "webm"],
            width=120
        )
        self.container_combo.set("mp4")
        self.container_combo.pack(side="left")

        # Toggles Row: Subtitles, Thumbnail, Metadata
        toggles_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        toggles_row.pack(fill="x", padx=14, pady=(4, 12))

        self.meta_check = ctk.CTkCheckBox(toggles_row, text="Embed Metadata & Chapters")
        self.meta_check.select()
        self.meta_check.pack(side="left", padx=(0, 20))

        self.thumb_check = ctk.CTkCheckBox(toggles_row, text="Embed Thumbnail")
        self.thumb_check.select()
        self.thumb_check.pack(side="left", padx=(0, 20))

        self.subs_check = ctk.CTkCheckBox(toggles_row, text="Embed Subtitles")
        self.subs_check.pack(side="left")

        # 4. Save Location Card
        dest_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        dest_frame.pack(fill="x", padx=10, pady=(0, 10))

        dest_title = ctk.CTkLabel(dest_frame, text="Save Location", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        dest_title.pack(anchor="w", padx=14, pady=(10, 4))

        dest_row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_row.pack(fill="x", padx=14, pady=(0, 12))

        default_dl = str(Path.home() / "Downloads")
        self.dest_entry = ctk.CTkEntry(dest_row, height=36, font=ctk.CTkFont(family="Segoe UI", size=12))
        self.dest_entry.insert(0, default_dl)
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            dest_row,
            text="📁 Browse",
            width=80,
            height=36,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._on_browse
        )
        browse_btn.pack(side="left", padx=(0, 8))

        open_btn = ctk.CTkButton(
            dest_row,
            text="↗ Open",
            width=70,
            height=36,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._on_open_folder
        )
        open_btn.pack(side="left")

        # 5. Download Progress & Actions Section
        action_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        action_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(action_frame, height=12, fg_color=("#E0E0E0", "#181818"), progress_color="#0078D4")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=14, pady=(14, 6))

        # Status text
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="Ready to download",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#666666", "#A0A0A0"),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 10))

        # Action Buttons
        btn_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 14))

        self.start_btn = ctk.CTkButton(
            btn_row,
            text="⬇ Start Download",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            fg_color="#0078D4",
            hover_color="#106EBE",
            command=self._on_start_download
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            btn_row,
            text="✖ Cancel",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=40,
            width=100,
            fg_color="#C42B1C",
            hover_color="#A82315",
            state="disabled",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="left")

    def _on_paste(self):
        try:
            clipboard = self.clipboard_get()
            if clipboard:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clipboard.strip())
        except Exception:
            pass

    def _on_type_changed(self, value):
        if "Audio Only" in value:
            self.quality_label.configure(text="Audio Bitrate:")
            self.quality_combo.configure(values=["320 kbps (High Quality)", "256 kbps", "192 kbps (Standard)", "128 kbps"])
            self.quality_combo.set("320 kbps (High Quality)")
            self.container_combo.configure(values=["mp3", "m4a", "wav", "flac", "opus"])
            self.container_combo.set("mp3")
            self.subs_check.configure(state="disabled")
        else:
            self.quality_label.configure(text="Resolution:")
            self.quality_combo.configure(values=["Best Available", "4K (2160p)", "2K (1440p)", "1080p Full HD", "720p HD", "480p", "360p"])
            self.quality_combo.set("1080p Full HD")
            self.container_combo.configure(values=["mp4", "mkv", "webm"])
            self.container_combo.set("mp4")
            self.subs_check.configure(state="normal")

    def _on_browse(self):
        folder = filedialog.askdirectory(initialdir=self.dest_entry.get())
        if folder:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, os.path.normpath(folder))

    def _on_open_folder(self):
        folder = self.dest_entry.get()
        if os.path.isdir(folder):
            os.startfile(folder)
        else:
            messagebox.showwarning("Folder Not Found", "The destination directory does not exist yet.")

    def _on_analyze(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter or paste a valid video URL.")
            return

        self.analyze_btn.configure(state="disabled", text="⏳ Analyzing...")
        self.status_label.configure(text="Fetching video metadata...")

        def _task():
            settings = self.get_settings()
            try:
                info = Downloader.fetch_info(
                    url,
                    cookies_browser=settings.get('cookies_browser'),
                    proxy=settings.get('proxy')
                )
                self.cached_info = info
                self.after(0, lambda: self.video_card.update_info(info))
                self.after(0, lambda: self.status_label.configure(text="Analysis complete. Ready to download."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Analysis Error", f"Failed to extract video info:\n{e}"))
                self.after(0, lambda: self.status_label.configure(text="Failed to analyze video."))
            finally:
                self.after(0, lambda: self.analyze_btn.configure(state="normal", text="🔍 Analyze"))

        threading.Thread(target=_task, daemon=True).start()

    def _on_start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a valid video URL.")
            return

        dest_dir = self.dest_entry.get().strip()
        if not dest_dir:
            messagebox.showwarning("Destination Required", "Please choose a save folder.")
            return

        settings = self.get_settings()

        # Parse quality
        q_val = self.quality_combo.get()
        quality_map = {
            "Best Available": "best",
            "4K (2160p)": "2160",
            "2K (1440p)": "1440",
            "1080p Full HD": "1080",
            "720p HD": "720",
            "480p": "480",
            "360p": "360",
            "320 kbps (High Quality)": "320",
            "256 kbps": "256",
            "192 kbps (Standard)": "192",
            "128 kbps": "128"
        }
        quality_code = quality_map.get(q_val, "best")

        is_audio = "Audio Only" in self.type_seg.get()
        media_type = "audio" if is_audio else "video"

        options: Dict[str, Any] = {
            'media_type': media_type,
            'quality': quality_code,
            'container': self.container_combo.get(),
            'audio_quality': quality_code if is_audio else '320',
            'embed_metadata': bool(self.meta_check.get()),
            'embed_thumbnail': bool(self.thumb_check.get()),
            'embed_subtitles': bool(self.subs_check.get()),
            'subtitle_langs': settings.get('subtitle_langs', ['en', 'all']),
            'rate_limit': settings.get('rate_limit'),
            'cookies_browser': settings.get('cookies_browser'),
            'proxy': settings.get('proxy'),
            'extra_opts': settings.get('extra_opts'),
        }

        self.is_downloading = True
        self.start_btn.configure(state="disabled", text="⏳ Downloading...")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing download...")

        self.downloader.download_async(
            urls=[url],
            output_dir=dest_dir,
            options=options,
            progress_callback=self._on_progress_update,
            log_callback=self.log_callback,
            done_callback=self._on_download_done
        )

    def _on_progress_update(self, d: Dict[str, Any]):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0

            percent = (downloaded / total) if total > 0 else 0
            speed_mb = (speed / (1024 * 1024)) if speed else 0
            down_mb = downloaded / (1024 * 1024)
            tot_mb = total / (1024 * 1024) if total > 0 else 0

            eta_min, eta_sec = divmod(int(eta), 60)
            eta_str = f"{eta_min:02d}:{eta_sec:02d}"

            status_text = f"Downloading: {percent * 100:.1f}% | {down_mb:.1f}/{tot_mb:.1f} MB | Speed: {speed_mb:.2f} MB/s | ETA: {eta_str}"

            self.after(0, lambda: self.progress_bar.set(percent))
            self.after(0, lambda: self.status_label.configure(text=status_text))
        elif status == 'finished':
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_label.configure(text="Processing/merging video streams with FFmpeg..."))

    def _on_download_done(self, success: bool, error_msg: Optional[str]):
        self.is_downloading = False
        def _cleanup():
            self.start_btn.configure(state="normal", text="⬇ Start Download")
            self.cancel_btn.configure(state="disabled")
            if success:
                self.progress_bar.set(1.0)
                self.status_label.configure(text="✔ Download completed successfully!")
                messagebox.showinfo("Success", "Download finished successfully!")
            else:
                self.status_label.configure(text=f"✖ {error_msg or 'Download failed'}")
                if error_msg and "cancelled" not in error_msg.lower():
                    messagebox.showerror("Download Error", f"An error occurred:\n{error_msg}")

        self.after(0, _cleanup)

    def _on_cancel(self):
        if self.is_downloading:
            self.status_label.configure(text="Cancelling download...")
            self.downloader.cancel()
            self.cancel_btn.configure(state="disabled")
