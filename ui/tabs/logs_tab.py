import datetime
import customtkinter as ctk
from tkinter import messagebox

class LogsTab(ctk.CTkFrame):
    """
    Real-time log viewer displaying yt-dlp console logs, FFmpeg merges, and network events.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.auto_scroll = ctk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self):
        # Header toolbar
        bar = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#242424"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        bar.pack(fill="x", padx=10, pady=(0, 10))

        title = ctk.CTkLabel(bar, text="📋 Execution & Diagnostics Log", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        title.pack(side="left", padx=14, pady=10)

        self.scroll_check = ctk.CTkCheckBox(bar, text="Auto-scroll", variable=self.auto_scroll)
        self.scroll_check.pack(side="right", padx=(0, 14), pady=10)

        copy_btn = ctk.CTkButton(
            bar,
            text="Copy Logs",
            width=80,
            height=28,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._copy_logs
        )
        copy_btn.pack(side="right", padx=(0, 8), pady=10)

        clear_btn = ctk.CTkButton(
            bar,
            text="Clear",
            width=65,
            height=28,
            fg_color=("#EAEAEA", "#333333"),
            hover_color=("#DADADA", "#404040"),
            text_color=("#1A1A1A", "#FFFFFF"),
            command=self._clear_logs
        )
        clear_btn.pack(side="right", padx=(0, 8), pady=10)

        # Text area container
        self.text_frame = ctk.CTkFrame(self, fg_color=("#F9F9F9", "#181818"), corner_radius=10, border_width=1, border_color=("#E5E5E5", "#2F2F2F"))
        self.text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.textbox = ctk.CTkTextbox(
            self.text_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="transparent",
            wrap="word",
            activate_scrollbars=True
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.append_log("INFO", "Application initialized. Ready for operations.")

    def append_log(self, level: str, message: str):
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = f"[{time_str}] [{level}] "

        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{prefix}{message}\n")
        self.textbox.configure(state="disabled")

        if self.auto_scroll.get():
            self.textbox.see("end")

    def _clear_logs(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self.append_log("INFO", "Logs cleared.")

    def _copy_logs(self):
        content = self.textbox.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Copied", "Logs copied to clipboard!")
