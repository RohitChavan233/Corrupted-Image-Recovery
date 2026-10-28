import io
import struct
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageFile
from .base import Severity, DiagnosticIssue, MarkerSegment, EmbeddedPreview, RecoveryArtifact, ImageAnalysisResult

ImageFile.LOAD_TRUNCATED_IMAGES = True

JPEG_MARKERS = {
    0xFFD8: ("SOI", "Start of Image"),
    0xFFE0: ("APP0", "JFIF Application Header"),
    0xFFE1: ("APP1", "EXIF / XMP Metadata & Preview"),
    0xFFE2: ("APP2", "ICC Color Profile"),
    0xFFDB: ("DQT", "Define Quantization Table"),
    0xFFC0: ("SOF0", "Start of Frame (Baseline DCT)"),
    0xFFC1: ("SOF1", "Start of Frame (Extended Sequential)"),
    0xFFC2: ("SOF2", "Start of Frame (Progressive DCT)"),
    0xFFC4: ("DHT", "Define Huffman Table"),
    0xFFDD: ("DRI", "Define Restart Interval"),
    0xFFDA: ("SOS", "Start of Scan (Compressed Scanlines)"),
    0xFFD9: ("EOI", "End of Image (Termination)")
}

# Standard JPEG Annex K Baseline Luminance Quantization Table (Table 0)
STD_LUMA_DQT = bytes([
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99
])

# Standard JPEG Annex K Baseline Chrominance Quantization Table (Table 1)
STD_CHROMA_DQT = bytes([
    17, 18, 24, 47, 99, 99, 99, 99,
    18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99,
    47, 66, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99
])

# Standard JPEG Annex K Baseline DC Luminance Huffman Table (Table 0, Class 0)
STD_DC_LUMA_DHT = bytes.fromhex(
    "0000010501010101010100000000000000"
    "000102030405060708090a0b"
)

# Standard JPEG Annex K Baseline AC Luminance Huffman Table (Table 0, Class 1)
STD_AC_LUMA_DHT = bytes.fromhex(
    "100002010303020403050504040000017d"
    "01020300041105122131410613516107227114328191a1082342b1c11552d1f024"
    "33627282090a161718191a25262728292a3435363738393a434445464748494a53"
    "5455565758595a636465666768696a737475767778797a838485868788898a9293"
    "9495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9"
    "cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9fa"
)

# Standard JPEG Annex K Baseline DC Chrominance Huffman Table (Table 1, Class 0)
STD_DC_CHROMA_DHT = bytes.fromhex(
    "0100030101010101010101010000000000"
    "000102030405060708090a0b"
)

# Standard JPEG Annex K Baseline AC Chrominance Huffman Table (Table 1, Class 1)
STD_AC_CHROMA_DHT = bytes.fromhex(
    "1100020102040403040705040400010277"
    "000102031104052131061241510761711322328108144291a1b1c109233352f015"
    "6272d10a162434e125f11718191a262728292a35363738393a434445464748494a"
    "535455565758595a636465666768696a737475767778797a82838485868788898a"
    "92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7"
    "c8c9cad2d3d4d5d6d7d8d9dae2e3e4e5e6e7e8e9eaf2f3f4f5f6f7f8f9fa"
)

def build_standard_dqt_marker() -> bytes:
    dqt0 = b"\x00" + STD_LUMA_DQT
    dqt1 = b"\x01" + STD_CHROMA_DQT
    return (
        b"\xff\xdb" + struct.pack(">H", len(dqt0) + 2) + dqt0 +
        b"\xff\xdb" + struct.pack(">H", len(dqt1) + 2) + dqt1
    )

def build_standard_dht_marker() -> bytes:
    return (
        b"\xff\xc4" + struct.pack(">H", len(STD_DC_LUMA_DHT) + 2) + STD_DC_LUMA_DHT +
        b"\xff\xc4" + struct.pack(">H", len(STD_AC_LUMA_DHT) + 2) + STD_AC_LUMA_DHT +
        b"\xff\xc4" + struct.pack(">H", len(STD_DC_CHROMA_DHT) + 2) + STD_DC_CHROMA_DHT +
        b"\xff\xc4" + struct.pack(">H", len(STD_AC_CHROMA_DHT) + 2) + STD_AC_CHROMA_DHT
    )

def build_standard_jfif_marker() -> bytes:
    return b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"

def build_standard_sof0_marker(width: int = 1200, height: int = 800, subsampling: str = "4:2:0") -> bytes:
    # 8-bit precision, height, width, color components
    if subsampling == "4:2:2":
        comps = b"\x01\x21\x00\x02\x11\x01\x03\x11\x01" # 2x1 Y, 1x1 Cb, 1x1 Cr
    elif subsampling == "4:4:4":
        comps = b"\x01\x11\x00\x02\x11\x01\x03\x11\x01" # 1x1 Y, 1x1 Cb, 1x1 Cr
    elif subsampling == "grayscale":
        payload = struct.pack(">BHHB", 8, max(height, 100), max(width, 100), 1) + b"\x01\x11\x00"
        return b"\xff\xc0" + struct.pack(">H", len(payload) + 2) + payload
    else: # 4:2:0 standard
        comps = b"\x01\x22\x00\x02\x11\x01\x03\x11\x01" # 2x2 Y, 1x1 Cb, 1x1 Cr
    payload = struct.pack(">BHHB", 8, max(height, 100), max(width, 100), 3) + comps
    return b"\xff\xc0" + struct.pack(">H", len(payload) + 2) + payload

