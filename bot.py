#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تليجرام للتحميل بالرابط فقط
- يدعم كل المواقع عبر yt-dlp (يوتيوب، تيك توك، انستا، فيس، تويتر، ... +1000 موقع)
- ابعت رابط => يعرض التفاصيل + زرارين: 🎬 أعلى جودة | 🎵 صوت فقط
- روابط مباشرة (pdf, zip, apk...) => يعرض الاسم والحجم ويحملها ويبعتها
- لوحة أدمن: الأدمن يبعت أي ملف للبوت يتخزن، والأعضاء يجيبوه من /files
- مصمم للشغل 24/7 على Railway / Render

تشغيل محلي:
  pip install -r requirements.txt
  cp .env.example .env  (وحط التوكن)
  python bot.py
"""

import os
import re
import json
import uuid
import asyncio
import logging
import tempfile
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
import yt_dlp
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
MAX_SEND_MB = int(os.getenv("MAX_FILE_MB", "50"))
MAX_SEND_BYTES = MAX_SEND_MB * 1024 * 1024

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "admin_files.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("dl-bot")

URL_RE = re.compile(r"https?://[^\s]+")

# تخزين مؤقت للروابط (callback_data في تليجرام محدود 64 بايت فبنخزن الرابط هنا بمفتاح قصير)
pending: dict[str, str] = {}

# ============ ملفات الأدمن ============
def load_admin_files():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_admin_files(items):
    DATA_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def fmt_bytes(n):
    if not n:
        return "غير معروف"
    n = float(n)
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def fmt_dur(sec):
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
    # شيل علامات الترقيم اللي بتلزق في آخر اللينك
    return m.group(0).rstrip(").],!؟\"'")

# ============ yt-dlp ============
def extract_info(url: str) -> dict | None:
    """يرجع معلومات الفيديو بدون تحميل، أو None لو مش صفحة فيديو."""
    opts = {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "socket_timeout": 20,
        "extract_flat": False,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            # لو بلاي ليست خد أول عنصر
            if info.get("_type") == "playlist" and info.get("entries"):
                info = next((e for e in info["entries"] if e), None) or info
            if not info or (not info.get("title") and not info.get("formats")):
                return None
            return info
    except Exception as e:
        log.info(f"extract_info failed for {url}: {e}")
        return None

def best_sizes(info: dict):
    """تقدير أحجام أعلى جودة فيديو وصوت."""
    fmts = info.get("formats") or []
    v = [f for f in fmts if f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none")]
    best = None
    for f in v:
        if not best or (f.get("filesize") or f.get("filesize_approx") or 0) > (best.get("filesize") or best.get("filesize_approx") or 0):
            best = f
    vsize = (best or {}).get("filesize") or (best or {}).get("filesize_approx")
    # صوت
    a = [f for f in fmts if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")]
    abest = max(a, key=lambda f: (f.get("abr") or 0), default=None)
    asize = (abest or {}).get("filesize") or (abest or {}).get("filesize_approx")
    res = (best or {}).get("resolution") or (best or {}).get("format_note") or ""
    return res, vsize, asize

async def run_ydl_blocking(opts, url):
    loop = asyncio.get_running_loop()
    def _run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)
    return await loop.run_in_executor(None, _run)

# ============ أوامر ============
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    admin_hint = "\n🛠 أنت أدمن: ابعت أي ملف (فيديو/صوت/مستند) عشان يتخزن ويظهر في /files" if is_admin(update.effective_user.id) else ""
    await update.message.reply_text(
        "👋 أهلاً بيك!\n\n"
        "📎 ابعت أي رابط فقط وهعرضلك التفاصيل:\n"
        "• 🎬 فيديو بأعلى جودة (MP4)\n"
        "• 🎵 صوت فقط (MP3)\n"
        "• 📦 روابط مباشرة (pdf / zip / apk ...) بحملها وأبعتهالك\n\n"
        "📁 ملفات الأدمن: /files\n"
        "❓ مساعدة: /help"
        f"{admin_hint}"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 طريقة الاستخدام:\n\n"
        "1️⃣ ابعت رابط فيديو (يوتيوب، تيك توك، انستا، فيس، ...)\n"
        "   هبعتلك الصورة والعنوان والمدة والأحجام + زرارين للتحميل.\n\n"
        "2️⃣ ابعت رابط ملف مباشر:\n"
        "   هبعتلك الاسم والحجم وزرار تحميل.\n\n"
        f"3️⃣ حد التليجرام: {MAX_SEND_MB}MB للملف الواحد. لو أكبر هقولك وأقترح الصوت فقط.\n\n"
        "👑 للأدمن:\n"
        "• ابعت أي ملف هنا وهيتخزن تلقائياً\n"
        "• /files — عرض الملفات\n"
        "• /del <رقم> — حذف ملف\n"
        "• /admin — إحصائيات"
    )

async def files_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    items = load_admin_files()
    if not items:
        await update.message.reply_text("📭 لا توجد ملفات من الأدمن بعد.")
        return
    kb = []
    for i, it in enumerate(items, 1):
        kb.append([InlineKeyboardButton(f"{i}. {it.get('name','ملف')} ({fmt_bytes(it.get('size'))})", callback_data=f"getfile|{i-1}")])
    await update.message.reply_text(f"📁 ملفات الأدمن ({len(items)}):\nاختر ملف للتحميل:", reply_markup=InlineKeyboardMarkup(kb))

async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ الأمر ده للأدمن فقط.")
        return
    items = load_admin_files()
    total = sum(i.get("size") or 0 for i in items)
    await update.message.reply_text(
        f"🛠 لوحة الأدمن\n\n🆔 ID بتاعك: {update.effective_user.id}\n"
        f"📁 عدد الملفات: {len(items)}\n"
        f"💾 الحجم التقريبي: {fmt_bytes(total)}\n\n"
        "• ابعت أي ملف هنا للتخزين\n• /files للعرض\n• /del <رقم> للحذف"
    )

async def del_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ للأدمن فقط.")
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("استخدم: /del <رقم>  (مثال: /del 1)")
        return
    idx = int(ctx.args[0]) - 1
    items = load_admin_files()
    if 0 <= idx < len(items):
        removed = items.pop(idx)
        save_admin_files(items)
        await update.message.reply_text(f"🗑 تم حذف: {removed.get('name')}")
    else:
        await update.message.reply_text("❌ رقم غير صحيح.")

# ============ استقبال الروابط ============
async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    url = clean_url(text)
    if not url:
        return
    wait = await update.message.reply_text("🔎 بفحص الرابط وبجيب التفاصيل...")

    # 1) جرّب كصفحة فيديو
    info = await asyncio.get_running_loop().run_in_executor(None, extract_info, url)
    if info:
        key = uuid.uuid4().hex[:10]
        pending[key] = url
        title = info.get("title", "بدون عنوان")[:200]
        up = info.get("uploader") or info.get("channel") or "—"
        dur = fmt_dur(info.get("duration"))
        view = info.get("view_count")
        res, vsize, asize = await asyncio.get_running_loop().run_in_executor(None, best_sizes, info)
        thumb = info.get("thumbnail")
        site = info.get("extractor_key") or info.get("extractor") or "رابط"
        cap = (
            f"✅ تم التعرف على الرابط\n\n🎬 {title}\n"
            f"📡 المصدر: {site}\n👤 الناشر: {up}\n⏱ المدة: {dur}\n"
            + (f"👁 المشاهدات: {view:,}\n" if view else "")
            + (f"📐 أعلى جودة: {res}\n" if res else "")
            + f"💾 حجم الفيديو التقريبي: {fmt_bytes(vsize)}\n"
            f"🎵 حجم الصوت التقريبي: {fmt_bytes(asize)}\n\nاختر التحميل:"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 فيديو أعلى جودة", callback_data=f"vid|{key}")],
            [InlineKeyboardButton("🎵 صوت فقط MP3", callback_data=f"aud|{key}")],
        ])
        try:
            if thumb:
                await update.message.reply_photo(photo=thumb, caption=cap[:1000], reply_markup=kb)
                await wait.delete()
            else:
                await wait.edit_text(cap[:1000], reply_markup=kb)
        except Exception:
            await wait.edit_text(cap[:1000], reply_markup=kb)
        return

    # 2) رابط مباشر
    try:
        r = requests.head(url, allow_redirects=True, timeout=15)
        ctype = r.headers.get("Content-Type", "")
        size = int(r.headers.get("Content-Length") or 0)
        parsed = urlparse(r.url or url)
        name = unquote(os.path.basename(parsed.path) or "file")
        if not name or "." not in name:
            ext = ctype.split("/")[-1].split(";")[0] if "/" in ctype else "bin"
            name = f"file.{ext}"
        key = uuid.uuid4().hex[:10]
        pending[key] = url
        warn = ""
        if size and size > MAX_SEND_BYTES:
            warn = f"\n⚠️ الملف أكبر من حد التليجرام ({MAX_SEND_MB}MB) — قد يفشل الإرسال."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 تحميل الملف", callback_data=f"direct|{key}")]])
        await wait.edit_text(
            f"📦 رابط مباشر\n\n📄 الاسم: {name}\n📁 النوع: {ctype or 'غير معروف'}\n"
            f"💾 الحجم: {fmt_bytes(size)}{warn}\n\nاضغط للتحميل:",
            reply_markup=kb,
        )
    except Exception as e:
        await wait.edit_text(f"❌ مقدرتش أتعرف على الرابط.\nتأكد إنه شغال وجرب تاني.\n({e})")

# ============ التحميل والإرسال ============
async def do_download_send(query, url: str, mode: str):
    """mode: vid | aud | direct"""
    chat = query.message.chat
    status = await chat.send_message("⏳ جاري التحميل... قد ياخد دقيقة للملفات الكبيرة.")

    tmpdir = tempfile.mkdtemp(prefix="dlbot_")
    try:
        if mode == "direct":
            # تحميل مباشر بـ requests مع progress بسيط
            parsed = urlparse(url)
            name = unquote(os.path.basename(parsed.path) or "file")
            dest = os.path.join(tmpdir, name or "file")
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length") or 0)
                if total and total > MAX_SEND_BYTES:
                    await status.edit_text(f"❌ الملف حجمه {fmt_bytes(total)} أكبر من حد التليجرام ({MAX_SEND_MB}MB).")
                    return
                done = 0
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1024 * 256):
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                size = os.path.getsize(dest)
                if size > MAX_SEND_BYTES:
                    await status.edit_text(f"❌ بعد التحميل الحجم {fmt_bytes(size)} أكبر من الحد ({MAX_SEND_MB}MB).")
                    return
            await status.edit_text("📤 جاري الرفع إلى تليجرام...")
            await chat.send_document(document=InputFile(dest, filename=os.path.basename(dest)),
                                     caption=f"✅ تم التحميل\n📄 {os.path.basename(dest)}")
            await status.delete()
        else:
            is_audio = (mode == "aud")
            outtmpl = os.path.join(tmpdir, "%(title).80s.%(ext)s")
            opts = {
                "outtmpl": outtmpl, "noplaylist": True, "quiet": True, "no_warnings": True,
                "socket_timeout": 30, "retries": 3,
            }
            if is_audio:
                opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
                })
            else:
                opts.update({
                    "format": "bv*+ba/best",
                    "merge_output_format": "mp4",
                })
            await status.edit_text("⏳ جاري التحميل بأعلى جودة..." if not is_audio else "⏳ جاري استخراج الصوت MP3...")
            await run_ydl_blocking(opts, url)
            files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)]
            if not files:
                await status.edit_text("❌ فشل التحميل. جرب رابط تاني.")
                return
            fpath = max(files, key=os.path.getsize)
            size = os.path.getsize(fpath)
            if size > MAX_SEND_BYTES:
                await status.edit_text(
                    f"❌ حجم الناتج {fmt_bytes(size)} أكبر من حد التليجرام ({MAX_SEND_MB}MB).\n"
                    "💡 جرب «صوت فقط» بدل الفيديو."
                )
                return
            await status.edit_text("📤 جاري الرفع إلى تليجرام...")
            base = os.path.basename(fpath)
            if is_audio:
                await chat.send_audio(audio=InputFile(fpath, filename=base), title=base)
            else:
                await chat.send_video(video=InputFile(fpath, filename=base), caption=f"✅ بأعلى جودة\n🎬 {base}",
                                      supports_streaming=True)
            await status.delete()
    except Exception as e:
        log.exception("download failed")
        try:
            await status.edit_text(f"❌ حصل خطأ أثناء التحميل:\n{e}")
        except Exception:
            pass
    finally:
        # تنظيف
        try:
            for f in Path(tmpdir).glob("*"):
                f.unlink(missing_ok=True)
            Path(tmpdir).rmdir()
        except Exception:
            pass

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        action, key = (q.data or "").split("|", 1)
    except ValueError:
        return
    if action == "getfile":
        items = load_admin_files()
        try:
            it = items[int(key)]
        except Exception:
            await q.message.reply_text("❌ الملف مش موجود.")
            return
        fid = it["file_id"]
        typ = it.get("type", "doc")
        cap = f"📁 {it.get('name')}"
        if typ == "video":
            await q.message.reply_video(video=fid, caption=cap)
        elif typ == "audio":
            await q.message.reply_audio(audio=fid, caption=cap)
        elif typ == "photo":
            await q.message.reply_photo(photo=fid, caption=cap)
        else:
            await q.message.reply_document(document=fid, caption=cap)
        return
    url = pending.get(key)
    if not url:
        await q.message.reply_text("⏳ الرابط انتهت صلاحيته. ابعته تاني.")
        return
    if action in ("vid", "aud", "direct"):
        await do_download_send(q, url, action)

# ============ ملفات الأدمن (تخزين file_id) ============
async def on_admin_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return  # تجاهل ملفات غير الأدمن
    msg = update.message
    fid = name = ftype = size = None
    if msg.document:
        fid = msg.document.file_id; name = msg.document.file_name or "file"; size = msg.document.file_size; ftype = "doc"
    elif msg.video:
        fid = msg.video.file_id; name = f"video_{msg.video.file_unique_id}.mp4"; size = msg.video.file_size; ftype = "video"
    elif msg.audio:
        fid = msg.audio.file_id; name = msg.audio.file_name or msg.audio.title or "audio.mp3"; size = msg.audio.file_size; ftype = "audio"
    elif msg.photo:
        fid = msg.photo[-1].file_id; name = f"photo_{msg.photo[-1].file_unique_id}.jpg"; size = msg.photo[-1].file_size; ftype = "photo"
    elif msg.voice:
        fid = msg.voice.file_id; name = "voice.ogg"; size = msg.voice.file_size; ftype = "audio"
    if not fid:
        return
    items = load_admin_files()
    items.append({"file_id": fid, "name": name, "type": ftype, "size": size})
    save_admin_files(items)
    await msg.reply_text(f"✅ اتخزن كملف أدمن رقم {len(items)}\n📄 {name}\nالأعضاء يقدروا يجيبوه من /files")

def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ حط BOT_TOKEN في ملف .env (شوف .env.example)")
    if not ADMIN_IDS:
        log.warning("⚠️ ADMIN_IDS فاضي — مميزات الأدمن مش هتشتغل لحد ما تحط ID بتاعك في .env")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.ATTACHMENT & ~filters.COMMAND, on_admin_file))
    log.info(f"🤖 Bot running | admin={ADMIN_IDS} | max={MAX_SEND_MB}MB")
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
