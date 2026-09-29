"""قسم الذكاء الاصطناعي (Gemini) مع سياق"""
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import config
import keyboards as kb
from services.helpers import split_text


async def ai_panel(query_or_update, ctx: ContextTypes.DEFAULT_TYPE):
    ai_on = ctx.user_data.get("ai_mode", False)
    has_key = bool(config.GEMINI_API_KEY)
    txt = ("🤖 **الذكاء الاصطناعي**\n\n"
           + ("✅ المفتاح موجود." if has_key else "⚠️ ضع GEMINI_API_KEY في .env (من Google AI Studio).\n")
           + f"الحالة: {'🟢 يعمل — ابعت سؤالك' if ai_on else '🔴 متوقف — فعّله بالزر'}\n"
           + "الأوامر: /ai سؤال • /clear مسح السياق")
    markup = kb.ai_menu(ai_on, has_key)
    if hasattr(query_or_update, "edit_message_text"):
        await query_or_update.edit_message_text(txt, reply_markup=markup, parse_mode="Markdown")
    else:
        await query_or_update.message.reply_text(txt, reply_markup=markup, parse_mode="Markdown")


async def ai_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if "ai:clear" in (q.data or ""):
        ctx.user_data["ai_hist"] = []
        await q.edit_message_text("🧹 تم مسح سياق المحادثة.", reply_markup=kb.ai_menu(ctx.user_data.get("ai_mode", False), bool(config.GEMINI_API_KEY)))
        return
    on = q.data == "ai:on"
    if on and not config.GEMINI_API_KEY:
        await q.edit_message_text("⚠️ لا يوجد GEMINI_API_KEY.\nاحصل عليه من Google AI Studio وحطه في .env ثم أعد التشغيل.",
                                  reply_markup=kb.back_menu())
        return
    ctx.user_data["ai_mode"] = on
    await ai_panel(q, ctx)


async def ai_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(ctx.args or []).strip()
    if not prompt:
        await update.message.reply_text("استخدم: /ai ما هي عاصمة مصر؟")
        return
    await answer_ai(update, ctx, prompt)


async def clear_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["ai_hist"] = []
    await update.message.reply_text("🧹 تم مسح سياق الذكاء الاصطناعي.")


async def answer_ai(update_or_msg, ctx: ContextTypes.DEFAULT_TYPE, prompt: str):
    import asyncio as _aio
    from services.helpers import spin_frame
    msg = update_or_msg.message if hasattr(update_or_msg, "message") and update_or_msg.message else update_or_msg
    if not config.GEMINI_API_KEY:
        await msg.reply_text("⚠️ خدمة الذكاء غير مفعلة (GEMINI_API_KEY ناقص).", reply_markup=kb.back_menu())
        return
    wait = await msg.reply_text(f"{spin_frame(0)} بفكر...")
    stop = {"v": False}

    async def _think():
        i = 0
        dots = ["", ".", "..", "..."]
        while not stop["v"]:
            await _aio.sleep(1.2)
            i += 1
            try:
                await wait.edit_text(f"{spin_frame(i)} بفكر{dots[i % 4]}")
            except Exception:
                pass

    thinker = _aio.create_task(_think())
    try:
        from services.ai_gemini import ask_sync
        loop = _aio.get_running_loop()
        hist = ctx.user_data.get("ai_hist", [])
        text, new_hist = await loop.run_in_executor(None, ask_sync, config.GEMINI_API_KEY, config.AI_MODEL, hist, prompt)
        ctx.user_data["ai_hist"] = new_hist
        stop["v"] = True
        try:
            thinker.cancel()
        except Exception:
            pass
        await wait.delete()
        for part in split_text(text):
            await msg.reply_text(part)
    except Exception as e:
        stop["v"] = True
        try:
            thinker.cancel()
        except Exception:
            pass
        msg_err = str(e)
        if "429" in msg_err or "quota" in msg_err.lower():
            msg_err = "⚠️ تجاوزت الحصة المجانية حالياً. انتظر قليلاً وحاول مجدداً."
        try:
            await wait.edit_text(f"❌ خطأ الذكاء الاصطناعي:\n{msg_err}"[:1000])
        except Exception:
            pass