def analyze_jpeg_deep(filepath: str) -> ImageAnalysisResult:
    p = Path(filepath)
    raw_data = p.read_bytes()
    file_size = len(raw_data)
    
    issues: List[DiagnosticIssue] = []
    segments: List[MarkerSegment] = []
    embedded_previews: List[EmbeddedPreview] = []
    available_repairs: List[str] = []
    
    if file_size < 4:
        return ImageAnalysisResult(
            filepath=filepath,
            filename=p.name,
            file_size=file_size,
            image_format="JPEG",
            is_corrupt=True,
            integrity_score=0,
            issues=[DiagnosticIssue("ERR_FILE_TOO_SMALL", "File is smaller than 4 bytes, invalid image header.", Severity.CRITICAL, 0, file_size)],
            decode_error="File is too small"
        )

    # 1. Check SOI
    has_soi = raw_data.startswith(b"\xff\xd8")
    if has_soi:
        segments.append(MarkerSegment(0, 2, "0xFFD8", "SOI (Start of Image)", "Valid Start of Image marker", True, "FF D8"))
    else:
        # Search if SOI exists deeper inside (prepended junk or offset shift)
        found_soi = raw_data.find(b"\xff\xd8")
        if found_soi != -1:
            issues.append(DiagnosticIssue(
                "WARN_SOI_SHIFTED",
                f"SOI marker found at offset {found_soi} instead of 0. Leading {found_soi} bytes of junk/padding detected.",
                Severity.CRITICAL,
                0,
                found_soi,
                "Strip leading padding to realign file header."
            ))
            available_repairs.append("strip_leading_junk")
        else:
            issues.append(DiagnosticIssue(
                "ERR_MISSING_SOI",
                "Missing SOI (0xFFD8) marker at beginning of file. Corrupted header or invalid format.",
                Severity.CRITICAL,
                0,
                2,
                "Graft standard JPEG baseline header."
            ))
            available_repairs.append("graft_baseline_header")

    # 2. Parse Markers
    idx = 2 if has_soi else (raw_data.find(b"\xff\xd8") + 2 if raw_data.find(b"\xff\xd8") != -1 else 0)
    has_dqt = False
    has_dht = False
    has_sof = False
    has_sos = False
    has_eoi = False
    sos_offset = -1
    sos_length = 0

    while idx < file_size - 1:
        if raw_data[idx] == 0xFF:
            marker_byte = raw_data[idx + 1]
            marker_val = 0xFF00 | marker_byte

            # Skip fill bytes (FF FF) or escaped zero (FF 00)
            if marker_byte in (0xFF, 0x00):
                idx += 1
                continue
            # Restart markers RST0-RST7 (FF D0 - FF D7)
            elif 0xD0 <= marker_byte <= 0xD7:
                segments.append(MarkerSegment(idx, 2, f"0x{marker_val:04X}", f"RST{marker_byte - 0xD0}", "Restart interval sync", True, f"FF {marker_byte:02X}"))
                idx += 2
                continue
            # EOI marker (FF D9)
            elif marker_val == 0xFFD9:
                has_eoi = True
                segments.append(MarkerSegment(idx, 2, "0xFFD9", "EOI (End of Image)", "Valid file termination", True, "FF D9"))
                idx += 2
                break
            # Unexpected duplicate SOI
            elif marker_val == 0xFFD8:
                segments.append(MarkerSegment(idx, 2, "0xFFD8", "Duplicate SOI", "Secondary image stream start", True, "FF D8"))
                idx += 2
                continue

            # Standard markers with length prefix
            if idx + 4 <= file_size:
                length = struct.unpack(">H", raw_data[idx + 2 : idx + 4])[0]
                code_name, desc = JPEG_MARKERS.get(marker_val, (f"0x{marker_val:04X}", f"Application Segment 0x{marker_val:04X}"))
                hex_prev = " ".join(f"{b:02X}" for b in raw_data[idx : min(idx + 12, file_size)])
                
                seg = MarkerSegment(idx, length + 2, f"0x{marker_val:04X}", f"{code_name} ({desc})", f"Payload size: {length} bytes", True, hex_prev)
                segments.append(seg)

                if marker_val == 0xFFDB:
                    has_dqt = True
                elif marker_val in (0xFFC0, 0xFFC1, 0xFFC2):
                    has_sof = True
                elif marker_val == 0xFFC4:
                    has_dht = True
                elif marker_val == 0xFFE1: # APP1 EXIF
                    # Carve previews in EXIF segment
                    app1_slice = raw_data[idx + 4 : idx + 2 + length]
                    previews = carve_jpegs_from_slice(app1_slice, parent_offset=idx + 4)
                    embedded_previews.extend(previews)
                elif marker_val == 0xFFDA: # Start of Scan
                    has_sos = True
                    sos_offset = idx + 2 + length
                    sos_length = length
                    # Rest of file after SOS is entropy scan data up to EOI
                    break

                idx += 2 + length
            else:
                issues.append(DiagnosticIssue(
                    "ERR_PREMATURE_MARKER_TRUNCATION",
                    f"Marker 0x{marker_val:04X} at offset {idx} was truncated before its payload could be read.",
                    Severity.CRITICAL,
                    idx,
                    file_size - idx,
                    "Reconstruct segment or terminate stream."
                ))
                break
        else:
            idx += 1

    # 3. Analyze Scan Data (Entropy payload after SOS)
    byte_stuffing_issues = 0
    if has_sos and sos_offset != -1:
        # Search scan data for rogue 0xFF bytes
        scan_end = file_size
        eoi_search = raw_data.rfind(b"\xff\xd9")
        if eoi_search != -1 and eoi_search > sos_offset:
            has_eoi = True
            scan_end = eoi_search
            segments.append(MarkerSegment(eoi_search, 2, "0xFFD9", "EOI (End of Image)", "Found at end of stream", True, "FF D9"))

        # Scan for unescaped 0xFF inside entropy data
        scan_bytes = raw_data[sos_offset:scan_end]
        s_idx = 0
        while s_idx < len(scan_bytes) - 1:
            if scan_bytes[s_idx] == 0xFF:
                next_b = scan_bytes[s_idx + 1]
                # Valid in entropy scan: 0x00 (stuffed 0xFF) or 0xD0-0xD7 (RST)
                if next_b != 0x00 and not (0xD0 <= next_b <= 0xD7):
                    byte_stuffing_issues += 1
                    if byte_stuffing_issues <= 3:
                        issues.append(DiagnosticIssue(
                            "WARN_ROGUE_FF_BYTE",
                            f"Unescaped 0xFF {next_b:02X} byte in entropy scan at relative offset +{s_idx}. May crash or abort baseline decoder.",
                            Severity.WARNING,
                            sos_offset + s_idx,
                            2,
                            "Escape rogue 0xFF to 0xFF 0x00."
                        ))
                s_idx += 2
            else:
                s_idx += 1

        if byte_stuffing_issues > 0:
            available_repairs.append("repair_byte_stuffing")

    # 4. Check for Missing EOI
    if not has_eoi:
        if raw_data[-2:] == b"\xff\xd9":
            has_eoi = True
        else:
            issues.append(DiagnosticIssue(
                "ERR_MISSING_EOI",
                "File is missing the 0xFFD9 EOI termination marker. It was cut off or aborted during saving.",
                Severity.CRITICAL,
                file_size,
                0,
                "Append missing EOI marker and reconstruct partial scanlines."
            ))
            available_repairs.append("fix_eoi_and_salvage")

    # 5. Check Header Essentials
    if not has_dqt:
        issues.append(DiagnosticIssue(
            "ERR_MISSING_DQT",
            "Missing DQT (Define Quantization Table). Decoder cannot dequantize DCT coefficients.",
            Severity.CRITICAL,
            None,
            None,
            "Inject standard baseline Annex K quantization tables."
        ))
        available_repairs.append("graft_baseline_header")

    if not has_dht:
        issues.append(DiagnosticIssue(
            "ERR_MISSING_DHT",
            "Missing DHT (Define Huffman Table). Decoder cannot parse entropy bitstream.",
            Severity.CRITICAL,
            None,
            None,
            "Inject standard baseline Huffman tables."
        ))
        available_repairs.append("graft_baseline_header")

    if not has_sof:
        issues.append(DiagnosticIssue(
            "ERR_MISSING_SOF",
            "Missing SOF (Start of Frame). Image dimensions, color components, and DCT mode are undefined.",
            Severity.CRITICAL,
            None,
            None,
            "Synthesize SOF0 frame header."
        ))

    # Also perform raw deep scan for any other embedded JPEGs
    if not embedded_previews:
        embedded_previews = carve_all_jpegs_in_bytes(raw_data)
        if len(embedded_previews) > 1:
            embedded_previews = embedded_previews[1:] # First is outer image
        elif len(embedded_previews) == 1 and not has_soi:
            # The carved JPEG is valid even though outer container was damaged!
            pass
        else:
            embedded_previews = []

    if embedded_previews:
        available_repairs.append("carve_embedded_previews")

    # 6. Test Decode
    decode_success = False
    decode_partial = False
    decoded_width = 0
    decoded_height = 0
    decode_error = None

    try:
        with Image.open(io.BytesIO(raw_data)) as test_img:
            decoded_width, decoded_height = test_img.size
            test_img.load()
            decode_success = True
    except Exception as e:
        decode_error = str(e)
        if decoded_width > 0 and decoded_height > 0:
            decode_partial = True
            available_repairs.append("render_partial_scanlines")
        else:
            available_repairs.append("donor_header_recovery")

    # 7. Integrity Score (0 - 100)
    score = 100
    for iss in issues:
        if iss.severity == Severity.CRITICAL:
            score -= 30
        elif iss.severity == Severity.WARNING:
            score -= 10
        elif iss.severity == Severity.INFO:
            score -= 3

    if not decode_success:
        if decode_partial:
            score = max(25, min(score, 65))
        else:
            score = max(5, min(score, 35))

    integrity_score = max(0, min(score, 100))
    is_corrupted = integrity_score < 95 or len(issues) > 0

    return ImageAnalysisResult(
        filepath=filepath,
        filename=p.name,
        file_size=file_size,
        image_format="JPEG",
        is_corrupt=is_corrupted,
        integrity_score=integrity_score,
        issues=issues,
        segments=segments,
        embedded_previews=embedded_previews,
        decode_success=decode_success,
        decode_partial=decode_partial,
        decoded_width=decoded_width,
        decoded_height=decoded_height,
        decode_error=decode_error,
        recoverable=(len(embedded_previews) > 0 or not has_eoi or decode_partial or len(available_repairs) > 0),
        available_repairs=list(set(available_repairs))
    )

