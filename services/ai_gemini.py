"""تكامل Gemini مع سياق محادثة"""
from collections import deque

MAX_HIST = 12


def ask_sync(api_key: str, model_name: str, history: list[dict], prompt: str) -> tuple[str, list[dict]]:
    """يعمل في Thread. يرجع (الرد, الهيستوري الجديد)."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    chat = model.start_chat(history=history[-MAX_HIST:] if history else [])
    resp = chat.send_message(prompt)
    text = (resp.text or "").strip() or "لم يصل رد من النموذج."
    new_hist = list(history[-MAX_HIST:]) + [
        {"role": "user", "parts": [prompt[:2000]]},
        {"role": "model", "parts": [text[:2000]]},
    ]
    return text, new_hist
