import os
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.downloader import Downloader
from core.playlist import extract_playlist_data, parse_range_string, format_indices_to_ytdlp

class PlaylistItemRow(ctk.CTkFrame):
    """A row representing an item in the playlist."""
    def __init__(self, master, item: Dict[str, Any], on_check_changed: Callable[[], None], **kwargs):
        super().__init__(
            master,
            fg_color=("#F3F3F3", "#202020"),
            corner_radius=6,
            border_width=1,
            border_color=("#E5E5E5", "#2D2D2D"),
            **kwargs
        )
        self.item = item
        self.on_check_changed = on_check_changed
        self.is_selected = ctk.BooleanVar(value=True)

        self.grid_columnconfigure(2, weight=1)

        # Checkbox
        self.check = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.is_selected,
            width=24,
            command=self.on_check_changed
        )
        self.check.grid(row=0, column=0, padx=(10, 4), pady=8)

        # Index badge
        idx_text = f"#{item['index']}"
        self.idx_label = ctk.CTkLabel(
            self,
            text=idx_text,
            width=40,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#0078D4"
        )
        self.idx_label.grid(row=0, column=1, padx=(0, 8), pady=8)

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=item['title'],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w",
            justify="left"
        )
        self.title_label.grid(row=0, column=2, padx=(0, 10), pady=8, sticky="ew")

        # Duration badge
        self.dur_label = ctk.CTkLabel(
            self,
            text=item['duration_str'],
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#666666", "#A0A0A0"),
            width=60,
            anchor="e"
        )
        self.dur_label.grid(row=0, column=3, padx=(0, 12), pady=8)


