"""أدوات الصور بـ Pillow"""
import io
from PIL import Image, ImageOps


def process_image(src: bytes, op: str) -> tuple[bytes, str, str]:
    """يرجع (bytes, filename, caption). op: compress|gray|png|jpg|webp|resize"""
    im = Image.open(io.BytesIO(src))
    if im.mode in ("RGBA", "P") and op in ("jpg", "compress"):
        im = im.convert("RGB")

    if op == "gray":
        im = ImageOps.grayscale(im)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), "gray.png", "⚫ فلتر رمادي"
    if op == "png":
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), "out.png", "🔄 تم التحويل إلى PNG"
    if op == "jpg":
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88, optimize=True)
        return buf.getvalue(), "out.jpg", "🔄 تم التحويل إلى JPG"
    if op == "webp":
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=85, method=6)
        return buf.getvalue(), "out.webp", "🔄 تم التحويل إلى WEBP"
    if op == "resize":
        im2 = im.copy()
        im2.thumbnail((800, 800))
        buf = io.BytesIO()
        fmt = "PNG" if im2.mode == "RGBA" else "JPEG"
        im2.save(buf, fmt, optimize=True)
        return buf.getvalue(), f"resized.{fmt.lower()}", "📐 تم التصغير لـ 800px"
    # compress
    buf = io.BytesIO()
    if im.mode == "RGBA":
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), "compressed.png", "🗜 تم الضغط"
    im = im.convert("RGB")
    im.save(buf, "JPEG", quality=70, optimize=True)
    return buf.getvalue(), "compressed.jpg", "🗜 تم الضغط"
