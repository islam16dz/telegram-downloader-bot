# @IslamDownloaderBot 🤖 — نسخة متقدمة

بوت تليجرام احترافي: 📥 تحميل | 🤖 ذكاء Gemini | 🖼 تعديل صور | 📁 ملفات أدمن | ⚙️ إعدادات. شغال 24/7 على Railway.

## الهيكلة النظيفة
```
bot.py              نقطة التشغيل وتسجيل المعالجات
config.py           الإعدادات من .env
keyboards.py        كل القوائم التفاعلية
handlers/           start, menu, download, ai, image, admin(settings+errors)
services/           downloader, ai_gemini, image_tools, store, helpers
data/               admin_files.json (file_id فقط)
```

## الميزات
1. **قوائم تفاعلية**: /start → أزرار (تحميل/ذكاء/صور/ملفات/إعدادات) مع زر رجوع.
2. **تحميل ضخم**: روابط مباشرة مقسمة + yt-dlp بأعلى جودة/صوت، شريط تقدم `████ 45%`، حذف تلقائي للملفات المؤقتة، حد تليجرام 50MB.
3. **ذكاء اصطناعي**: فعّل من القائمة ثم اسأل، سياق آخر 12 رسالة، تقسيم الردود الطويلة، `/ai سؤال` و `/clear`.
4. **صور**: ابعت صورة → ضغط / رمادي / PNG-JPG-WEBP / تصغير 800px (Pillow).
5. **أخطاء**: معالج عام يمنع توقف البوت.

## التشغيل المحلي
```bash
pip install -r requirements.txt
cp .env.example .env  # حط BOT_TOKEN + ADMIN_IDS + GEMINI_API_KEY
python bot.py
```

## مفتاح Gemini (اختياري)
1. https://aistudio.google.com/app/apikey → انسخ المفتاح
2. في `.env`: `GEMINI_API_KEY=...`
3. أعد التشغيل وفعّل 🤖 من القائمة.

## النشر الدائم Railway (جهازك مطفي عادي)
1. ارفع على GitHub (`.env` و `*.log` مستبعدة تلقائياً).
2. railway.app → New Project → من GitHub.
3. Variables: `BOT_TOKEN` `ADMIN_IDS` `MAX_FILE_MB=50` `GEMINI_API_KEY` `AI_MODEL=gemini-1.5-flash`
4. Deploy → Active. أوقف النسخة المحلية (`kill <pid>`) لمنع تعارض getUpdates.