class PlaylistTab(ctk.CTkFrame):
    """
    Tab for inspecting playlists, selecting items, and batch downloading with custom formats.
    """
    def __init__(self, master, downloader: Downloader, get_settings: Callable[[], Dict[str, Any]], log_callback: Callable[[str, str], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.downloader = downloader
        self.get_settings = get_settings
        self.log_callback = log_callback

        self.playlist_data: Optional[Dict[str, Any]] = None
        self.item_rows: List[PlaylistItemRow] = []
        self.is_downloading = False

        self._build_ui()

    def _build_ui(self):
        # 1. URL Bar Frame
        url_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        url_frame.pack(fill="x", padx=10, pady=(0, 10))

        url_label = ctk.CTkLabel(url_frame, text="Playlist URL", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        url_label.pack(anchor="w", padx=14, pady=(10, 4))

        input_row = ctk.CTkFrame(url_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Paste YouTube Playlist URL (e.g. https://www.youtube.com/playlist?list=...)",
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
            text="🔍 Fetch Playlist",
            width=120,
            height=36,
            fg_color="#0078D4",
            hover_color="#106EBE",
            command=self._on_fetch_playlist
        )
        self.analyze_btn.pack(side="left")

        # 2. Playlist Summary & Selection Controls
        self.summary_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        self.summary_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Playlist Header row
        header_row = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10, 4))

        self.title_label = ctk.CTkLabel(
            header_row,
            text="No playlist loaded",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        self.count_badge = ctk.CTkLabel(
            header_row,
            text="0 Videos",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#EAEAEA", "#303030"),
            text_color=("#333333", "#CCCCCC"),
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.count_badge.pack(side="right")

        # Action Toolbar (Select All, Deselect All, Range)
        toolbar_row = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        toolbar_row.pack(fill="x", padx=14, pady=(4, 12))

        self.all_btn = ctk.CTkButton(
            toolbar_row,
            text="Select All",
            width=80,
            height=28,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._select_all
        )
        self.all_btn.pack(side="left", padx=(0, 6))

        self.none_btn = ctk.CTkButton(
            toolbar_row,
            text="Deselect All",
            width=90,
            height=28,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._deselect_all
        )
        self.none_btn.pack(side="left", padx=(0, 14))

        range_label = ctk.CTkLabel(toolbar_row, text="Select Range:", font=ctk.CTkFont(size=12))
        range_label.pack(side="left", padx=(0, 4))

        self.range_entry = ctk.CTkEntry(toolbar_row, placeholder_text="e.g. 1-10, 15", width=120, height=28)
        self.range_entry.pack(side="left", padx=(0, 6))

        self.range_btn = ctk.CTkButton(
            toolbar_row,
            text="Apply Range",
            width=90,
            height=28,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._apply_range
        )
        self.range_btn.pack(side="left")

        self.selection_stat = ctk.CTkLabel(
            toolbar_row,
            text="Selected: 0 / 0",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#0078D4"
        )
        self.selection_stat.pack(side="right")

        # 3. Format & Quality Options
        opt_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        opt_frame.pack(fill="x", padx=10, pady=(0, 10))

        opt_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        opt_row.pack(fill="x", padx=14, pady=10)

        type_lbl = ctk.CTkLabel(opt_row, text="Format:", font=ctk.CTkFont(size=12))
        type_lbl.pack(side="left", padx=(0, 4))

        self.type_combo = ctk.CTkComboBox(
            opt_row,
            values=["Video (MP4)", "Video (MKV)", "Audio Only (MP3)", "Audio Only (FLAC)"],
            width=160,
            command=self._on_format_changed
        )
        self.type_combo.set("Video (MP4)")
        self.type_combo.pack(side="left", padx=(0, 14))

        self.quality_lbl = ctk.CTkLabel(opt_row, text="Resolution:", font=ctk.CTkFont(size=12))
        self.quality_lbl.pack(side="left", padx=(0, 4))

        self.quality_combo = ctk.CTkComboBox(
            opt_row,
            values=["Best Available", "4K (2160p)", "2K (1440p)", "1080p Full HD", "720p HD", "480p", "360p"],
            width=150
        )
        self.quality_combo.set("1080p Full HD")
        self.quality_combo.pack(side="left", padx=(0, 14))

        self.meta_check = ctk.CTkCheckBox(opt_row, text="Embed Metadata")
        self.meta_check.select()
        self.meta_check.pack(side="left", padx=(0, 12))

        self.subs_check = ctk.CTkCheckBox(opt_row, text="Embed Subtitles")
        self.subs_check.pack(side="left")

        # 4. Scrollable Video Items List
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            fg_color=("#F9F9F9", "#242424"),
            corner_radius=10,
            border_width=1,
            border_color=("#E5E5E5", "#2F2F2F"),
            height=200
        )
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Placeholder label in scroll list
        self.empty_label = ctk.CTkLabel(
            self.scroll_list,
            text="Fetch a playlist URL above to display and select individual videos.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#666666", "#A0A0A0")
        )
        self.empty_label.pack(pady=40)

        # 5. Destination & Action Frame
        bottom_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        dest_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        dest_row.pack(fill="x", padx=14, pady=(10, 6))

        default_dl = str(Path.home() / "Downloads")
        self.dest_entry = ctk.CTkEntry(dest_row, height=32, font=ctk.CTkFont(family="Segoe UI", size=12))
        self.dest_entry.insert(0, default_dl)
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            dest_row,
            text="📁 Browse",
            width=80,
            height=32,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._on_browse
        )
        browse_btn.pack(side="left")

        # Progress bar & status
        self.progress_bar = ctk.CTkProgressBar(bottom_frame, height=10, fg_color=("#E0E0E0", "#181818"), progress_color="#0078D4")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=14, pady=(6, 4))

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Ready to download",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#666666", "#A0A0A0"),
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 8))

        # Start / Cancel Buttons
        btn_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        self.start_btn = ctk.CTkButton(
            btn_row,
            text="⬇ Download Selected Videos",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            fg_color="#0078D4",
            hover_color="#106EBE",
            command=self._on_start_download
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            btn_row,
            text="✖ Cancel",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
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

    def _on_format_changed(self, value):
        if "Audio Only" in value:
            self.quality_lbl.configure(text="Audio Quality:")
            self.quality_combo.configure(values=["320 kbps (High)", "256 kbps", "192 kbps", "128 kbps"])
            self.quality_combo.set("320 kbps (High)")
            self.subs_check.configure(state="disabled")
        else:
            self.quality_lbl.configure(text="Resolution:")
            self.quality_combo.configure(values=["Best Available", "4K (2160p)", "2K (1440p)", "1080p Full HD", "720p HD", "480p", "360p"])
            self.quality_combo.set("1080p Full HD")
            self.subs_check.configure(state="normal")

    def _on_browse(self):
        folder = filedialog.askdirectory(initialdir=self.dest_entry.get())
        if folder:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, os.path.normpath(folder))

    def _on_fetch_playlist(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a valid playlist URL.")
            return

        self.analyze_btn.configure(state="disabled", text="⏳ Loading...")
        self.status_label.configure(text="Fetching playlist items (this might take a few moments)...")

        def _task():
            settings = self.get_settings()
            try:
                data = extract_playlist_data(
                    url,
                    cookies_browser=settings.get('cookies_browser'),
                    proxy=settings.get('proxy')
                )
                self.playlist_data = data
                self.after(0, self._render_playlist)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Playlist Error", f"Failed to load playlist:\n{e}"))
                self.after(0, lambda: self.status_label.configure(text="Failed to load playlist."))
            finally:
                self.after(0, lambda: self.analyze_btn.configure(state="normal", text="🔍 Fetch Playlist"))

        threading.Thread(target=_task, daemon=True).start()

    def _render_playlist(self):
        if not self.playlist_data:
            return

        # Clear existing items
        for row in self.item_rows:
            row.destroy()
        self.item_rows.clear()
        self.empty_label.pack_forget()

        # Update header
        title = self.playlist_data.get('title', 'Playlist')
        count = self.playlist_data.get('total_count', 0)
        channel = self.playlist_data.get('uploader', 'Unknown Channel')

        self.title_label.configure(text=f"{title} ({channel})")
        self.count_badge.configure(text=f"{count} Videos")

        # Populate rows
        for item in self.playlist_data.get('entries', []):
            row = PlaylistItemRow(self.scroll_list, item, on_check_changed=self._update_selection_count)
            row.pack(fill="x", pady=2)
            self.item_rows.append(row)

        self._update_selection_count()
        self.status_label.configure(text=f"Loaded {count} videos. Choose videos and click Download.")

    def _update_selection_count(self):
        selected = sum(1 for r in self.item_rows if r.is_selected.get())
        total = len(self.item_rows)
        self.selection_stat.configure(text=f"Selected: {selected} / {total}")

    def _select_all(self):
        for r in self.item_rows:
            r.is_selected.set(True)
        self._update_selection_count()

    def _deselect_all(self):
        for r in self.item_rows:
            r.is_selected.set(False)
        self._update_selection_count()

    def _apply_range(self):
        range_text = self.range_entry.get().strip()
        if not range_text or not self.item_rows:
            return

        selected_indices = parse_range_string(range_text, max_count=len(self.item_rows))
        idx_set = set(selected_indices)

        for r in self.item_rows:
            r.is_selected.set(r.item['index'] in idx_set)

        self._update_selection_count()

    def _on_start_download(self):
        if not self.playlist_data or not self.item_rows:
            messagebox.showwarning("No Playlist", "Please load a playlist first.")
            return

        selected_items = [r.item for r in self.item_rows if r.is_selected.get()]
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one video to download.")
            return

        dest_dir = self.dest_entry.get().strip()
        if not dest_dir:
            messagebox.showwarning("Destination Required", "Please choose a save folder.")
            return

        settings = self.get_settings()
        selected_indices = [item['index'] for item in selected_items]
        playlist_items_str = format_indices_to_ytdlp(selected_indices)

        # Parse format and quality
        fmt_val = self.type_combo.get()
        if "Audio Only (MP3)" in fmt_val:
            media_type = "audio"
            container = "mp3"
        elif "Audio Only (FLAC)" in fmt_val:
            media_type = "audio"
            container = "flac"
        elif "Video (MKV)" in fmt_val:
            media_type = "video"
            container = "mkv"
        else:
            media_type = "video"
            container = "mp4"

        q_val = self.quality_combo.get()
        quality_map = {
            "Best Available": "best",
            "4K (2160p)": "2160",
            "2K (1440p)": "1440",
            "1080p Full HD": "1080",
            "720p HD": "720",
            "480p": "480",
            "360p": "360",
            "320 kbps (High)": "320",
            "256 kbps": "256",
            "192 kbps": "192",
            "128 kbps": "128"
        }
        quality_code = quality_map.get(q_val, "best")

        options: Dict[str, Any] = {
            'media_type': media_type,
            'quality': quality_code,
            'container': container,
            'audio_quality': quality_code if media_type == 'audio' else '320',
            'playlist_items': playlist_items_str,
            'embed_metadata': bool(self.meta_check.get()),
            'embed_subtitles': bool(self.subs_check.get()),
            'subtitle_langs': settings.get('subtitle_langs', ['en', 'all']),
            'rate_limit': settings.get('rate_limit'),
            'cookies_browser': settings.get('cookies_browser'),
            'proxy': settings.get('proxy'),
            'extra_opts': settings.get('extra_opts'),
        }

        # Subdirectory for playlist by playlist title
        playlist_title = self.playlist_data.get('title') or "Playlist"
        # Sanitize folder name
        safe_title = "".join(c for c in playlist_title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        final_dest = os.path.join(dest_dir, safe_title)

        self.is_downloading = True
        self.start_btn.configure(state="disabled", text=f"⏳ Downloading ({len(selected_indices)} videos)...")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text=f"Starting playlist download ({len(selected_indices)} videos)...")

        url = self.url_entry.get().strip()
        self.downloader.download_async(
            urls=[url],
            output_dir=final_dest,
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

            fn = os.path.basename(d.get('filename', ''))
            status_text = f"Downloading: {percent * 100:.1f}% | {down_mb:.1f}/{tot_mb:.1f} MB | Speed: {speed_mb:.2f} MB/s | ETA: {eta_str}\n{fn}"

            self.after(0, lambda: self.progress_bar.set(percent))
            self.after(0, lambda: self.status_label.configure(text=status_text))
        elif status == 'finished':
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_label.configure(text="Finished item, processing stream..."))

    def _on_download_done(self, success: bool, error_msg: Optional[str]):
        self.is_downloading = False
        def _cleanup():
            self.start_btn.configure(state="normal", text="⬇ Download Selected Videos")
            self.cancel_btn.configure(state="disabled")
            if success:
                self.progress_bar.set(1.0)
                self.status_label.configure(text="✔ All selected videos downloaded successfully!")
                messagebox.showinfo("Success", "Playlist download complete!")
            else:
                self.status_label.configure(text=f"✖ {error_msg or 'Download stopped.'}")
                if error_msg and "cancelled" not in error_msg.lower():
                    messagebox.showerror("Error", f"Playlist download ended with error:\n{error_msg}")

        self.after(0, _cleanup)

    def _on_cancel(self):
        if self.is_downloading:
            self.status_label.configure(text="Cancelling playlist download...")
            self.downloader.cancel()
            self.cancel_btn.configure(state="disabled")
