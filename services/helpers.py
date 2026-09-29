"""دوال مساعدة مشتركة"""
import os
import re
from urllib.parse import urlparse, unquote

URL_RE = re.compile(r"https?://[^\s]+")

SPIN = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def spin_frame(i: int) -> str:
    return SPIN[i % len(SPIN)]


def fmt_bytes(n) -> str:
    if not n:
        return "غير معروف"
    n = float(n)
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_dur(sec) -> str:
    if not sec:
        return "—"
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def clean_url(text: str) -> str | None:
    m = URL_RE.search(text or "")
    if not m:
        return None
    return m.group(0).rstrip(").],!؟\"'")


def guess_filename(url: str, ctype: str = "") -> str:
    parsed = urlparse(url)
    name = unquote(os.path.basename(parsed.path) or "file")
    if not name or "." not in name:
        ext = ctype.split("/")[-1].split(";")[0] if "/" in ctype else "bin"
        name = f"file.{ext}"
    return name[:120]


def split_text(text: str, limit: int = 4000) -> list[str]:
    parts, cur = [], ""
    for line in (text or "").splitlines(keepends=True):
        if len(cur) + len(line) > limit:
            parts.append(cur)
            cur = line
        else:
            cur += line
    if cur:
        parts.append(cur)
    return parts or [""]


def progress_bar(done: int, total: int, width: int = 12) -> str:
    if not total:
        return f"⏳ {fmt_bytes(done)}"
    p = max(0.0, min(1.0, done / total))
    fill = int(p * width)
    return f"{'█' * fill}{'░' * (width - fill)} {p*100:.0f}% • {fmt_bytes(done)}/{fmt_bytes(total)}"
