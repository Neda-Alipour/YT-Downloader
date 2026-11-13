import re
from typing import List, Dict, Any, Optional
from .downloader import Downloader

def parse_range_string(range_str: str, max_count: int = 10000) -> List[int]:
    """
    Parses expressions like '1-5, 8, 10-12' into a sorted list of 1-based integers.
    Bounds checks against max_count.
    """
    indices = set()
    parts = [p.strip() for p in range_str.split(',') if p.strip()]

    for part in parts:
        if '-' in part:
            bounds = part.split('-')
            if len(bounds) == 2:
                try:
                    start = int(bounds[0].strip())
                    end = int(bounds[1].strip())
                    if start <= end:
                        for i in range(start, end + 1):
                            if 1 <= i <= max_count:
                                indices.add(i)
                except ValueError:
                    continue
        else:
            try:
                num = int(part)
                if 1 <= num <= max_count:
                    indices.add(num)
            except ValueError:
                continue

    return sorted(list(indices))

def format_indices_to_ytdlp(indices: List[int]) -> str:
    """
    Converts a list of integers [1, 2, 3, 5, 8, 9] into a concise comma-separated string for yt-dlp playlist_items.
    """
    if not indices:
        return ""
    sorted_idx = sorted(set(indices))
    return ",".join(str(i) for i in sorted_idx)

def extract_playlist_data(url: str, cookies_browser: Optional[str] = None, proxy: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts playlist metadata and its entry items list without downloading.
    """
    raw_info = Downloader.fetch_info(url, cookies_browser=cookies_browser, proxy=proxy)
    
    entries = raw_info.get('entries', [])
    if entries is None:
        entries = []
    
    # In some flat extractions entries might be a generator or list
    entry_list = list(entries)
    
    cleaned_entries = []
    for idx, item in enumerate(entry_list, start=1):
        if not item:
            continue
        duration_sec = item.get('duration') or 0
        minutes, seconds = divmod(int(duration_sec), 60)
        hours, minutes = divmod(minutes, 60)
        dur_str = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

        video_id = item.get('id') or item.get('url')
        video_url = item.get('webpage_url') or item.get('url')
        if not video_url and video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        cleaned_entries.append({
            'index': idx,
            'id': video_id,
            'title': item.get('title') or f"Video #{idx}",
            'duration_str': dur_str,
            'duration_sec': duration_sec,
            'uploader': item.get('uploader') or item.get('channel') or 'Unknown',
            'thumbnail': item.get('thumbnail') or (f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""),
            'url': video_url,
        })

    return {
        'id': raw_info.get('id', ''),
        'title': raw_info.get('title') or "Untitled Playlist",
        'uploader': raw_info.get('uploader') or raw_info.get('channel') or "Unknown Channel",
        'description': raw_info.get('description', ''),
        'total_count': len(cleaned_entries),
        'entries': cleaned_entries
    }
