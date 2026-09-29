"""التنقل بين القوائم الرئيسية والفرعية"""
from telegram import Update
from telegram.ext import ContextTypes
import keyboards as kb
import config
from services.store import load_admin_files


async def webapp_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not config.WEBAPP_URL:
        await update.message.reply_text(
            "🌐 لوحة WebApp غير مفعلة بعد.\nارفع مجلد `webapp/` على GitHub Pages ثم حط رابطه في `WEBAPP_URL` وأعد التشغيل.",
            reply_markup=kb.back_menu())
        return
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
    await update.message.reply_text("🌐 افتح لوحة التحكم:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 لوحة التحكم", web_app=WebAppInfo(url=config.WEBAPP_URL))]]))


async def on_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    dest = (q.data or "").split(":", 1)[-1]

    if dest == "main":
        await q.edit_message_text("🏠 **القائمة الرئيسية**\nاختر قسماً:", reply_markup=kb.main_menu(config.WEBAPP_URL), parse_mode="Markdown")
    elif dest == "dl":
        await q.edit_message_text(
            "📥 **قسم التحميل**\n\nابعت رابط فقط وسأعرض التفاصيل:\n• 🎬 فيديو أعلى جودة\n• 🎵 صوت MP3\n• 📦 روابط مباشرة",
            reply_markup=kb.back_menu(), parse_mode="Markdown")
    elif dest == "ai":
        from handlers.ai import ai_panel
        await ai_panel(q, ctx)
    elif dest == "img":
        await q.edit_message_text(
            "🖼 **تعديل وتحسين الصور**\n\nابعت أي صورة وسأعرض خيارات:\n✨ تحسين 2x / 🚀 تحسين 4x\n🗜 ضغط • ⚫ رمادي • 🔄 PNG/JPG/WEBP • 📐 تصغير",
            reply_markup=kb.back_menu(), parse_mode="Markdown")
    elif dest == "files":
        items = load_admin_files()
        if not items:
            await q.edit_message_text("📭 لا توجد ملفات أدمن بعد.", reply_markup=kb.back_menu())
            return
        await q.edit_message_text(f"📁 **ملفات الأدمن ({len(items)})**\nاختر ملفاً:", reply_markup=kb.files_menu(items), parse_mode="Markdown")
    elif dest == "set":
        quality = ctx.user_data.get("quality", "high")
        prog = ctx.user_data.get("show_progress", True)
        await q.edit_message_text("⚙️ **الإعدادات**", reply_markup=kb.settings_menu(quality, prog), parse_mode="Markdown")
    elif dest == "help":
        await q.edit_message_text(
            "📖 ابعت رابط → تفاصيل + تحميل\n📷 ابعت صورة → تعديل\n🤖 فعّل الذكاء ثم اسأل\n"
            f"الحد {config.MAX_FILE_MB}MB • /files • /ai • /clear",
            reply_markup=kb.back_menu())
