import io
import urllib.request
import threading
from typing import Optional, Dict, Any
from PIL import Image, ImageTk
import customtkinter as ctk

class VideoCard(ctk.CTkFrame):
    """
    A modern card displaying video preview:
    Thumbnail, title, uploader, duration, and metrics.
    """
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=("#F3F3F3", "#202020"),
            border_width=1,
            border_color=("#E5E5E5", "#2D2D2D"),
            **kwargs
        )
        self._build_ui()
        self.reset()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # Thumbnail container
        self.thumb_label = ctk.CTkLabel(
            self,
            text="",
            width=160,
            height=90,
            fg_color=("#E0E0E0", "#181818"),
            corner_radius=6
        )
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=12, pady=12, sticky="nw")

        # Title Label
        self.title_label = ctk.CTkLabel(
            self,
            text="No video analyzed yet",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w",
            justify="left",
            wraplength=480
        )
        self.title_label.grid(row=0, column=1, padx=(0, 12), pady=(12, 2), sticky="ew")

        # Uploader / Channel
        self.channel_label = ctk.CTkLabel(
            self,
            text="Channel: —",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("#666666", "#A0A0A0"),
            anchor="w"
        )
        self.channel_label.grid(row=1, column=1, padx=(0, 12), pady=(0, 4), sticky="w")

        # Badges row: Duration, Views
        self.badges_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.badges_frame.grid(row=2, column=1, padx=(0, 12), pady=(0, 10), sticky="w")

        self.duration_badge = ctk.CTkLabel(
            self.badges_frame,
            text="⏱ --:--",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#0078D4", "#0078D4"),
            text_color="#FFFFFF",
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.duration_badge.pack(side="left", padx=(0, 8))

        self.views_badge = ctk.CTkLabel(
            self.badges_frame,
            text="👁 -- views",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=("#EAEAEA", "#2E2E2E"),
            text_color=("#444444", "#CCCCCC"),
            corner_radius=4,
            padx=6,
            pady=2
        )
        self.views_badge.pack(side="left")

    def reset(self):
        self.title_label.configure(text="Enter a URL and click 'Analyze' to preview video details.")
        self.channel_label.configure(text="Channel: —")
        self.duration_badge.configure(text="⏱ --:--")
        self.views_badge.configure(text="👁 -- views")
        self._set_placeholder_thumbnail()

    def _set_placeholder_thumbnail(self):
        # 16:9 placeholder
        img = Image.new("RGB", (160, 90), color=(40, 40, 40))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(160, 90))
        self.thumb_label.configure(image=ctk_img, text="No Preview")

    def update_info(self, info: Dict[str, Any]):
        title = info.get("title", "Untitled Video")
        uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"
        duration_sec = info.get("duration") or 0
        minutes, seconds = divmod(int(duration_sec), 60)
        hours, minutes = divmod(minutes, 60)
        dur_str = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

        views = info.get("view_count")
        if views is not None:
            if views >= 1_000_000:
                views_str = f"{views / 1_000_000:.1f}M views"
            elif views >= 1_000:
                views_str = f"{views / 1_000:.1f}K views"
            else:
                views_str = f"{views} views"
        else:
            views_str = "Live / N/A"

        self.title_label.configure(text=title)
        self.channel_label.configure(text=f"Channel: {uploader}")
        self.duration_badge.configure(text=f"⏱ {dur_str}")
        self.views_badge.configure(text=f"👁 {views_str}")

        # Async fetch thumbnail
        thumb_url = info.get("thumbnail")
        if thumb_url:
            threading.Thread(target=self._fetch_thumbnail, args=(thumb_url,), daemon=True).start()

    def _fetch_thumbnail(self, url: str):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                pil_img = Image.open(io.BytesIO(data))
                pil_img = pil_img.resize((160, 90), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 90))
                # Update UI on main thread
                self.after(0, lambda: self.thumb_label.configure(image=ctk_img, text=""))
        except Exception:
            pass
