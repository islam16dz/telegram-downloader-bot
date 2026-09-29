"""أدوات الصور بـ Pillow + تحسين الدقة"""
import io
from PIL import Image, ImageOps, ImageFilter, ImageEnhance


def _enhance(im: Image.Image) -> Image.Image:
    """تحسين التفاصيل والحدة (Detail + Sharpness + Contrast خفيف)."""
    im = im.filter(ImageFilter.DETAIL)
    im = ImageEnhance.Sharpness(im).enhance(1.6)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.05)
    return im


def _upscale(im: Image.Image, factor: int) -> Image.Image:
    w, h = im.size
    big = im.resize((w * factor, h * factor), Image.LANCZOS)
    return _enhance(big)


def _save(im: Image.Image, fmt: str = "JPEG", **kw) -> bytes:
    buf = io.BytesIO()
    im.save(buf, fmt, optimize=True, **kw)
    return buf.getvalue()


def process_image(src: bytes, op: str) -> tuple[bytes, str, str]:
    """يرجع (bytes, filename, caption). op: compress|gray|png|jpg|webp|resize|up2|up4"""
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
    if op in ("up2", "up4"):
        factor = 2 if op == "up2" else 4
        if im.mode == "P":
            im = im.convert("RGB")
        big = _upscale(im, factor)
        if big.mode == "RGBA":
            return _save(big, "PNG"), f"upscaled_{factor}x.png", f"✨ تم تحسين الدقة {factor}x"
        return _save(big.convert("RGB"), "JPEG", quality=90), f"upscaled_{factor}x.jpg", f"✨ تم تحسين الدقة {factor}x"
    # compress
    buf = io.BytesIO()
    if im.mode == "RGBA":
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), "compressed.png", "🗜 تم الضغط"
    im = im.convert("RGB")
    im.save(buf, "JPEG", quality=70, optimize=True)
    return buf.getvalue(), "compressed.jpg", "🗜 تم الضغط"
