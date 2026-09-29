"""قسم التحميل: روابط فيديو + مباشرة مع شريط تقدم وتنظيف تلقائي"""
import asyncio
import shutil
import time
import uuid
from pathlib import Path
from telegram import Update, InputFile
from telegram.ext import ContextTypes

import config
import keyboards as kb
from services import downloader as DL
from services.helpers import fmt_bytes, fmt_dur, clean_url, guess_filename, progress_bar


def _pending(ctx: ContextTypes.DEFAULT_TYPE) -> dict:
    return ctx.bot_data.setdefault("pending_links", {})


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # وضع AI له أولوية (ما عدا الروابط)
    if ctx.user_data.get("ai_mode") and not clean_url(update.message.text or ""):
        from handlers.ai import answer_ai
        await answer_ai(update, ctx, update.message.text)
        return

    url = clean_url(update.message.text or "")
    if not url:
        return
    wait = await update.message.reply_text("🔎 بفحص الرابط وبجيب التفاصيل...")

    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, DL.extract_info, url)
    if info:
        key = uuid.uuid4().hex[:10]
        _pending(ctx)[key] = url
        title = (info.get("title") or "بدون عنوان")[:200]
        up = info.get("uploader") or info.get("channel") or "—"
        dur = fmt_dur(info.get("duration"))
        view = info.get("view_count")
        res, vsize, asize = await loop.run_in_executor(None, DL.best_sizes, info)
        thumb = info.get("thumbnail")
        site = info.get("extractor_key") or info.get("extractor") or "رابط"
        cap = (f"✅ تم التعرف\n\n🎬 {title}\n📡 {site}\n👤 {up}\n⏱ {dur}\n"
               + (f"👁 {view:,}\n" if view else "")
               + (f"📐 {res}\n" if res else "")
               + f"💾 فيديو: {fmt_bytes(vsize)}\n🎵 صوت: {fmt_bytes(asize)}\n\nاختر:")
        try:
            if thumb:
                await update.message.reply_photo(photo=thumb, caption=cap[:1000], reply_markup=kb.download_menu(key))
                await wait.delete()
            else:
                await wait.edit_text(cap[:1000], reply_markup=kb.download_menu(key))
        except Exception:
            await wait.edit_text(cap[:1000], reply_markup=kb.download_menu(key))
        return

    # رابط مباشر
    try:
        final, ctype, size = await loop.run_in_executor(None, DL.head_info, url)
        name = guess_filename(final, ctype)
        key = uuid.uuid4().hex[:10]
        _pending(ctx)[key] = final
        warn = f"\n⚠️ أكبر من حد تليجرام ({config.MAX_FILE_MB}MB)." if size and size > config.MAX_SEND_BYTES else ""
        await wait.edit_text(
            f"📦 رابط مباشر\n\n📄 {name}\n📁 {ctype or '؟'}\n💾 {fmt_bytes(size)}{warn}",
            reply_markup=kb.direct_menu(key))
    except Exception as e:
        await wait.edit_text(f"❌ مقدرتش أتعرف على الرابط.\n({e})")


async def _updater(status_msg, state: dict, prefix: str, show: bool):
    last = 0.0
    while not state.get("done"):
        await asyncio.sleep(2.5)
        if not show:
            continue
        d, t = state.get("done_bytes", 0), state.get("total", 0)
        txt = f"{prefix}\n{progress_bar(d, t)}"
        if txt != state.get("last_txt") and time.time() - last > 2.4:
            state["last_txt"] = txt
            last = time.time()
            try:
                await status_msg.edit_text(txt)
            except Exception:
                pass


async def _send_with_progress(query, url: str, mode: str, ctx: ContextTypes.DEFAULT_TYPE):
    chat = query.message.chat
    show = ctx.user_data.get("show_progress", True)
    quality = ctx.user_data.get("quality", "high")
    status = await chat.send_message("⏳ جاري التحميل...")
    tmpdir = Path(config.TEMP_ROOT) / f"job_{uuid.uuid4().hex[:8]}"
    tmpdir.mkdir(parents=True, exist_ok=True)
    state = {"done": False, "done_bytes": 0, "total": 0}
    updater = asyncio.create_task(_updater(status, state,
                                           "⏳ تحميل الفيديو..." if mode == "vid" else "⏳ استخراج الصوت..." if mode == "aud" else "⏳ تحميل الملف...",
                                           show))
    try:
        loop = asyncio.get_running_loop()

        def hook(d, t):
            state["done_bytes"] = d
            state["total"] = t

        if mode == "direct":
            name = guess_filename(url)
            dest = str(tmpdir / name)
            await loop.run_in_executor(None, DL.download_direct_sync, url, dest, hook)
            size = Path(dest).stat().st_size
            if size > config.MAX_SEND_BYTES:
                await status.edit_text(f"❌ الحجم {fmt_bytes(size)} أكبر من حد تليجرام ({config.MAX_FILE_MB}MB).")
                return
            await status.edit_text("📤 جاري الرفع...")
            await chat.send_document(document=InputFile(dest, filename=name), caption=f"✅ تم\n📄 {name}")
        else:
            audio_only = (mode == "aud")
            outtmpl = str(tmpdir / "%(title).80s.%(ext)s")
            await loop.run_in_executor(None, DL.download_media_sync, url, outtmpl, audio_only, quality, hook)
            fpath = DL.biggest_file(str(tmpdir))
            if not fpath:
                await status.edit_text("❌ فشل التحميل. جرب رابطاً آخر.")
                return
            size = Path(fpath).stat().st_size
            if size > config.MAX_SEND_BYTES:
                await status.edit_text(f"❌ الناتج {fmt_bytes(size)} أكبر من الحد ({config.MAX_FILE_MB}MB).\n💡 جرب الصوت فقط أو قلل الجودة من ⚙️.")
                return
            await status.edit_text("📤 جاري الرفع...")
            base = Path(fpath).name
            if audio_only:
                await chat.send_audio(audio=InputFile(fpath, filename=base), title=base)
            else:
                await chat.send_video(video=InputFile(fpath, filename=base), caption=f"✅ أعلى جودة\n🎬 {base}", supports_streaming=True)
        try:
            await status.delete()
        except Exception:
            pass
    except Exception as e:
        try:
            await status.edit_text(f"❌ خطأ أثناء التحميل:\n{e}")
        except Exception:
            pass
    finally:
        state["done"] = True
        try:
            updater.cancel()
        except Exception:
            pass
        shutil.rmtree(tmpdir, ignore_errors=True)


async def on_download_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        action, key = (q.data or "").split("|", 1)
        mode = action.split(":")[1]  # vid/aud/direct
    except (ValueError, IndexError):
        return
    url = _pending(ctx).get(key)
    if not url:
        await q.message.reply_text("⏳ انتهت صلاحية الرابط. ابعته مجدداً.")
        return
    await _send_with_progress(q, url, mode, ctx)
