import os
import sys
import shutil

def get_ffmpeg_location() -> str:
    """
    Finds the directory or executable for FFmpeg and FFprobe.
    yt-dlp prefers a directory path containing both ffmpeg.exe and ffprobe.exe,
    or a direct path to ffmpeg.exe.
    """
    # 1. PyInstaller bundled dir
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
        if os.path.isfile(os.path.join(bundle_dir, 'ffmpeg.exe')):
            return bundle_dir
        bundle_bin = os.path.join(bundle_dir, 'bin')
        if os.path.isfile(os.path.join(bundle_bin, 'ffmpeg.exe')):
            return bundle_bin

    # 2. Local application bin/ directory (highest priority in source tree)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_bin = os.path.join(base_dir, 'bin')
    if os.path.isfile(os.path.join(local_bin, 'ffmpeg.exe')):
        return local_bin

    # 3. Local application root
    if os.path.isfile(os.path.join(base_dir, 'ffmpeg.exe')):
        return base_dir

    # 4. static_ffmpeg package bin folder
    try:
        import static_ffmpeg
        ffmpeg_exe, ffprobe_exe = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
            return os.path.dirname(ffmpeg_exe)
    except Exception:
        pass

    # 5. imageio_ffmpeg fallback
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
            return ffmpeg_exe
    except Exception:
        pass

    # 6. System PATH
    path_ffmpeg = shutil.which('ffmpeg')
    if path_ffmpeg:
        return os.path.dirname(path_ffmpeg)

    return ""

def get_ffmpeg_path() -> str:
    """Returns direct path to ffmpeg.exe for status display."""
    loc = get_ffmpeg_location()
    if not loc:
        return ""
    if os.path.isfile(loc):
        return loc
    candidate = os.path.join(loc, 'ffmpeg.exe')
    if os.path.isfile(candidate):
        return candidate
    return loc

def is_ffmpeg_available() -> bool:
    loc = get_ffmpeg_location()
    return bool(loc and (os.path.isfile(loc) or os.path.isdir(loc)))
