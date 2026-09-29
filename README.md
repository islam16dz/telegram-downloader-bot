# بوت تليجرام للتحميل بالرابط 🤖

ابعت رابط فقط → يعرض التفاصيل → حمل 🎬 أعلى جودة أو 🎵 صوت فقط.
+ روابط مباشرة 📦 + ملفات أدمن 📁. شغال 24/7 حتى وجهازك مطفي (استضافة سحابية).

## 1) طلع التوكن والـ ID (دقيقة واحدة)

1. من تليجرام كلم `@BotFather` → `/newbot` → انسخ التوكن.
2. كلم `@userinfobot` → انسخ رقم الـ ID بتاعك (ده الـ ADMIN_IDS).

## 2) شغله محلياً للتجربة

```bash
cd telegram-downloader-bot
pip install -r requirements.txt
cp .env.example .env
# افتح .env وحط BOT_TOKEN و ADMIN_IDS
python bot.py
```

جرب في تليجرام: ابعت رابط يوتيوب → هيظهر زرارين.

> لازم `ffmpeg` متسطب عندك للدمج وتحويل MP3:
> Ubuntu: `sudo apt install ffmpeg` | Windows: نزله من ffmpeg.org وحطه في PATH.

## 3) شغله دائماً (جهازك مطفي عادي) — Railway مجاني

1. ارفع المجلد ده على GitHub (اعمل repo جديد وضيف الملفات).
2. ادخل https://railway.app → New Project → Deploy from GitHub → اختر الريبو.
3. Variables → ضيف:
   - `BOT_TOKEN` = التوكن
   - `ADMIN_IDS` = الآي دي بتاعك
   - `MAX_FILE_MB` = 50
4. Deploy → البوت هيفضل شغال 24/7. أي تحديث على GitHub بيتعمل Redeploy تلقائي.

### بديل: Render مجاني
1. https://render.com → New → Background Worker → اختر الريبو.
2. Runtime: Docker، Dockerfile موجود جاهز.
3. ضيف نفس الـ Environment Variables → Deploy.

## 4) الاستخدام

- ابعت أي رابط فيديو → صورة + عنوان + مدة + حجم → اختر 🎬 أو 🎵
- ابعت رابط مباشر (`.pdf .zip .apk ...`) → الاسم والحجم → 📥 تحميل
- 👑 أدمن: ابعت أي ملف للبوت وهيتخزن → الأعضاء يجيبوه من `/files`
- `/admin` إحصائيات • `/del 1` حذف • `/help` مساعدة

## 5) ملاحظات مهمة

- حد تليجرام للبوتات **50MB** للملف. لو الفيديو أكبر، البوت هيقولك وجرب الصوت فقط.
- انستا/تيك توك أحياناً بيحتاجوا تحديث `yt-dlp`: شغل `pip install -U yt-dlp` أو اعمل Redeploy.
- ملفات الأدمن محفوظة في `data/admin_files.json` (file_id مش الملف نفسه، فمبتاخدش مساحة).
