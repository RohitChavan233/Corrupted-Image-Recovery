import io
import struct
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
from .base import Severity, DiagnosticIssue, MarkerSegment, RecoveryArtifact, ImageAnalysisResult

def analyze_bmp_deep(filepath: str) -> ImageAnalysisResult:
    p = Path(filepath)
    raw_data = p.read_bytes()
    file_size = len(raw_data)

    issues: List[DiagnosticIssue] = []
    segments: List[MarkerSegment] = []
    available_repairs: List[str] = []

    if file_size < 14 + 40:
        return ImageAnalysisResult(
            filepath=filepath,
            filename=p.name,
            file_size=file_size,
            image_format="BMP",
            is_corrupt=True,
            integrity_score=0,
            issues=[DiagnosticIssue("ERR_FILE_TOO_SMALL", "File too small to contain valid BITMAPFILEHEADER and DIB header.", Severity.CRITICAL)],
            decode_error="File is too small"
        )

    # 1. Check Magic bytes 'BM' (0x42, 0x4D)
    has_bm = raw_data.startswith(b"BM")
    if has_bm:
        segments.append(MarkerSegment(0, 2, "MAGIC_BM", "BMP Signature", "Valid Windows Bitmap header signature", True, "42 4D"))
    else:
        issues.append(DiagnosticIssue(
            "ERR_MISSING_BM_MAGIC",
            "Missing 'BM' (0x42 0x4D) signature in header.",
            Severity.CRITICAL,
            0,
            2,
            "Inject 'BM' magic bytes."
        ))
        available_repairs.append("repair_bmp_header")

    # 2. Parse BITMAPFILEHEADER (14 bytes)
    reported_file_size = struct.unpack("<I", raw_data[2:6])[0]
    pixel_offset = struct.unpack("<I", raw_data[10:14])[0]

    segments.append(MarkerSegment(2, 4, "BF_SIZE", "Reported File Size", f"{reported_file_size} bytes", True))
    segments.append(MarkerSegment(10, 4, "BF_OFFBITS", "Pixel Data Offset", f"Offset: {pixel_offset}", True))

    if pixel_offset >= file_size or pixel_offset < 54:
        issues.append(DiagnosticIssue(
            "ERR_INVALID_PIXEL_OFFSET",
            f"Pixel data offset (bfOffBits={pixel_offset}) is out of bounds or smaller than minimum 54 bytes.",
            Severity.CRITICAL,
            10,
            4,
            "Recalculate standard 54-byte pixel offset."
        ))
        available_repairs.append("repair_bmp_header")

    # 3. Parse BITMAPINFOHEADER (offset 14, standard 40 bytes)
    header_size = struct.unpack("<I", raw_data[14:18])[0]
    segments.append(MarkerSegment(14, 4, "BI_SIZE", "DIB Header Size", f"{header_size} bytes", True))

    width = 0
    height = 0
    if 18 + 8 <= file_size:
        width = struct.unpack("<i", raw_data[18:22])[0]
        height = struct.unpack("<i", raw_data[22:26])[0]
        planes = struct.unpack("<H", raw_data[26:28])[0]
        bpp = struct.unpack("<H", raw_data[28:30])[0]

        segments.append(MarkerSegment(18, 4, "BI_WIDTH", "Image Width", f"{width} px", True))
        segments.append(MarkerSegment(22, 4, "BI_HEIGHT", "Image Height", f"{height} px", True))
        segments.append(MarkerSegment(28, 2, "BI_BITCOUNT", "Bits Per Pixel", f"{bpp} bpp", True))

        if width <= 0 or abs(height) <= 0:
            issues.append(DiagnosticIssue("ERR_INVALID_BMP_DIMENSIONS", f"Invalid width ({width}) or height ({height}).", Severity.CRITICAL))

    # 4. Test Decode
    decode_success = False
    decode_error = None
    try:
        with Image.open(io.BytesIO(raw_data)) as test_img:
            width, height = test_img.size
            test_img.load()
            decode_success = True
    except Exception as e:
        decode_error = str(e)
        issues.append(DiagnosticIssue("ERR_DECODE_FAILED", f"BMP decoding failed: {decode_error}", Severity.CRITICAL))

    score = 100
    for iss in issues:
        if iss.severity == Severity.CRITICAL:
            score -= 35
        elif iss.severity == Severity.WARNING:
            score -= 15

    integrity_score = max(0, min(score, 100))
    is_corrupted = integrity_score < 95 or len(issues) > 0

    return ImageAnalysisResult(
        filepath=filepath,
        filename=p.name,
        file_size=file_size,
        image_format="BMP",
        is_corrupt=is_corrupted,
        integrity_score=integrity_score,
        issues=issues,
        segments=segments,
        embedded_previews=[],
        decode_success=decode_success,
        decode_partial=False,
        decoded_width=width,
        decoded_height=abs(height),
        decode_error=decode_error,
        recoverable=len(available_repairs) > 0 or not decode_success,
        available_repairs=list(set(available_repairs))
    )

def repair_bmp_advanced(filepath: str, action: str, output_dir: Path) -> List[RecoveryArtifact]:
    p = Path(filepath)
    raw_data = bytearray(p.read_bytes())
    artifacts: List[RecoveryArtifact] = []

    # Inject 'BM' if missing
    if not raw_data.startswith(b"BM"):
        raw_data[0:2] = b"BM"

    # Set accurate file size
    raw_data[2:6] = struct.pack("<I", len(raw_data))

    # Set standard 54-byte pixel offset if corrupt
    pixel_offset = struct.unpack("<I", raw_data[10:14])[0]
    if pixel_offset >= len(raw_data) or pixel_offset < 54:
        raw_data[10:14] = struct.pack("<I", 54)

    try:
        with Image.open(io.BytesIO(raw_data)) as test_img:
            w, h = test_img.size
            out_name = f"{p.stem}_recovered.bmp"
            out_file = output_dir / out_name
            test_img.save(str(out_file), "BMP")

            buf = io.BytesIO()
            test_img.save(buf, "PNG")
            b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

            artifacts.append(RecoveryArtifact(
                method="BMP Header Reconstruction",
                filename=out_name,
                filepath=str(out_file.resolve()),
                width=w,
                height=h,
                size=out_file.stat().st_size,
                preview_base64=b64,
                description="Reconstructed BITMAPFILEHEADER, valid 'BM' signature, and pixel offset."
            ))
    except Exception:
        pass

    return artifacts
