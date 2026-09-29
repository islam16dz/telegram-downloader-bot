"""فحص سريع للتوكن بدون طباعته"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()
tok = os.getenv("BOT_TOKEN", "").strip()

if not tok or "ضع-التوكن" in tok or len(tok) < 20:
    print("❌ BOT_TOKEN مش متظبط في ملف .env - حط التوكن الجديد من @BotFather")
    exit(1)

print(f"ℹ️ التوكن موجود (طوله {len(tok)} حرف، أوله {tok[:4]}***)")
try:
    r = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=15).json()
    if r.get("ok"):
        print(f"✅ التوكن شغال! البوت: @{r['result'].get('username')} ({r['result'].get('first_name')})")
    else:
        print(f"❌ التوكن مرفوض من تليجرام: {r}")
        print("👉 روح @BotFather وطلع توكن جديد وحطه في .env")
except Exception as e:
    print(f"❌ خطأ اتصال: {e}")
