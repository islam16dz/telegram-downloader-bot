"""إدارة ملفات الأدمن + الإعدادات + الأخطاء"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
import config
from services.store import load_admin_files, save_admin_files
from services.helpers import fmt_bytes
import keyboards as kb

log = logging.getLogger("dl-bot")


# ---- admin ----
async def files_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    items = load_admin_files()
    if not items:
        await update.message.reply_text("📭 لا توجد ملفات أدمن بعد.")
        return
    await update.message.reply_text(f"📁 ملفات الأدمن ({len(items)}):", reply_markup=kb.files_menu(items))


async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("⛔ للأدمن فقط.")
        return
    items = load_admin_files()
    total = sum(i.get("size") or 0 for i in items)
    await update.message.reply_text(
        f"🛠 لوحة الأدمن\n🆔 {update.effective_user.id}\n📁 {len(items)} ملف\n💾 {fmt_bytes(total)}\n\n"
        "• ابعت أي ملف للتخزين\n• /files للعرض\n• /del <رقم> للحذف")


async def del_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("⛔ للأدمن فقط.")
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.message.reply_text("استخدم: /del 1")
        return
    idx = int(ctx.args[0]) - 1
    items = load_admin_files()
    if 0 <= idx < len(items):
        removed = items.pop(idx)
        save_admin_files(items)
        await update.message.reply_text(f"🗑 تم حذف: {removed.get('name')}")
    else:
        await update.message.reply_text("❌ رقم غير صحيح.")


async def on_admin_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS:
        return
    msg = update.message
    fid = name = ftype = size = None
    if msg.document:
        fid, name, size, ftype = msg.document.file_id, msg.document.file_name or "file", msg.document.file_size, "doc"
    elif msg.video:
        fid, name, size, ftype = msg.video.file_id, f"video_{msg.video.file_unique_id}.mp4", msg.video.file_size, "video"
    elif msg.audio:
        fid, name, size, ftype = msg.audio.file_id, msg.audio.file_name or "audio.mp3", msg.audio.file_size, "audio"
    elif msg.photo:
        fid, name, size, ftype = msg.photo[-1].file_id, f"photo_{msg.photo[-1].file_unique_id}.jpg", msg.photo[-1].file_size, "photo"
    elif msg.voice:
        fid, name, size, ftype = msg.voice.file_id, "voice.ogg", msg.voice.file_size, "audio"
    if not fid:
        return
    items = load_admin_files()
    items.append({"file_id": fid, "name": name, "type": ftype, "size": size})
    save_admin_files(items)
    await msg.reply_text(f"✅ اتخزن رقم {len(items)}\n📄 {name}\nالأعضاء: /files")


async def on_getfile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        idx = int((q.data or "").split("|", 1)[1])
        it = load_admin_files()[idx]
    except Exception:
        await q.message.reply_text("❌ الملف غير موجود.")
        return
    typ, fid, cap = it.get("type", "doc"), it["file_id"], f"📁 {it.get('name')}"
    if typ == "video":
        await q.message.reply_video(video=fid, caption=cap)
    elif typ == "audio":
        await q.message.reply_audio(audio=fid, caption=cap)
    elif typ == "photo":
        await q.message.reply_photo(photo=fid, caption=cap)
    else:
        await q.message.reply_document(document=fid, caption=cap)


# ---- settings ----
async def on_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "set:qtoggle":
        ctx.user_data["quality"] = "med" if ctx.user_data.get("quality", "high") == "high" else "high"
    elif q.data == "set:ptoggle":
        ctx.user_data["show_progress"] = not ctx.user_data.get("show_progress", True)
    await q.edit_message_text("⚙️ **الإعدادات**",
                              reply_markup=kb.settings_menu(ctx.user_data.get("quality", "high"),
                                                            ctx.user_data.get("show_progress", True)),
                              parse_mode="Markdown")


# ---- errors ----
async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.exception("Handler error", exc_info=ctx.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("⚠️ حصل خطأ بسيط، حاول مجدداً. والبوت مستمر في العمل.")
    except Exception:
        pass
