#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@IslamDownloaderBot — نسخة متقدمة بهيكلة نظيفة
أقسام: 📥 تحميل | 🤖 ذكاء Gemini | 🖼 صور | 📁 أدمن | ⚙️ إعدادات
تشغيل: pip install -r requirements.txt && cp .env.example .env && python bot.py
"""
import asyncio
import logging

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

import config
from handlers.start import start, help_cmd
from handlers.menu import on_menu
from handlers.download import on_text, on_download_btn
from handlers.ai import ai_toggle, ai_cmd, clear_cmd
from handlers.image import on_photo, on_image_btn
from handlers.admin import (
    files_cmd, admin_cmd, del_cmd, on_admin_file, on_getfile, on_settings, on_error,
)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("dl-bot")


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("❌ حط BOT_TOKEN في .env (شوف .env.example)")
    if not config.ADMIN_IDS:
        log.warning("⚠️ ADMIN_IDS فاضي — مميزات الأدمن معطلة")
    if not config.GEMINI_API_KEY:
        log.warning("⚠️ GEMINI_API_KEY ناقص — قسم الذكاء سيطلب المفتاح")

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("ai", ai_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))

    app.add_handler(CallbackQueryHandler(on_menu, pattern=r"^m:"))
    app.add_handler(CallbackQueryHandler(ai_toggle, pattern=r"^ai:"))
    app.add_handler(CallbackQueryHandler(on_settings, pattern=r"^set:"))
    app.add_handler(CallbackQueryHandler(on_getfile, pattern=r"^getfile\|"))
    app.add_handler(CallbackQueryHandler(on_download_btn, pattern=r"^dl:"))
    app.add_handler(CallbackQueryHandler(on_image_btn, pattern=r"^img:"))

    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.ATTACHMENT & ~filters.COMMAND, on_admin_file))

    app.add_error_handler(on_error)

    log.info("🤖 %s running | admin=%s | max=%dMB | ai=%s",
             config.BOT_NAME, config.ADMIN_IDS, config.MAX_FILE_MB,
             "on" if config.GEMINI_API_KEY else "off")
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
