import os
import sys

# High DPI awareness for Windows 10/11
if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from ui.main_window import MainWindow

def main():
    app = MainWindow()
    app.mainloop()

if __name__ == '__main__':
    main()
