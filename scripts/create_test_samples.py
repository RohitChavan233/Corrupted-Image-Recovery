import os
import io
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_samples():
    out_dir = Path("r:/GitHub EXp/Photorecover/test_samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create a pristine high-res JPEG image with an embedded EXIF thumbnail
    img = Image.new("RGB", (1200, 800), color=(24, 80, 160))
    draw = ImageDraw.Draw(img)
    # Draw geometric patterns & gradient-like bands
    for i in range(0, 800, 40):
        draw.line([(0, i), (1200, i)], fill=(40 + i // 4, 100, 180), width=3)
    draw.ellipse([400, 200, 800, 600], fill=(220, 160, 40), outline=(255, 255, 255), width=4)
    draw.rectangle([100, 100, 300, 400], fill=(40, 180, 90), outline=(255, 255, 255), width=2)
    draw.text((450, 380), "Photorecover Test Sample", fill=(255, 255, 255))
    
    # Generate thumbnail
    thumb = img.copy()
    thumb.thumbnail((160, 120))
    thumb_buf = io.BytesIO()
    thumb.save(thumb_buf, format="JPEG", quality=80)
    thumb_bytes = thumb_buf.getvalue()
    
    # Save standard JPEG
    main_buf = io.BytesIO()
    img.save(main_buf, format="JPEG", quality=95)
    main_bytes = main_buf.getvalue()
    
    # Construct JPEG with custom APP1 EXIF containing the embedded thumbnail
    # EXIF Header: b"Exif\x00\x00" + TIFF Header + thumbnail
    exif_header = b"Exif\x00\x00MM\x00*\x00\x00\x00\x08" # Big endian TIFF
    # Embed the raw thumbnail bytes inside the APP1 segment
    app1_payload = exif_header + b"\x00\x00" + thumb_bytes
    app1_length = len(app1_payload) + 2
    app1_marker = b"\xff\xe1" + struct.pack(">H", app1_length) + app1_payload
    
    # Inject APP1 after SOI (0xFFD8)
    jpeg_with_exif_thumb = main_bytes[:2] + app1_marker + main_bytes[2:]
    
    # 1. Normal Image with embedded thumbnail
    sample_normal = out_dir / "sample_nature.jpg"
    sample_normal.write_bytes(jpeg_with_exif_thumb)
    print(f"Created {sample_normal}")
    
    # 2. Corrupted Image: Truncated mid-scan (simulate damaged transfer / damaged SD card)
    # Cuts off at 55% of the file! Note: The APP1 embedded thumbnail is in the first 2% and is 100% intact!
    cut_point = int(len(jpeg_with_exif_thumb) * 0.55)
    truncated_bytes = jpeg_with_exif_thumb[:cut_point]
    sample_corrupted = out_dir / "corrupted_truncated_photo.jpg"
    sample_corrupted.write_bytes(truncated_bytes)
    print(f"Created {sample_corrupted} (truncated at 55%, missing EOI)")
    
    # 3. Missing EOI only (Premature EOF without 0xFFD9)
    # Remove last 2 bytes (0xFFD9)
    sample_missing_eoi = out_dir / "corrupted_missing_eoi.jpg"
    sample_missing_eoi.write_bytes(main_bytes[:-2])
    print(f"Created {sample_missing_eoi} (missing EOI termination)")
    
    # 4. Create Duplicate Images (Exact copy & Perceptual copy)
    sample_dup_exact = out_dir / "sample_nature_copy.jpg"
    sample_dup_exact.write_bytes(jpeg_with_exif_thumb)
    print(f"Created {sample_dup_exact} (exact SHA256 duplicate)")
    
    # Perceptually similar (slightly recompressed & smaller)
    perceptual_img = img.resize((960, 640))
    sample_dup_perceptual = out_dir / "sample_nature_web_version.jpg"
    perceptual_img.save(sample_dup_perceptual, format="JPEG", quality=75)
    print(f"Created {sample_dup_perceptual} (perceptual duplicate)")
    
    # 5. Other formats: PNG, WebP, BMP, GIF
    img.save(out_dir / "sample_graphic.png", format="PNG")
    img.save(out_dir / "sample_compressed.webp", format="WEBP", quality=80)
    img.resize((400, 300)).save(out_dir / "sample_legacy.bmp", format="BMP")
    img.resize((400, 300)).convert("P").save(out_dir / "sample_animated.gif", format="GIF")
    print("Created PNG, WebP, BMP, and GIF samples.")

if __name__ == "__main__":
    create_samples()
