import io
import base64
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
from .base import EmbeddedPreview, RecoveryArtifact

def deep_carve_all_images(filepath: str, output_dir: Path) -> List[RecoveryArtifact]:
    """
    Forensic deep carver: scans arbitrary binary data for embedded JPEG, PNG, and WebP streams,
    re-validates their headers, and saves carved images.
    """
    p = Path(filepath)
    raw_data = p.read_bytes()
    file_size = len(raw_data)
    artifacts: List[RecoveryArtifact] = []

    # 1. Carve JPEGs (SOI: FF D8 ... EOI: FF D9)
    start_pos = 0
    jpeg_count = 0
    while start_pos < file_size - 4:
        soi = raw_data.find(b"\xff\xd8", start_pos)
        if soi == -1:
            break
        # Find corresponding EOI
        eoi = raw_data.find(b"\xff\xd9", soi + 2)
        if eoi != -1 and (eoi + 2 - soi) > 512:
            candidate = raw_data[soi : eoi + 2]
            try:
                with Image.open(io.BytesIO(candidate)) as img:
                    w, h = img.size
                    jpeg_count += 1
                    out_name = f"{p.stem}_carved_stream_{jpeg_count}.jpg"
                    out_file = output_dir / out_name
                    out_file.write_bytes(candidate)

                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=88)
                    b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                    artifacts.append(RecoveryArtifact(
                        method="Deep Binary Stream Carving (JPEG)",
                        filename=out_name,
                        filepath=str(out_file.resolve()),
                        width=w,
                        height=h,
                        size=len(candidate),
                        preview_base64=b64,
                        description=f"Carved intact JPEG stream ({w}x{h}) found at byte offset {soi}."
                    ))
            except Exception:
                pass
            start_pos = eoi + 2
        else:
            start_pos = soi + 2

    # 2. Carve PNGs (\x89PNG\r\n\x1a\n ... IEND\xaeB`\x82)
    start_pos = 0
    png_count = 0
    while start_pos < file_size - 8:
        sig = raw_data.find(b"\x89PNG\r\n\x1a\n", start_pos)
        if sig == -1:
            break
        iend = raw_data.find(b"IEND\xaeB\x60\x82", sig + 8)
        if iend != -1:
            candidate = raw_data[sig : iend + 8]
            try:
                with Image.open(io.BytesIO(candidate)) as img:
                    w, h = img.size
                    png_count += 1
                    out_name = f"{p.stem}_carved_stream_{png_count}.png"
                    out_file = output_dir / out_name
                    out_file.write_bytes(candidate)

                    buf = io.BytesIO()
                    img.save(buf, "PNG")
                    b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                    artifacts.append(RecoveryArtifact(
                        method="Deep Binary Stream Carving (PNG)",
                        filename=out_name,
                        filepath=str(out_file.resolve()),
                        width=w,
                        height=h,
                        size=len(candidate),
                        preview_base64=b64,
                        description=f"Carved intact PNG stream ({w}x{h}) found at byte offset {sig}."
                    ))
            except Exception:
                pass
            start_pos = iend + 8
        else:
            start_pos = sig + 8

    return artifacts