def carve_jpegs_from_slice(data: bytes, parent_offset: int = 0) -> List[EmbeddedPreview]:
    results = []
    start_pos = 0
    while True:
        soi = data.find(b"\xff\xd8", start_pos)
        if soi == -1:
            break
        eoi = data.find(b"\xff\xd9", soi + 2)
        if eoi != -1 and (eoi + 2 - soi) > 512:
            chunk = data[soi : eoi + 2]
            try:
                with Image.open(io.BytesIO(chunk)) as img:
                    w, h = img.size
                    results.append(EmbeddedPreview(
                        offset=parent_offset + soi,
                        size=len(chunk),
                        width=w,
                        height=h,
                        format=img.format or "JPEG",
                        preview_base64=f"data:image/jpeg;base64,{base64.b64encode(chunk).decode('ascii')}"
                    ))
            except Exception:
                pass
            start_pos = eoi + 2
        else:
            start_pos = soi + 2
    return results

def carve_all_jpegs_in_bytes(data: bytes) -> List[EmbeddedPreview]:
    return carve_jpegs_from_slice(data, parent_offset=0)

def remove_thumbnail_borders(thumb: Image.Image) -> Image.Image:
    """
    Detects and crops away solid black or uniform letterbox/pillarbox borders
    commonly added to camera EXIF thumbnails.
    """
    try:
        import numpy as np
        arr = np.array(thumb.convert("RGB"))
        h, w, _ = arr.shape
        top = 0
        while top < h // 4 and np.mean(arr[top, :, :]) < 18 and np.std(arr[top, :, :]) < 6:
            top += 1
        bottom = h
        while bottom > h * 3 // 4 and np.mean(arr[bottom - 1, :, :]) < 18 and np.std(arr[bottom - 1, :, :]) < 6:
            bottom -= 1
        left = 0
        while left < w // 4 and np.mean(arr[:, left, :]) < 18 and np.std(arr[:, left, :]) < 6:
            left += 1
        right = w
        while right > w * 3 // 4 and np.mean(arr[:, right - 1, :]) < 18 and np.std(arr[:, right - 1, :]) < 6:
            right -= 1

        if top < bottom and left < right and (top > 0 or bottom < h or left > 0 or right < w):
            return thumb.crop((left, top, right, bottom))
    except Exception:
        pass
    return thumb

