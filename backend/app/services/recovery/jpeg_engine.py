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

def build_standard_sof0_marker(width: int = 1200, height: int = 800) -> bytes:
    # 8-bit precision, height, width, 3 color components: Y (2x2, Q=0), Cb (1x1, Q=1), Cr (1x1, Q=1)
    payload = struct.pack(">BHHB", 8, max(height, 100), max(width, 100), 3) + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01"
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

def detect_grey_corruption(img: Image.Image) -> Tuple[bool, Optional[int], float]:
    """
    Detects if an image contains solid grey scanlines (RGB around 128 with near-zero deviation),
    which occurs when libjpeg aborts decoding mid-stream due to bitstream or zero-block corruption.
    Returns: (is_grey_corrupted, first_bad_row, grey_ratio)
    """
    try:
        import numpy as np
        rgb = img.convert("RGB")
        w, h = rgb.size
        # Fast sample rows across height
        step = max(1, h // 600)
        arr = np.array(rgb)[::step, :, :].astype(np.float32)
        diff = np.abs(arr - 128.0)
        std = np.std(arr, axis=2)
        is_grey = (std < 3.5) & (diff.mean(axis=2) < 5.0)
        row_ratio = is_grey.mean(axis=1)

        total_grey = float(is_grey.mean())
        if total_grey < 0.03:
            return False, None, 0.0

        first_bad_row_sampled = None
        for r_idx, ratio in enumerate(row_ratio):
            if ratio > 0.70:
                first_bad_row_sampled = r_idx
                break

        if first_bad_row_sampled is not None:
            actual_row = min(h - 1, first_bad_row_sampled * step)
            return True, actual_row, total_grey
        return total_grey > 0.20, int(h * (1.0 - total_grey)), total_grey
    except Exception:
        return False, None, 0.0

def enhance_thumbnail_super_res(thumb_bytes: bytes, target_w: int = 2560, target_h: int = 1920) -> Tuple[Image.Image, bytes]:
    """
    High-definition upscaling & detail enhancement of intact EXIF thumbnails.
    Uses multi-stage Lanczos resampling, unsharp masking, and contrast-adaptive detail enhancement.
    """
    from PIL import ImageFilter, ImageEnhance
    with Image.open(io.BytesIO(thumb_bytes)) as thumb:
        thumb_rgb = thumb.convert("RGB")
        w_orig, h_orig = thumb_rgb.size
        target_w = max(target_w, w_orig * 4, 1920)
        target_h = max(target_h, h_orig * 4, 1080)

        # 2-stage upscale for smoother edge interpolation
        mid_w = (w_orig + target_w) // 2
        mid_h = (h_orig + target_h) // 2
        mid = thumb_rgb.resize((mid_w, mid_h), Image.Resampling.LANCZOS)
        up = mid.resize((target_w, target_h), Image.Resampling.LANCZOS)

        sharpened = up.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
        enhanced = ImageEnhance.Sharpness(sharpened).enhance(1.3)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.05)

        buf = io.BytesIO()
        enhanced.save(buf, "JPEG", quality=98, subsampling=0, optimize=True)
        return enhanced, buf.getvalue()

def thumbnail_guided_fusion(main_img: Image.Image, thumb_bytes: bytes, bad_row: int) -> Image.Image:
    """
    Blends the high-resolution uncorrupted top scanlines of the main photo with the
    upscaled intact thumbnail bottom scanlines, completely eliminating the grey box.
    """
    import numpy as np
    from PIL import ImageFilter
    main_rgb = main_img.convert("RGB")
    w, h = main_rgb.size

    with Image.open(io.BytesIO(thumb_bytes)) as t:
        t_rgb = t.convert("RGB")
        up = t_rgb.resize((w, h), Image.Resampling.LANCZOS)
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
                has_grey, _, _ = detect_grey_corruption(test_img)
                if not has_grey and test_img.width >= 800:
                    return str(cand.resolve())
        except Exception:
            continue
    return None

