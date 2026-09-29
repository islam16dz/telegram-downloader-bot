"""تخزين ملفات الأدمن (file_id فقط — بدون مساحة)"""
import json
from config import ADMIN_DB

def load_admin_files() -> list:
    if not ADMIN_DB.exists():
        return []
    try:
        import json as _j
        return _j.loads(ADMIN_DB.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_admin_files(items: list) -> None:
    ADMIN_DB.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
