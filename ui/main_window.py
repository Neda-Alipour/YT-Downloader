import os
import sys
import customtkinter as ctk
from typing import Dict, Any

from core.downloader import Downloader
from ui.tabs.single_download import SingleDownloadTab
from ui.tabs.playlist_tab import PlaylistTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.logs_tab import LogsTab

class MainWindow(ctk.CTk):
    """
    Main application window with Windows 11 Fluent styling.
    """
    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("YT-DLP Downloader - Windows 11")
        self.geometry("980x740")
        self.minsize(860, 620)

        # Center on screen
        self._center_window(980, 740)

        # Apply Windows 11 Fluent Dark Mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize core downloader
        self.downloader = Downloader()

        self._build_ui()

    def _center_window(self, width: int, height: int):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # Header banner
        header_frame = ctk.CTkFrame(self, fg_color=("#EAEAEA", "#1F1F1F"), height=54, corner_radius=0)
        header_frame.pack(fill="x", side="top")

        # Title & Logo
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚡ YT-DLP Media Downloader",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.pack(side="left", padx=18, pady=12)

        version_badge = ctk.CTkLabel(
            header_frame,
            text="v2.0 (Win11)",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#0078D4",
            text_color="#FFFFFF",
            corner_radius=4,
            padx=6,
            pady=2
        )
        version_badge.pack(side="left", padx=(0, 16), pady=12)

        # Segmented Tab Navigation
        self.nav_seg = ctk.CTkSegmentedButton(
            header_frame,
            values=["Single Video", "Playlist & Batch", "Settings", "Activity Logs"],
            command=self._on_nav_change,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.nav_seg.set("Single Video")
        self.nav_seg.pack(side="right", padx=18, pady=11)

        # Container Frame for tabs
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=14, pady=14)

        # Initialize Logs tab first to receive all logs
        self.logs_tab = LogsTab(self.container)

        # Initialize Settings tab
        self.settings_tab = SettingsTab(self.container)

        # Initialize Single Download tab
        self.single_tab = SingleDownloadTab(
            self.container,
            downloader=self.downloader,
            get_settings=self.settings_tab.get_settings,
            log_callback=self._log_handler
        )

        # Initialize Playlist tab
        self.playlist_tab = PlaylistTab(
            self.container,
            downloader=self.downloader,
            get_settings=self.settings_tab.get_settings,
            log_callback=self._log_handler
        )

        # Show Single Video Tab by default
        self.single_tab.pack(fill="both", expand=True)

    def _log_handler(self, level: str, message: str):
        # Forward thread-safely to logs tab
        self.after(0, lambda: self.logs_tab.append_log(level, message))

    def _on_nav_change(self, value: str):
        # Hide all
        self.single_tab.pack_forget()
        self.playlist_tab.pack_forget()
        self.settings_tab.pack_forget()
        self.logs_tab.pack_forget()

        # Display selected
        if value == "Single Video":
            self.single_tab.pack(fill="both", expand=True)
        elif value == "Playlist & Batch":
            self.playlist_tab.pack(fill="both", expand=True)
        elif value == "Settings":
            self.settings_tab.pack(fill="both", expand=True)
        elif value == "Activity Logs":
            self.logs_tab.pack(fill="both", expand=True)