def extract_outer_jpeg_structure(raw_data: bytes) -> Dict[str, Any]:
    """
    Robust top-level marker parser that correctly skips nested APP1 EXIF thumbnails,
    returning true outer SOF, SOS, DQTs, and DHTs of the main photo.
    """
    idx = 2 if raw_data.startswith(b"\xff\xd8") else (raw_data.find(b"\xff\xd8") + 2 if raw_data.find(b"\xff\xd8") != -1 else 0)
    file_size = len(raw_data)
    
    sof_info = None
    sos_offset = -1
    dqt_list = []
    dht_list = []
    
    while idx < file_size - 1:
        if raw_data[idx] == 0xFF:
            marker = raw_data[idx + 1]
            if marker in (0xFF, 0x00):
                idx += 1
                continue
            if marker == 0xDA: # Top-level SOS
                sos_offset = idx
                break
            if idx + 4 <= file_size:
                length = struct.unpack(">H", raw_data[idx + 2 : idx + 4])[0]
                chunk = raw_data[idx : idx + 2 + length]
                if marker in (0xC0, 0xC1, 0xC2):
                    sof_info = (idx, chunk)
                elif marker == 0xDB:
                    dqt_list.append(chunk)
                elif marker == 0xC4:
                    dht_list.append(chunk)
                idx += 2 + length
            else:
                break
        else:
            idx += 1
            
    if sos_offset == -1:
        sos_offset = raw_data.rfind(b"\xff\xda")

    return {
        "sof": sof_info,
        "sos": sos_offset,
        "dqts": dqt_list,
        "dhts": dht_list
    }

def detect_scanline_corruption(img: Image.Image) -> Tuple[bool, Optional[int], float]:
    """
    Detects if an image contains solid grey, black, or flat zero-variance corrupt scanlines
    resulting from mid-stream bitstream loss, zero-block stuffing, or decoder termination.
    Returns: (is_corrupted, first_bad_row, corruption_ratio)
    """
    try:
        import numpy as np
        rgb = img.convert("RGB")
        w, h = rgb.size
        step = max(1, h // 600)
        arr = np.array(rgb)[::step, :, :].astype(np.float32)
        
        # 1. Grey corruption (RGB near 128)
        diff_128 = np.abs(arr - 128.0)
        std_rgb = np.std(arr, axis=2)
        is_grey = (std_rgb < 4.0) & (diff_128.mean(axis=2) < 6.0)
        
        # 2. Solid black corruption (RGB near 0)
        is_black = (std_rgb < 2.0) & (arr.mean(axis=2) < 4.0)
        
        # Combined dead pixels
        is_dead = is_grey | is_black
        row_ratio = is_dead.mean(axis=1)

        total_corrupt = float(is_dead.mean())
        if total_corrupt < 0.02:
            return False, None, 0.0

        first_bad_row_sampled = None
        for r_idx, ratio in enumerate(row_ratio):
            if ratio > 0.65:
                first_bad_row_sampled = r_idx
                break

        if first_bad_row_sampled is not None:
            actual_row = min(h - 1, first_bad_row_sampled * step)
            return True, actual_row, total_corrupt
        return total_corrupt > 0.15, int(h * (1.0 - total_corrupt)), total_corrupt
    except Exception:
        return False, None, 0.0

# Backwards compatibility alias
detect_grey_corruption = detect_scanline_corruption

def enhance_thumbnail_super_res(
    thumb_bytes: bytes,
    target_w: Optional[int] = None,
    target_h: Optional[int] = None
) -> Tuple[Image.Image, bytes]:
    """
    High-definition upscaling & detail enhancement of intact EXIF thumbnails.
    Preserves exact natural aspect ratio without squashing or stretching.
    """
    from PIL import ImageFilter, ImageEnhance
    with Image.open(io.BytesIO(thumb_bytes)) as thumb:
        thumb_rgb = remove_thumbnail_borders(thumb.convert("RGB"))
        w_orig, h_orig = thumb_rgb.size
        aspect = w_orig / float(max(1, h_orig))

        if target_w and target_h and target_w > 100 and target_h > 100:
            final_w = target_w
            final_h = target_h
        elif aspect >= 1.0: # Landscape
            final_w = max(2560, w_orig * 8)
            final_h = int(round(final_w / aspect))
        else: # Portrait
            final_h = max(2560, h_orig * 8)
            final_w = int(round(final_h * aspect))

        # 2-stage upscale for smooth edge interpolation
        mid_w = (w_orig + final_w) // 2
        mid_h = (h_orig + final_h) // 2
        mid = thumb_rgb.resize((mid_w, mid_h), Image.Resampling.LANCZOS)
        up = mid.resize((final_w, final_h), Image.Resampling.LANCZOS)

        sharpened = up.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
        enhanced = ImageEnhance.Sharpness(sharpened).enhance(1.35)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.05)

        buf = io.BytesIO()
        enhanced.save(buf, "JPEG", quality=98, subsampling=0, optimize=True)
        return enhanced, buf.getvalue()

