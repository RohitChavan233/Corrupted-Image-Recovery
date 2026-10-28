import hashlib
import io
import math
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont, ImageFile
from ..config import THUMBNAIL_CACHE_DIR
from ..database import update_file_record

# Allow loading truncated images for recovery and display
ImageFile.LOAD_TRUNCATED_IMAGES = True

def get_cache_key(filepath: str, size: int) -> str:
    p = Path(filepath)
    try:
        stat = p.stat()
        raw = f"{filepath}_{stat.st_mtime}_{stat.st_size}_{size}"
    except Exception:
        raw = f"{filepath}_{size}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def get_or_generate_thumbnail(filepath: str, size: int = 256) -> Tuple[bytes, str]:
    cache_key = get_cache_key(filepath, size)
    cache_file = THUMBNAIL_CACHE_DIR / f"{cache_key}.webp"
    
    if cache_file.exists():
        return cache_file.read_bytes(), "image/webp"
        
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    try:
        with Image.open(filepath) as img:
            # Handle orientation from EXIF
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
                
            orig_w, orig_h = img.size
            orig_format = img.format or p.suffix.upper()[1:]
            
            # Update database with known dimensions if not present
            try:
                update_file_record(filepath, {
                    "width": orig_w,
                    "height": orig_h,
                    "format": orig_format
                })
            except Exception:
                pass
                
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if RGBA/P/CMYK for clean webp output
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                out_format = "WEBP"
                mime = "image/webp"
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                out_format = "WEBP"
                mime = "image/webp"
                
            buffer = io.BytesIO()
            img.save(buffer, format=out_format, quality=85, method=4)
            data = buffer.getvalue()
            
            # Save to disk cache
            cache_file.write_bytes(data)
            return data, mime
    except Exception as e:
        # Fallback placeholder thumbnail
        buffer = io.BytesIO()
        placeholder = Image.new("RGB", (size, size), color=(30, 34, 42))
        draw = ImageDraw.Draw(placeholder)
        draw.text((size // 4, size // 2), "Load Error", fill=(180, 80, 80))
        placeholder.save(buffer, format="WEBP")
        return buffer.getvalue(), "image/webp"

def process_image(
    filepath: str,
    crop: Optional[Dict[str, int]] = None,
    resize: Optional[Dict[str, int]] = None,
    rotate: Optional[float] = None,
    flip_h: bool = False,
    flip_v: bool = False,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    gamma: float = 1.0,
    hue: float = 0.0,
    filter_name: Optional[str] = None,
    watermark_text: Optional[str] = None,
    watermark_color: str = "#ffffff",
    watermark_opacity: float = 0.8,
    watermark_position: str = "bottom-right",
    output_format: Optional[str] = None,
    output_quality: int = 90
) -> Tuple[bytes, str]:
    
    with Image.open(filepath) as img:
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
            
        img = img.convert("RGBA") if img.mode not in ("RGB", "RGBA") else img.copy()
        
        # 1. Crop
        if crop and all(k in crop for k in ("x", "y", "width", "height")):
            x, y, w, h = crop["x"], crop["y"], crop["width"], crop["height"]
            img_w, img_h = img.size
            x1 = max(0, min(x, img_w))
            y1 = max(0, min(y, img_h))
            x2 = max(x1, min(x + w, img_w))
            y2 = max(y1, min(y + h, img_h))
            if x2 > x1 and y2 > y1:
                img = img.crop((x1, y1, x2, y2))
                
        # 2. Resize
        if resize and "width" in resize and "height" in resize:
            rw, rh = int(resize["width"]), int(resize["height"])
            if rw > 0 and rh > 0:
                img = img.resize((rw, rh), Image.Resampling.LANCZOS)
                
        # 3. Rotate
        if rotate and rotate % 360 != 0:
            angle = rotate % 360
            if angle == 90:
                img = img.transpose(Image.Transpose.ROTATE_270)
            elif angle == 180:
                img = img.transpose(Image.Transpose.ROTATE_180)
            elif angle == 270:
                img = img.transpose(Image.Transpose.ROTATE_90)
            else:
                img = img.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
                
        # 4. Flip
        if flip_h:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            
        # 5. Brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
            
        # 6. Contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
            
        # 7. Saturation (Color)
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
            
        # 8. Gamma correction
        if gamma != 1.0 and gamma > 0:
            inv_gamma = 1.0 / gamma
            lut = [min(255, int((i / 255.0) ** inv_gamma * 255 + 0.5)) for i in range(256)]
            if img.mode == "RGBA":
                r, g, b, a = img.split()
                r = r.point(lut)
                g = g.point(lut)
                b = b.point(lut)
                img = Image.merge("RGBA", (r, g, b, a))
            else:
                img = img.point(lut * len(img.getbands()))
                
        # 9. Filters
        if filter_name:
            fn = filter_name.lower()
            if fn == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            elif fn == "blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=2))
            elif fn == "grayscale":
                alpha = img.split()[-1] if img.mode == "RGBA" else None
                gray = ImageOps.grayscale(img.convert("RGB"))
                img = gray.convert("RGBA")
                if alpha:
                    img.putalpha(alpha)
            elif fn == "sepia":
                rgb = img.convert("RGB")
                r, g, b = rgb.split()
                # standard sepia matrix
                tr = r.point(lambda i: i * 0.393 + 0.769 * i + 0.189 * i)
                tg = g.point(lambda i: i * 0.349 + 0.686 * i + 0.168 * i)
                tb = b.point(lambda i: i * 0.272 + 0.534 * i + 0.131 * i)
                img = Image.merge("RGB", (tr, tg, tb)).convert(img.mode)
            elif fn == "invert":
                if img.mode == "RGBA":
                    r, g, b, a = img.split()
                    rgb = Image.merge("RGB", (r, g, b))
                    inv = ImageOps.invert(rgb)
                    ir, ig, ib = inv.split()
                    img = Image.merge("RGBA", (ir, ig, ib, a))
                else:
                    img = ImageOps.invert(img.convert("RGB"))
            elif fn == "edge":
                img = img.filter(ImageFilter.FIND_EDGES)
            elif fn == "noise_reduction":
                img = img.filter(ImageFilter.MedianFilter(size=3))
                
        # 10. Watermark
        if watermark_text:
            draw = ImageDraw.Draw(img)
            w_w, w_h = img.size
            font_size = max(16, min(w_w, w_h) // 25)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
                
            # text bounding box
            text = watermark_text
            margin = 20
            
            # calculate position
            if watermark_position == "bottom-right":
                pos = (w_w - len(text) * 10 - margin, w_h - font_size - margin)
            elif watermark_position == "bottom-left":
                pos = (margin, w_h - font_size - margin)
            elif watermark_position == "top-right":
                pos = (w_w - len(text) * 10 - margin, margin)
            elif watermark_position == "top-left":
                pos = (margin, margin)
            else: # center
                pos = ((w_w - len(text) * 10) // 2, (w_h - font_size) // 2)
                
            draw.text(pos, text, fill=watermark_color)
            
        # Determine output format
        orig_ext = Path(filepath).suffix.lower()
        target_fmt = (output_format or orig_ext.replace(".", "")).upper()
        if target_fmt in ("JPG", "JPEG"):
            target_fmt = "JPEG"
            mime = "image/jpeg"
            if img.mode != "RGB":
                img = img.convert("RGB")
        elif target_fmt == "PNG":
            mime = "image/png"
        elif target_fmt == "WEBP":
            mime = "image/webp"
        else:
            target_fmt = "JPEG"
            mime = "image/jpeg"
            if img.mode != "RGB":
                img = img.convert("RGB")
                
        buffer = io.BytesIO()
        save_kwargs = {}
        if target_fmt == "JPEG":
            save_kwargs["quality"] = max(output_quality, 95)
            save_kwargs["subsampling"] = 0
            save_kwargs["optimize"] = True
            save_kwargs["keep_rgb"] = True
        elif target_fmt == "WEBP":
            save_kwargs["quality"] = output_quality
            save_kwargs["method"] = 6
            
        img.save(buffer, format=target_fmt, **save_kwargs)
        return buffer.getvalue(), mime