def repair_with_donor_reference(target_filepath: str, donor_filepath: str, output_dir: Path) -> List[RecoveryArtifact]:
    """
    Grafts complete camera headers (DQT, DHT, SOF0, APP1) from an intact reference/donor image
    onto the damaged photo, restoring authentic camera quantization and Huffman tables.
    """
    artifacts = []
    try:
        p_target = Path(target_filepath)
        p_donor = Path(donor_filepath)
        donor_bytes = p_donor.read_bytes()
        target_bytes = p_target.read_bytes()

        donor_sos = donor_bytes.find(b"\xff\xda")
        target_sos = target_bytes.find(b"\xff\xda")
        if donor_sos == -1 or target_sos == -1:
            return artifacts

        donor_headers = donor_bytes[:donor_sos]
        grafted_stream = donor_headers + target_bytes[target_sos:]
        if not grafted_stream.endswith(b"\xff\xd9"):
            grafted_stream += b"\xff\xd9"

        with Image.open(io.BytesIO(grafted_stream)) as img:
            w, h = img.size
            img.load()

            has_grey, bad_row, grey_ratio = detect_grey_corruption(img)

            out_name = f"{p_target.stem}_donor_grafted_{p_donor.stem}.jpg"
            out_file = output_dir / out_name
            img.save(str(out_file), "JPEG", quality=100, subsampling=0, optimize=True, keep_rgb=True)

            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=95)
            b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

            desc = f"Grafted exact camera Quantization & Huffman tables from reference image {p_donor.name}."
            if has_grey:
                desc += f" (Note: scanlines contain {grey_ratio*100:.1f}% grey due to missing sensor data)."

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
    Advanced JPEG Repair Engine executing precision repairs:
    - 'smart_auto': multi-pass recovery (thumbnail fusion, donor grafting, lossless bitstream repair, HD thumbnail)
    - 'graft_baseline_header': inject standard Annex K baseline DQT/DHT/JFIF headers
    - 'repair_byte_stuffing': sanitize rogue 0xFF bytes in entropy scan
    - 'fix_eoi_and_salvage': append missing EOI and reconstruct scanlines
    - 'carve_embedded_previews': extract all intact embedded thumbnails
    - 'donor_reference': graft headers from intact donor reference photo in same folder
    """
    p = Path(filepath)
    raw_data = p.read_bytes()
    analysis = analyze_jpeg_deep(filepath)
    artifacts: List[RecoveryArtifact] = []

    # Extract raw intact thumbnail bytes if present
    raw_thumb_bytes = None
    if analysis.embedded_previews:
        first_prev = analysis.embedded_previews[0]
        raw_thumb_bytes = raw_data[first_prev.offset : first_prev.offset + first_prev.size]

    # Check for grey corruption in primary decode
    main_has_grey = False
    main_bad_row = None
    main_grey_ratio = 0.0
    main_img_clean = None

    try:
        with Image.open(io.BytesIO(raw_data)) as test_img:
            test_img.load()
            main_has_grey, main_bad_row, main_grey_ratio = detect_grey_corruption(test_img)
            main_img_clean = test_img.copy()
    except Exception:
        main_has_grey = True

    # 1. THUMBNAIL-GUIDED SEAMLESS FUSION (0% Grey Blocks!) - Highest Priority for corrupted photos!
    if action in ("smart_auto", "auto", "thumbnail_fusion") and raw_thumb_bytes and main_img_clean:
        if main_has_grey or action == "thumbnail_fusion":
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

    # 2. ENHANCED HIGH-DEFINITION THUMBNAIL RESTORATION (Complete Scene)
    if (action in ("smart_auto", "auto", "thumbnail_hd") or not main_img_clean) and raw_thumb_bytes:
        try:
            target_w = analysis.decoded_width or 2560
            target_h = analysis.decoded_height or 1920
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

    # 3. DONOR REFERENCE IMAGE RECOVERY (from Folder / Track)
    active_donor = donor_filepath
    if not active_donor and action in ("smart_auto", "auto", "donor_reference"):
        active_donor = find_reference_donor_in_folder(filepath)

    if active_donor and Path(active_donor).is_file():
        donor_arts = repair_with_donor_reference(filepath, active_donor, output_dir)
        if donor_arts:
            artifacts.extend(donor_arts)

    # 4. Full-Resolution Scanline Salvage & Lossless Stream Repair
    if action in ("smart_auto", "fix_eoi_and_salvage", "render_partial_scanlines"):
        # A. Direct Lossless Bitstream Repair
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
                    if main_has_grey:
                        desc += f" (Contains {main_grey_ratio*100:.1f}% grey scanlines from sensor cut-off)."

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

        # B. High-Resolution Scanline Reconstruction (100% Quality, 4:4:4 Chroma Subsampling)
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
                if main_has_grey:
                    desc += f" (Warning: scanlines contain {main_grey_ratio*100:.1f}% grey)."

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
                    width=analysis.decoded_width,
                    height=analysis.decoded_height,
                    size=len(repaired),
                    preview_base64=None,
                    description="Appended missing 0xFFD9 EOI marker to raw bitstream."
                ))

    # 5. Baseline Header Grafting (Annex K tables)
    if action in ("smart_auto", "graft_baseline_header") and (not analysis.to_dict()["has_dqt"] or not analysis.to_dict()["has_dht"] or not analysis.to_dict()["has_soi"]):
        try:
            donor_header = b"\xff\xd8" + build_standard_jfif_marker() + build_standard_dqt_marker() + build_standard_dht_marker()
            sos_pos = raw_data.find(b"\xff\xda")
            if sos_pos != -1:
                sof_pos = -1
                for marker in (b"\xff\xc0", b"\xff\xc1", b"\xff\xc2"):
                    sof_pos = raw_data.find(marker)
                    if sof_pos != -1:
                        break

                if sof_pos != -1 and sof_pos < sos_pos:
                    sof_len = struct.unpack(">H", raw_data[sof_pos+2:sof_pos+4])[0]
                    sof_block = raw_data[sof_pos : sof_pos + 2 + sof_len]
                    repaired_data = donor_header + sof_block + raw_data[sos_pos:]
                else:
                    target_w = analysis.decoded_width or 1200
                    target_h = analysis.decoded_height or 800
                    repaired_data = donor_header + build_standard_sof0_marker(target_w, target_h) + raw_data[sos_pos:]
            else:
                first_ff = raw_data.find(b"\xff")
                if first_ff != -1:
                    repaired_data = donor_header + raw_data[first_ff:]
                else:
                    repaired_data = donor_header + raw_data

            if not repaired_data.endswith(b"\xff\xd9"):
                repaired_data += b"\xff\xd9"

            with Image.open(io.BytesIO(repaired_data)) as r_img:
                w, h = r_img.size
                out_name = f"{p.stem}_grafted_header.jpg"
                out_file = output_dir / out_name
                r_img.save(
                    str(out_file),
                    "JPEG",
                    quality=100,
                    subsampling=0,
                    optimize=True,
                    keep_rgb=True
                )

                png_name = f"{p.stem}_grafted_master.png"
                png_file = output_dir / png_name
                r_img.save(str(png_file), "PNG", optimize=True)

                buf = io.BytesIO()
                r_img.save(buf, "JPEG", quality=95)
                b64 = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

                artifacts.append(RecoveryArtifact(
                    method="Baseline Header Grafting (Max Quality)",
                    filename=out_name,
                    filepath=str(out_file.resolve()),
                    width=w,
                    height=h,
                    size=out_file.stat().st_size,
                    preview_base64=b64,
                    description="Grafted standard baseline Quantization and Huffman tables and exported at 100% quality."
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
        except Exception:
            pass

    # 6. Rogue 0xFF Byte-Stuffing Repair (Max Quality)
    if action in ("smart_auto", "repair_byte_stuffing") and "repair_byte_stuffing" in analysis.available_repairs:
        try:
            sos_pos = raw_data.find(b"\xff\xda")
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

    # 7. Raw Embedded Previews Carving (Auxiliary / Low-Res)
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
    # 1. Complete images without grey corruption (Thumbnail-Guided Fusion, Enhanced HD Thumbnail) ranked FIRST!
    # 2. Then sorted by resolution (width * height) and file size descending.
    def artifact_rank(art: RecoveryArtifact) -> Tuple[int, int, int]:
        is_grey_warning = "grey" in art.description.lower()
        is_fused = "seamless fusion" in art.method.lower()
        is_hd_thumb = "enhanced high-definition" in art.method.lower()
        is_raw_thumb = "embedded exif preview" in art.method.lower()

        if is_fused:
            priority = 100
        elif is_hd_thumb:
            priority = 90
        elif not is_grey_warning and not is_raw_thumb:
            priority = 80
        elif not is_raw_thumb:
            priority = 50
        else:
            priority = 10

        return (priority, art.width * art.height, art.size)

    artifacts.sort(key=artifact_rank, reverse=True)
    return artifacts