def thumbnail_guided_fusion(main_img: Image.Image, thumb_bytes: bytes, bad_row: int) -> Image.Image:
    """
    Blends the high-resolution uncorrupted top scanlines of the main photo with the
    upscaled intact thumbnail bottom scanlines, completely eliminating grey/black boxes.
    Precisely aligns aspect ratio and removes thumbnail letterboxing.
    """
    import numpy as np
    from PIL import ImageFilter
    main_rgb = main_img.convert("RGB")
    w, h = main_rgb.size

    with Image.open(io.BytesIO(thumb_bytes)) as t:
        t_clean = remove_thumbnail_borders(t.convert("RGB"))
        tw, th = t_clean.size

        # Fit thumbnail aspect ratio precisely to match main image without stretching
        target_aspect = w / float(h)
        thumb_aspect = tw / float(th)

        if abs(target_aspect - thumb_aspect) > 0.02:
            if thumb_aspect > target_aspect:
                new_w = int(th * target_aspect)
                x_offset = max(0, (tw - new_w) // 2)
                t_clean = t_clean.crop((x_offset, 0, x_offset + new_w, th))
            else:
                new_h = int(tw / target_aspect)
                y_offset = max(0, (th - new_h) // 2)
                t_clean = t_clean.crop((0, y_offset, tw, y_offset + new_h))

        up = t_clean.resize((w, h), Image.Resampling.LANCZOS)
        up = up.filter(ImageFilter.UnsharpMask(radius=2, percent=130, threshold=2))

    arr_main = np.array(main_rgb)
    arr_thumb = np.array(up)
    blended = arr_main.copy()

    feather = min(48, max(16, bad_row // 20))
    start_y = max(0, bad_row - feather)

    for y in range(start_y, h):
        if y < bad_row:
            alpha = (y - start_y) / float(feather)
        else:
            alpha = 1.0
        blended[y] = ((1.0 - alpha) * arr_main[y].astype(np.float32) + alpha * arr_thumb[y].astype(np.float32)).astype(np.uint8)

    return Image.fromarray(blended)

def generate_uncorrupted_crop_artifact(
    img: Image.Image,
    bad_row: int,
    stem: str,
    output_dir: Path
) -> Optional[RecoveryArtifact]:
    """
    Crops the valid, uncorrupted top scanlines up to the point of corruption,
    delivering a 100% clean photo with zero grey pixels and genuine sensor resolution.
    """
    try:
        w, h = img.size
        crop_h = max(64, bad_row - 4)
        if crop_h < h * 0.2:
            return None

        cropped = img.crop((0, 0, w, crop_h))
        out_name = f"{stem}_pristine_uncorrupted_crop.jpg"
        out_file = output_dir / out_name
        cropped.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True, keep_rgb=True)

        buf = io.BytesIO()
        cropped.save(buf, "JPEG", quality=95)
        b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

        return RecoveryArtifact(
            method="Pristine Native Crop (0% Grey Blocks)",
            filename=out_name,
            filepath=str(out_file.resolve()),
            width=w,
            height=crop_h,
            size=out_file.stat().st_size,
            preview_base64=b64,
            description=f"Auto-cropped valid sensor scanlines (rows 0 to {crop_h}). 100% genuine sensor pixels with zero grey corruption."
        )
    except Exception:
        return None

def generate_inpainted_artifact(
    img: Image.Image,
    bad_row: int,
    stem: str,
    output_dir: Path
) -> Optional[RecoveryArtifact]:
    """
    Fills the damaged/grey scanlines using edge-preserving color and gradient continuation,
    eliminating the harsh flat grey slab while preserving the original canvas dimensions.
    """
    try:
        import numpy as np
        rgb = img.convert("RGB")
        w, h = rgb.size
        arr = np.array(rgb)

        sample_h = min(16, bad_row)
        if sample_h <= 0:
            return None
        sample_rows = arr[bad_row - sample_h : bad_row, :, :].astype(np.float32)
        mean_profile = np.mean(sample_rows, axis=0)

        for y in range(bad_row, h):
            dist = (y - bad_row) / max(1, h - bad_row)
            fade = np.clip(1.0 - dist * 0.35, 0.65, 1.0)
            arr[y] = np.clip(mean_profile * fade, 0, 255).astype(np.uint8)

        inpainted = Image.fromarray(arr)
        out_name = f"{stem}_inpainted_scene_fill.jpg"
        out_file = output_dir / out_name
        inpainted.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True)

        buf = io.BytesIO()
        inpainted.save(buf, "JPEG", quality=95)
        b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

        return RecoveryArtifact(
            method="Context-Aware Inpainted Fill (Smooth Continuation)",
            filename=out_name,
            filepath=str(out_file.resolve()),
            width=w,
            height=h,
            size=out_file.stat().st_size,
            preview_base64=b64,
            description=f"Replaced harsh solid grey blocks with gradient-matched scene continuation at row {bad_row}."
        )
    except Exception:
        return None

def find_reference_donor_in_folder(target_filepath: str) -> Optional[str]:
    """
    Auto-detects an intact, uncorrupted reference photo in the same directory
    taken by the same camera (matching prefix/pattern like IMG2016*).
    """
    p = Path(target_filepath)
    parent = p.parent
    if not parent.is_dir():
        return None

    candidates = []
    prefix = p.stem[:11] if len(p.stem) >= 11 else p.stem[:7]
    for candidate in parent.glob("*.jpg"):
        if candidate.resolve() == p.resolve():
            continue
        if candidate.stem.startswith(prefix):
            candidates.append(candidate)

    if not candidates:
        for candidate in parent.glob("*.jpg"):
            if candidate.resolve() != p.resolve():
                candidates.append(candidate)

    for cand in candidates:
        try:
            with Image.open(cand) as test_img:
                test_img.load()
                has_corrupt, _, _ = detect_scanline_corruption(test_img)
                if not has_corrupt and test_img.width >= 600:
                    return str(cand.resolve())
        except Exception:
            continue
    return None

def repair_with_donor_reference(target_filepath: str, donor_filepath: str, output_dir: Path) -> List[RecoveryArtifact]:
    """
    Grafts authentic camera Quantization and Huffman tables from an intact reference/donor image
    onto the damaged photo, preserving target dimensions and preventing diagonal shearing.
    """
    artifacts = []
    try:
        p_target = Path(target_filepath)
        p_donor = Path(donor_filepath)
        donor_bytes = p_donor.read_bytes()
        target_bytes = p_target.read_bytes()

        donor_struct = extract_outer_jpeg_structure(donor_bytes)
        target_struct = extract_outer_jpeg_structure(target_bytes)

        if not donor_struct["dqts"] or donor_struct["sos"] == -1 or target_struct["sos"] == -1:
            return artifacts

        # Build clean outer header from donor's tables
        header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        for dqt in donor_struct["dqts"]:
            header += dqt
        for dht in donor_struct["dhts"]:
            header += dht

        # Preserve target's authentic SOF dimensions and sampling factors
        if target_struct["sof"]:
            header += target_struct["sof"][1]
        elif donor_struct["sof"]:
            header += donor_struct["sof"][1]
        else:
            header += build_standard_sof0_marker(1200, 800)

        target_scan = target_bytes[target_struct["sos"]:]
        if not target_scan.endswith(b"\xff\xd9"):
            target_scan += b"\xff\xd9"

        grafted_stream = header + target_scan

        with Image.open(io.BytesIO(grafted_stream)) as img:
            w, h = img.size
            img.load()

            has_corrupt, bad_row, corrupt_ratio = detect_scanline_corruption(img)

            out_name = f"{p_target.stem}_donor_grafted_{p_donor.stem}.jpg"
            out_file = output_dir / out_name
            img.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True, keep_rgb=True)

            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=95)
            b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

            desc = f"Grafted authentic camera Quantization & Huffman tables from {p_donor.name} onto target scanlines."
            if has_corrupt:
                desc += f" (Contains {corrupt_ratio*100:.1f}% grey scanlines from cut-off sensor stream)."

            artifacts.append(RecoveryArtifact(
                method=f"Donor Reference Header Grafting ({p_donor.name})",
                filename=out_name,
                filepath=str(out_file.resolve()),
                width=w,
                height=h,
                size=out_file.stat().st_size,
                preview_base64=b64,
                description=desc
            ))
    except Exception:
        pass
    return artifacts

