import os
import customtkinter as ctk
from typing import Dict, Any
from core.ffmpeg_helper import get_ffmpeg_path, is_ffmpeg_available

class SettingsTab(ctk.CTkScrollableFrame):
    """
    Settings tab for configuring browser cookies, proxies, speed limits,
    subtitles, custom yt-dlp flags, and viewing FFmpeg engine status.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build_ui()

    def _build_ui(self):
        # 1. FFmpeg Engine Status Card
        ff_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        ff_frame.pack(fill="x", padx=10, pady=(0, 10))

        ff_title = ctk.CTkLabel(ff_frame, text="⚡ Core Media Engine (FFmpeg)", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        ff_title.pack(anchor="w", padx=14, pady=(10, 4))

        ff_path = get_ffmpeg_path()
        is_avail = is_ffmpeg_available()

        ff_info_row = ctk.CTkFrame(ff_frame, fg_color="transparent")
        ff_info_row.pack(fill="x", padx=14, pady=(0, 12))

        status_badge_text = "✔ FFmpeg & FFprobe Ready" if is_avail else "⚠ Engine Not Found"
        status_badge_color = "#107C41" if is_avail else "#D83B01"

        self.ff_status_label = ctk.CTkLabel(
            ff_info_row,
            text=status_badge_text,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=status_badge_color,
            text_color="#FFFFFF",
            corner_radius=4,
            padx=8,
            pady=3
        )
        self.ff_status_label.pack(side="left", padx=(0, 10))

        short_path = ff_path if len(ff_path) < 60 else "..." + ff_path[-55:]
        self.ff_path_label = ctk.CTkLabel(
            ff_info_row,
            text=f"Location: {short_path if ff_path else 'None'}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#666666", "#A0A0A0")
        )
        self.ff_path_label.pack(side="left")

        # 2. Authentication & Browser Cookies
        auth_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        auth_frame.pack(fill="x", padx=10, pady=(0, 10))

        auth_title = ctk.CTkLabel(auth_frame, text="🔑 Authentication & Age-Restricted Content", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        auth_title.pack(anchor="w", padx=14, pady=(10, 4))

        auth_desc = ctk.CTkLabel(
            auth_frame,
            text="Extract cookies from your local browser to download age-restricted, subscriber-only, or private videos.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#666666", "#A0A0A0"),
            anchor="w"
        )
        auth_desc.pack(fill="x", padx=14, pady=(0, 8))

        cookie_row = ctk.CTkFrame(auth_frame, fg_color="transparent")
        cookie_row.pack(fill="x", padx=14, pady=(0, 12))

        cookie_lbl = ctk.CTkLabel(cookie_row, text="Import Cookies From:", width=150, anchor="w", font=ctk.CTkFont(size=12))
        cookie_lbl.pack(side="left")

        self.cookie_combo = ctk.CTkComboBox(
            cookie_row,
            values=["None", "Chrome", "Edge", "Firefox", "Brave", "Opera", "Vivaldi"],
            width=160
        )
        self.cookie_combo.set("None")
        self.cookie_combo.pack(side="left")

        # 3. Network & Connection
        net_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        net_frame.pack(fill="x", padx=10, pady=(0, 10))

        net_title = ctk.CTkLabel(net_frame, text="🌐 Network & Speed Limits", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        net_title.pack(anchor="w", padx=14, pady=(10, 4))

        # Speed limit
        speed_row = ctk.CTkFrame(net_frame, fg_color="transparent")
        speed_row.pack(fill="x", padx=14, pady=(0, 8))

        speed_lbl = ctk.CTkLabel(speed_row, text="Download Speed Limit:", width=150, anchor="w", font=ctk.CTkFont(size=12))
        speed_lbl.pack(side="left")

        self.speed_combo = ctk.CTkComboBox(
            speed_row,
            values=["Unlimited", "1 MB/s", "2 MB/s", "5 MB/s", "10 MB/s", "25 MB/s"],
            width=160
        )
        self.speed_combo.set("Unlimited")
        self.speed_combo.pack(side="left")

        # Proxy
        proxy_row = ctk.CTkFrame(net_frame, fg_color="transparent")
        proxy_row.pack(fill="x", padx=14, pady=(0, 12))

        proxy_lbl = ctk.CTkLabel(proxy_row, text="Custom Proxy:", width=150, anchor="w", font=ctk.CTkFont(size=12))
        proxy_lbl.pack(side="left")

        self.proxy_entry = ctk.CTkEntry(proxy_row, placeholder_text="e.g. http://127.0.0.1:7890 or socks5://...", height=32)
        self.proxy_entry.pack(side="left", fill="x", expand=True)

        # 4. Subtitles Preferences
        sub_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        sub_frame.pack(fill="x", padx=10, pady=(0, 10))

        sub_title = ctk.CTkLabel(sub_frame, text="💬 Subtitles Configuration", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        sub_title.pack(anchor="w", padx=14, pady=(10, 4))

        sub_row = ctk.CTkFrame(sub_frame, fg_color="transparent")
        sub_row.pack(fill="x", padx=14, pady=(0, 12))

        sub_lbl = ctk.CTkLabel(sub_row, text="Subtitle Languages:", width=150, anchor="w", font=ctk.CTkFont(size=12))
        sub_lbl.pack(side="left")

        self.subs_entry = ctk.CTkEntry(sub_row, height=32)
        self.subs_entry.insert(0, "en")
        self.subs_entry.pack(side="left", fill="x", expand=True)

        # 5. Appearance & Theme
        theme_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        theme_frame.pack(fill="x", padx=10, pady=(0, 10))

        theme_title = ctk.CTkLabel(theme_frame, text="🎨 Appearance & UI Theme", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        theme_title.pack(anchor="w", padx=14, pady=(10, 4))

        theme_row = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_row.pack(fill="x", padx=14, pady=(0, 12))

        theme_lbl = ctk.CTkLabel(theme_row, text="Color Theme:", width=150, anchor="w", font=ctk.CTkFont(size=12))
        theme_lbl.pack(side="left")

        self.theme_seg = ctk.CTkSegmentedButton(
            theme_row,
            values=["Dark", "Light", "System"],
            command=self._on_theme_changed
        )
        self.theme_seg.set("Dark")
        self.theme_seg.pack(side="left")

    def _on_theme_changed(self, value):
        ctk.set_appearance_mode(value.lower())

    def get_settings(self) -> Dict[str, Any]:
        """Returns current configured settings dictionary."""
        # Speed limit
        spd = self.speed_combo.get()
        rate_limit = None
        if "1 MB/s" in spd:
            rate_limit = 1024 * 1024
        elif "2 MB/s" in spd:
            rate_limit = 2 * 1024 * 1024
        elif "5 MB/s" in spd:
            rate_limit = 5 * 1024 * 1024
        elif "10 MB/s" in spd:
            rate_limit = 10 * 1024 * 1024
        elif "25 MB/s" in spd:
            rate_limit = 25 * 1024 * 1024

        # Subtitles
        langs = [l.strip() for l in self.subs_entry.get().split(',') if l.strip()]
        if not langs:
            langs = ['en']

        return {
            'cookies_browser': self.cookie_combo.get() if self.cookie_combo.get() != 'None' else None,
            'proxy': self.proxy_entry.get().strip() or None,
            'rate_limit': rate_limit,
            'subtitle_langs': langs,
            'extra_opts': None
        }
