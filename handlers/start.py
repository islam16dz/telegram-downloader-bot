"""/start و /help"""
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_menu
import config


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.setdefault("quality", "high")
    ctx.user_data.setdefault("show_progress", True)
    ctx.user_data.setdefault("ai_mode", False)
    admin_hint = "\n🛠 أنت أدمن: ابعت أي ملف ليتخزن في /files" if update.effective_user.id in config.ADMIN_IDS else ""
    await update.message.reply_text(
        "👋 أهلاً بيك في **@IslamDownloaderBot**\n\n"
        "اختر قسماً من القائمة:\n"
        "📥 تحميل بالرابط (أعلى جودة / صوت)\n"
        "🤖 ذكاء اصطناعي (Gemini)\n"
        "🖼 تعديل الصور\n"
        "📁 ملفات الأدمن\n"
        f"{admin_hint}",
        reply_markup=main_menu(), parse_mode="Markdown",
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from keyboards import back_menu
    await update.message.reply_text(
        "📖 **المساعدة**\n\n"
        "• ابعت رابط فيديو → تفاصيل + 🎬/🎵\n"
        "• ابعت رابط مباشر → 📥 تحميل\n"
        "• ابعت صورة → قائمة تعديل (ضغط/تحويل/رمادي/تصغير)\n"
        "• فعّل 🤖 ثم اسأل أي سؤال\n"
        f"• الحد: {config.MAX_FILE_MB}MB للملف\n"
        "• /files ملفات الأدمن • /ai سؤال مباشر • /clear مسح سياق AI",
        reply_markup=back_menu(), parse_mode="Markdown",
    )