def repair_jpeg_advanced(filepath: str, action: str, output_dir: Path, donor_filepath: Optional[str] = None) -> List[RecoveryArtifact]:
    """
    Advanced JPEG Repair Engine executing precision multi-stage repairs:
    - 'smart_auto': multi-pass recovery (junk stripping, thumbnail fusion, donor grafting, baseline Annex K, pristine crop, inpainting)
    - 'thumbnail_fusion': reconstruct complete image by blending native scanlines with upscaled intact thumbnail (0% grey)
    - 'thumbnail_hd': upscale and enhance intact embedded thumbnail to high definition (complete scene)
    - 'donor_reference': graft authentic camera tables from intact reference photo
    - 'pristine_crop': auto-crop valid uncorrupted scanlines (0% grey)
    - 'inpainted_fill': gradient-matched inpainting across damaged rows
    - 'graft_baseline_header': inject standard Annex K baseline DQT/DHT/JFIF headers
    - 'repair_byte_stuffing': sanitize rogue 0xFF bytes in entropy scan
    - 'fix_eoi_and_salvage': append missing EOI and reconstruct scanlines
    - 'carve_embedded_previews': extract raw embedded EXIF previews
    """
    p = Path(filepath)
    raw_data = p.read_bytes()
    artifacts: List[RecoveryArtifact] = []

    # 1. Check for leading junk / byte shift
    found_soi = raw_data.find(b"\xff\xd8")
    if found_soi > 0:
        stripped_bytes = raw_data[found_soi:]
        try:
            with Image.open(io.BytesIO(stripped_bytes)) as s_img:
                w, h = s_img.size
                s_img.load()
                out_name = f"{p.stem}_header_realigned.jpg"
                out_file = output_dir / out_name
                s_img.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True)

                buf = io.BytesIO()
                s_img.save(buf, "JPEG", quality=95)
                b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                artifacts.append(RecoveryArtifact(
                    method="Header Alignment (Stripped Leading Junk)",
                    filename=out_name,
                    filepath=str(out_file.resolve()),
                    width=w,
                    height=h,
                    size=out_file.stat().st_size,
                    preview_base64=b64,
                    description=f"Stripped {found_soi} bytes of invalid prepended junk and aligned SOI header."
                ))
                raw_data = stripped_bytes
        except Exception:
            raw_data = stripped_bytes

    analysis = analyze_jpeg_deep(filepath)

    # Extract raw intact thumbnail bytes if present
    raw_thumb_bytes = None
    if analysis.embedded_previews:
        first_prev = analysis.embedded_previews[0]
        raw_thumb_bytes = raw_data[first_prev.offset : first_prev.offset + first_prev.size]

    # Check for scanline corruption in primary decode
    main_has_corruption = False
    main_bad_row = None
    main_corrupt_ratio = 0.0
    main_img_clean = None

    try:
        with Image.open(io.BytesIO(raw_data)) as test_img:
            test_img.load()
            main_has_corruption, main_bad_row, main_corrupt_ratio = detect_scanline_corruption(test_img)
            main_img_clean = test_img.copy()
    except Exception:
        main_has_corruption = True

    # ACTION: THUMBNAIL-GUIDED SEAMLESS FUSION (0% Grey Blocks)
    if action in ("smart_auto", "auto", "thumbnail_fusion") and raw_thumb_bytes and main_img_clean:
        if main_has_corruption or action == "thumbnail_fusion":
            try:
                bad_row = main_bad_row if (main_bad_row is not None) else int(main_img_clean.height * 0.5)
                fused_img = thumbnail_guided_fusion(main_img_clean, raw_thumb_bytes, bad_row)
                w, h = fused_img.size
                out_name = f"{p.stem}_thumbnail_guided_restoration.jpg"
                out_file = output_dir / out_name
                fused_img.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True, keep_rgb=True)

                png_name = f"{p.stem}_thumbnail_guided_master.png"
                png_file = output_dir / png_name
                fused_img.save(str(png_file), "PNG", optimize=True)

                buf = io.BytesIO()
                fused_img.save(buf, "JPEG", quality=95)
                b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                artifacts.append(RecoveryArtifact(
                    method="Thumbnail-Guided Seamless Fusion (0% Grey Blocks)",
                    filename=out_name,
                    filepath=str(out_file.resolve()),
                    width=w,
                    height=h,
                    size=out_file.stat().st_size,
                    preview_base64=b64,
                    description=f"Reconstructed photo by blending high-res native scanlines with enhanced intact camera thumbnail at row {bad_row}. 0% grey boxes remaining."
                ))

                artifacts.append(RecoveryArtifact(
                    method="Lossless Master Export (PNG)",
                    filename=png_name,
                    filepath=str(png_file.resolve()),
                    width=w,
                    height=h,
                    size=png_file.stat().st_size,
                    preview_base64=b64,
                    description=f"Lossless PNG master of seamless thumbnail-guided restoration at {w}x{h} resolution."
                ))
            except Exception:
                pass

    # ACTION: PRISTINE NATIVE CROP (0% Grey Blocks, 100% Genuine Sensor Pixels)
    if action in ("smart_auto", "auto", "pristine_crop") and main_img_clean and main_has_corruption and main_bad_row:
        crop_art = generate_uncorrupted_crop_artifact(main_img_clean, main_bad_row, p.stem, output_dir)
        if crop_art:
            artifacts.append(crop_art)

    # ACTION: CONTEXT-AWARE INPAINTED FILL
    if action in ("smart_auto", "auto", "inpainted_fill") and main_img_clean and main_has_corruption and main_bad_row:
        inpaint_art = generate_inpainted_artifact(main_img_clean, main_bad_row, p.stem, output_dir)
        if inpaint_art:
            artifacts.append(inpaint_art)

    # ACTION: ENHANCED HIGH-DEFINITION THUMBNAIL RESTORATION (Complete Scene)
    if (action in ("smart_auto", "auto", "thumbnail_hd") or not main_img_clean) and raw_thumb_bytes:
        try:
            target_w = analysis.decoded_width
            target_h = analysis.decoded_height
            hd_img, hd_bytes = enhance_thumbnail_super_res(raw_thumb_bytes, target_w, target_h)
            w, h = hd_img.size

            out_name = f"{p.stem}_enhanced_thumbnail_hd.jpg"
            out_file = output_dir / out_name
            out_file.write_bytes(hd_bytes)

            buf = io.BytesIO()
            hd_img.save(buf, "JPEG", quality=95)
            b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

            artifacts.append(RecoveryArtifact(
                method="Enhanced High-Definition Thumbnail (Complete Scene)",
                filename=out_name,
                filepath=str(out_file.resolve()),
                width=w,
                height=h,
                size=len(hd_bytes),
                preview_base64=b64,
                description=f"Restored 100% complete scene from uncorrupted embedded EXIF thumbnail, upscaled & enhanced to {w}x{h} HD with Lanczos & Unsharp Masking."
            ))
        except Exception:
            pass

    # ACTION: DONOR REFERENCE IMAGE RECOVERY
    active_donor = donor_filepath
    if not active_donor and action in ("smart_auto", "auto", "donor_reference"):
        active_donor = find_reference_donor_in_folder(filepath)

    if active_donor and Path(active_donor).is_file():
        donor_arts = repair_with_donor_reference(filepath, active_donor, output_dir)
        if donor_arts:
            artifacts.extend(donor_arts)

    # ACTION: Full-Resolution Scanline Salvage & Lossless Stream Repair
    if action in ("smart_auto", "fix_eoi_and_salvage", "render_partial_scanlines"):
        # Direct Lossless Bitstream Repair
        if not raw_data.endswith(b"\xff\xd9"):
            try:
                lossless_bytes = raw_data + b"\xff\xd9"
                with Image.open(io.BytesIO(lossless_bytes)) as test_l:
                    w, h = test_l.size
                    test_l.load()
                    out_name = f"{p.stem}_lossless_stream_repaired.jpg"
                    out_file = output_dir / out_name
                    out_file.write_bytes(lossless_bytes)

                    buf = io.BytesIO()
                    test_l.save(buf, "JPEG", quality=95)
                    b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                    desc = "Repaired JPEG stream without re-compression."
                    if main_has_corruption:
                        desc += f" (Contains {main_corrupt_ratio*100:.1f}% grey scanlines from sensor cut-off)."

                    artifacts.append(RecoveryArtifact(
                        method="Lossless Bitstream Repair (0% Quality Loss)",
                        filename=out_name,
                        filepath=str(out_file.resolve()),
                        width=w,
                        height=h,
                        size=len(lossless_bytes),
                        preview_base64=b64,
                        description=desc
                    ))
            except Exception:
                pass

        # High-Resolution Scanline Reconstruction (4:4:4 Chroma Subsampling)
        try:
            with Image.open(io.BytesIO(raw_data)) as img:
                w, h = img.size
                out_name = f"{p.stem}_high_quality_full_res.jpg"
                out_file = output_dir / out_name
                clean = img.convert("RGB")

                clean.save(
                    str(out_file),
                    "JPEG",
                    quality=100,
                    subsampling=0,
                    optimize=True,
                    keep_rgb=True
                )

                png_name = f"{p.stem}_lossless_master.png"
                png_file = output_dir / png_name
                clean.save(str(png_file), "PNG", optimize=True)

                buf = io.BytesIO()
                clean.save(buf, "JPEG", quality=95)
                b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                desc = "Decoded all scanlines with 4:4:4 chroma (subsampling=0) and quality=100."
                if main_has_corruption:
                    desc += f" (Warning: scanlines contain {main_corrupt_ratio*100:.1f}% grey)."

                artifacts.append(RecoveryArtifact(
                    method="Full-Resolution Reconstruction (Max 100% Quality)",
                    filename=out_name,
                    filepath=str(out_file.resolve()),
                    width=w,
                    height=h,
                    size=out_file.stat().st_size,
                    preview_base64=b64,
                    description=desc
                ))

                artifacts.append(RecoveryArtifact(
                    method="Lossless Master Export (PNG)",
                    filename=png_name,
                    filepath=str(png_file.resolve()),
                    width=w,
                    height=h,
                    size=png_file.stat().st_size,
                    preview_base64=b64,
                    description=f"Lossless PNG export at {w}x{h} native resolution."
                ))
        except Exception:
            if not raw_data.endswith(b"\xff\xd9"):
                repaired = raw_data + b"\xff\xd9"
                out_name = f"{p.stem}_eoi_fixed.jpg"
                out_file = output_dir / out_name
                out_file.write_bytes(repaired)
                artifacts.append(RecoveryArtifact(
                    method="EOI Terminator Appended",
                    filename=out_name,
                    filepath=str(out_file.resolve()),
                    width=analysis.decoded_width or 0,
                    height=analysis.decoded_height or 0,
                    size=len(repaired),
                    preview_base64=None,
                    description="Appended missing 0xFFD9 EOI marker to raw bitstream."
                ))

    # ACTION: Baseline Header Grafting (Annex K tables, testing 4:2:0, 4:2:2, 4:4:4)
    should_graft_baseline = (
        action in ("smart_auto", "graft_baseline_header") and
        (not analysis.to_dict()["has_dqt"] or not analysis.to_dict()["has_dht"] or not analysis.to_dict()["has_soi"] or not main_img_clean)
    )

    if should_graft_baseline:
        structure = extract_outer_jpeg_structure(raw_data)
        outer_sos = structure["sos"]

        donor_tables = b"\xff\xd8" + build_standard_jfif_marker() + build_standard_dqt_marker() + build_standard_dht_marker()

        target_w = analysis.decoded_width or 1200
        target_h = analysis.decoded_height or 800

        # Try multiple chroma subsampling schemes: 4:2:0, 4:2:2, 4:4:4
        subsampling_candidates = ["4:2:0", "4:2:2", "4:4:4"]
        for sub_scheme in subsampling_candidates:
            try:
                if structure["sof"]:
                    sof_block = structure["sof"][1]
                else:
                    sof_block = build_standard_sof0_marker(target_w, target_h, subsampling=sub_scheme)

                if outer_sos != -1:
                    repaired_data = donor_tables + sof_block + raw_data[outer_sos:]
                else:
                    repaired_data = donor_tables + sof_block + raw_data

                if not repaired_data.endswith(b"\xff\xd9"):
                    repaired_data += b"\xff\xd9"

                with Image.open(io.BytesIO(repaired_data)) as r_img:
                    w, h = r_img.size
                    r_img.load()
                    out_name = f"{p.stem}_grafted_header_{sub_scheme.replace(':', '')}.jpg"
                    out_file = output_dir / out_name
                    r_img.save(
                        str(out_file),
                        "JPEG",
                        quality=100,
                        subsampling=0,
                        optimize=True,
                        keep_rgb=True
                    )

                    png_name = f"{p.stem}_grafted_master_{sub_scheme.replace(':', '')}.png"
                    png_file = output_dir / png_name
                    r_img.save(str(png_file), "PNG", optimize=True)

                    buf = io.BytesIO()
                    r_img.save(buf, "JPEG", quality=95)
                    b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                    artifacts.append(RecoveryArtifact(
                        method=f"Baseline Header Grafting ({sub_scheme} Annex K)",
                        filename=out_name,
                        filepath=str(out_file.resolve()),
                        width=w,
                        height=h,
                        size=out_file.stat().st_size,
                        preview_base64=b64,
                        description=f"Grafted standard baseline Quantization and Huffman tables with {sub_scheme} sampling."
                    ))

                    artifacts.append(RecoveryArtifact(
                        method="Lossless Master Export (PNG)",
                        filename=png_name,
                        filepath=str(png_file.resolve()),
                        width=w,
                        height=h,
                        size=png_file.stat().st_size,
                        preview_base64=b64,
                        description=f"Lossless PNG export of grafted photo at {w}x{h} native resolution."
                    ))
                    break # Successfully grafted with valid subsampling!
            except Exception:
                continue

    # ACTION: Rogue 0xFF Byte-Stuffing Repair (using true outer SOS)
    if action in ("smart_auto", "repair_byte_stuffing"):
        try:
            structure = extract_outer_jpeg_structure(raw_data)
            sos_pos = structure["sos"]
            if sos_pos != -1:
                sos_len = struct.unpack(">H", raw_data[sos_pos+2:sos_pos+4])[0]
                scan_start = sos_pos + 2 + sos_len

                header_part = raw_data[:scan_start]
                scan_part = raw_data[scan_start:]

                sanitized_scan = bytearray()
                i = 0
                while i < len(scan_part):
                    b = scan_part[i]
                    sanitized_scan.append(b)
                    if b == 0xFF:
                        if i + 1 < len(scan_part):
                            next_b = scan_part[i+1]
                            if next_b == 0x00 or (0xD0 <= next_b <= 0xD7) or next_b == 0xD9:
                                sanitized_scan.append(next_b)
                                i += 1
                            else:
                                sanitized_scan.append(0x00)
                        else:
                            sanitized_scan.append(0x00)
                    i += 1

                repaired_bytes = header_part + bytes(sanitized_scan)
                if not repaired_bytes.endswith(b"\xff\xd9"):
                    repaired_bytes += b"\xff\xd9"

                with Image.open(io.BytesIO(repaired_bytes)) as b_img:
                    w, h = b_img.size
                    b_img.load()
                    out_name = f"{p.stem}_sanitized_stuffing.jpg"
                    out_file = output_dir / out_name
                    b_img.save(
                        str(out_file),
                        "JPEG",
                        quality=100,
                        subsampling=0,
                        optimize=True,
                        keep_rgb=True
                    )

                    buf = io.BytesIO()
                    b_img.save(buf, "JPEG", quality=95)
                    b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                    artifacts.append(RecoveryArtifact(
                        method="Byte-Stuffing Error Repair (Max Quality)",
                        filename=out_name,
                        filepath=str(out_file.resolve()),
                        width=w,
                        height=h,
                        size=out_file.stat().st_size,
                        preview_base64=b64,
                        description="Escaped rogue 0xFF bytes inside entropy scanlines and saved at 100% quality."
                    ))
        except Exception:
            pass

    # ACTION: Raw Embedded Previews Carving (Auxiliary / Low-Res)
    if action in ("smart_auto", "carve_embedded_previews") and analysis.embedded_previews:
        for i, prev in enumerate(analysis.embedded_previews):
            chunk = raw_data[prev.offset : prev.offset + prev.size]
            out_name = f"{p.stem}_carved_preview_{i+1}.jpg"
            out_file = output_dir / out_name
            out_file.write_bytes(chunk)
            artifacts.append(RecoveryArtifact(
                method="Embedded EXIF Preview (Camera Thumbnail)",
                filename=out_name,
                filepath=str(out_file.resolve()),
                width=prev.width,
                height=prev.height,
                size=len(chunk),
                preview_base64=prev.preview_base64,
                description=f"Carved embedded preview thumbnail ({prev.width}x{prev.height}) from EXIF header."
            ))

    # CRITICAL SORTING:
    # 1. Complete images without grey corruption (Fusion, Pristine Crop, Inpainted, HD Thumbnail) ranked FIRST!
    # 2. Then sorted by resolution (width * height) and file size descending.
    def artifact_rank(art: RecoveryArtifact) -> Tuple[int, int, int]:
        is_grey_warning = "grey" in art.description.lower()
        is_fused = "seamless fusion" in art.method.lower()
        is_crop = "pristine native crop" in art.method.lower()
        is_inpaint = "context-aware inpainted" in art.method.lower()
        is_hd_thumb = "enhanced high-definition" in art.method.lower()
        is_raw_thumb = "embedded exif preview" in art.method.lower()

        if is_fused:
            priority = 100
        elif is_crop:
            priority = 95
        elif is_hd_thumb:
            priority = 90
        elif is_inpaint:
            priority = 85
        elif not is_grey_warning and not is_raw_thumb:
            priority = 80
        elif not is_raw_thumb:
            priority = 50
        else:
            priority = 10

        return (priority, art.width * art.height, art.size)

    artifacts.sort(key=artifact_rank, reverse=True)
    return artifacts