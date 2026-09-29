"""قسم تعديل الصور"""
import uuid
from pathlib import Path
from telegram import Update, InputFile
from telegram.ext import ContextTypes
import config
import keyboards as kb


def _pending_img(ctx) -> dict:
    return ctx.bot_data.setdefault("pending_images", {})


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    f = await photo.get_file()
    key = uuid.uuid4().hex[:10]
    dest = Path(config.TEMP_ROOT) / f"img_{key}.jpg"
    await f.download_to_drive(str(dest))
    _pending_img(ctx)[key] = str(dest)
    await update.message.reply_photo(
        photo=photo.file_id,
        caption="🖼 اختر تعديلاً للصورة:",
        reply_markup=kb.image_menu(key))


async def on_image_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        op, key = q.data.split("|", 1)
        op = op.split(":")[1]
    except (ValueError, IndexError):
        return
    src = _pending_img(ctx).get(key)
    if not src or not Path(src).exists():
        await q.message.reply_text("⏳ الصورة انتهت. ابعتها مجدداً.")
        return
    status = await q.message.reply_text("🎨 جاري المعالجة...")
    try:
        from services.image_tools import process_image
        data = Path(src).read_bytes()
        out, fname, cap = process_image(data, op)
        await status.delete()
        await q.message.reply_document(document=InputFile(out, filename=fname), caption=f"✅ {cap}")
    except Exception as e:
        try:
            await status.edit_text(f"❌ خطأ معالجة الصورة:\n{e}")
        except Exception:
            pass
