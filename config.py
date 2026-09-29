"""الإعدادات المركزية للبوت — تُقرأ من .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_DB = DATA_DIR / "admin_files.json"
TEMP_ROOT = Path(os.getenv("TEMP_DIR", "/tmp/islambot")).resolve()
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS: list[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
MAX_FILE_MB: int = int(os.getenv("MAX_FILE_MB", "50"))
MAX_SEND_BYTES: int = MAX_FILE_MB * 1024 * 1024

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"

BOT_NAME = "@IslamDownloaderBot"
