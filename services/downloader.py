"""خدمة التحميل: yt-dlp + روابط مباشرة مقسمة مع تقدم"""
import os
import requests
import yt_dlp
from pathlib import Path


def extract_info(url: str) -> dict | None:
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
            "socket_timeout": 20}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            if info.get("_type") == "playlist" and info.get("entries"):
                info = next((e for e in info["entries"] if e), None) or info
            if not info or (not info.get("title") and not info.get("formats")):
                return None
            return info
    except Exception:
        return None


def best_sizes(info: dict):
    fmts = info.get("formats") or []
    v = [f for f in fmts if f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none")]
    best = None
    for f in v:
        cur = f.get("filesize") or f.get("filesize_approx") or 0
        bst = (best or {}).get("filesize") or (best or {}).get("filesize_approx") or 0
        if not best or cur > bst:
            best = f
    vsize = (best or {}).get("filesize") or (best or {}).get("filesize_approx")
    a = [f for f in fmts if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")]
    abest = max(a, key=lambda f: (f.get("abr") or 0), default=None)
    asize = (abest or {}).get("filesize") or (abest or {}).get("filesize_approx")
    res = (best or {}).get("resolution") or (best or {}).get("format_note") or ""
    return res, vsize, asize


def head_info(url: str, timeout: int = 15) -> tuple[str, str, int]:
    """يرجع (final_url, content_type, size) لرابط مباشر"""
    r = requests.head(url, allow_redirects=True, timeout=timeout)
    return (r.url or url), r.headers.get("Content-Type", ""), int(r.headers.get("Content-Length") or 0)


def download_direct_sync(url: str, dest: str, hook=None, chunk: int = 1024 * 512) -> str:
    """تحميل مقسم مع hook(downloaded, total). يعمل في Thread."""
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            for part in r.iter_content(chunk):
                if part:
                    f.write(part)
                    done += len(part)
                    if hook:
                        try:
                            hook(done, total)
                        except Exception:
                            pass
    return dest


def download_media_sync(url: str, outtmpl: str, audio_only: bool, quality: str = "high", hook=None) -> None:
    """تحميل yt-dlp في Thread مع progress_hook يسجل التقدم."""
    def _hook(d: dict):
        if hook and d.get("status") == "downloading":
            try:
                hook(d.get("downloaded_bytes") or 0, d.get("total_bytes") or d.get("total_bytes_estimate") or 0)
            except Exception:
                pass

    if audio_only:
        fmt = "bestaudio/best"
        pp = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        merge = None
    else:
        fmt = "bv*+ba/best" if quality == "high" else "bv*[height<=720]+ba/best[height<=720]/best[height<=720]/best"
        pp = []
        merge = "mp4"

    opts = {"outtmpl": outtmpl, "noplaylist": True, "quiet": True, "no_warnings": True,
            "socket_timeout": 30, "retries": 3, "format": fmt, "progress_hooks": [_hook]}
    if pp:
        opts["postprocessors"] = pp
    if merge:
        opts["merge_output_format"] = merge
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(url, download=True)


def biggest_file(folder: str) -> str | None:
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if os.path.isfile(os.path.join(folder, f))]
    if not files:
        return None
    return max(files, key=os.path.getsize)
