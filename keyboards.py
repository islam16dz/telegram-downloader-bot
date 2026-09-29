"""لوحات المفاتيح التفاعلية — كل القوائم في مكان واحد"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def main_menu(webapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📥 قسم التحميل", callback_data="m:dl"),
         InlineKeyboardButton("🤖 الذكاء الاصطناعي", callback_data="m:ai")],
        [InlineKeyboardButton("🖼 تعديل الصور", callback_data="m:img"),
         InlineKeyboardButton("📁 ملفات الأدمن", callback_data="m:files")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="m:set"),
         InlineKeyboardButton("❓ مساعدة", callback_data="m:help")],
    ]
    if webapp_url:
        rows.append([InlineKeyboardButton("🌐 لوحة التحكم", web_app=WebAppInfo(url=webapp_url))])
    return InlineKeyboardMarkup(rows)


def back_menu(extra: list | None = None) -> InlineKeyboardMarkup:
    rows = extra or []
    rows = [list(r) for r in rows]
    rows.append([InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")])
    return InlineKeyboardMarkup(rows)


def download_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 فيديو أعلى جودة", callback_data=f"dl:vid|{key}")],
        [InlineKeyboardButton("🎵 صوت فقط MP3", callback_data=f"dl:aud|{key}")],
        [InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")],
    ])


def direct_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 تحميل الملف", callback_data=f"dl:direct|{key}")],
        [InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")],
    ])


def image_menu(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ تحسين 2x", callback_data=f"img:up2|{key}"),
         InlineKeyboardButton("🚀 تحسين 4x", callback_data=f"img:up4|{key}")],
        [InlineKeyboardButton("🗜 ضغط", callback_data=f"img:compress|{key}"),
         InlineKeyboardButton("⚫ رمادي", callback_data=f"img:gray|{key}")],
        [InlineKeyboardButton("🔄 PNG", callback_data=f"img:png|{key}"),
         InlineKeyboardButton("🔄 JPG", callback_data=f"img:jpg|{key}"),
         InlineKeyboardButton("🔄 WEBP", callback_data=f"img:webp|{key}")],
        [InlineKeyboardButton("📐 تصغير 800px", callback_data=f"img:resize|{key}")],
        [InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")],
    ])


def ai_menu(ai_on: bool, has_key: bool) -> InlineKeyboardMarkup:
    toggle = "🔴 إيقاف الذكاء" if ai_on else "🟢 تفعيل الذكاء"
    cb = "ai:off" if ai_on else "ai:on"
    rows = [
        [InlineKeyboardButton(toggle, callback_data=cb),
         InlineKeyboardButton("🧹 مسح السياق", callback_data="ai:clear")],
        [InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")],
    ]
    return InlineKeyboardMarkup(rows)


def settings_menu(quality: str, prog: bool) -> InlineKeyboardMarkup:
    q = "🎬 عالية" if quality == "high" else "📦 متوسطة"
    p = "🔔 التقدم: يعمل" if prog else "🔕 التقدم: متوقف"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"الجودة: {q}", callback_data="set:qtoggle")],
        [InlineKeyboardButton(p, callback_data="set:ptoggle")],
        [InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")],
    ])


def files_menu(items: list) -> InlineKeyboardMarkup:
    from services.helpers import fmt_bytes
    rows = []
    for i, it in enumerate(items[:30]):
        rows.append([InlineKeyboardButton(
            f"{i+1}. {it.get('name','ملف')} ({fmt_bytes(it.get('size'))})",
            callback_data=f"getfile|{i}")])
    rows.append([InlineKeyboardButton("◀️ القائمة الرئيسية", callback_data="m:main")])
    return InlineKeyboardMarkup(rows)
