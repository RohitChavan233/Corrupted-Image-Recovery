import io
import zlib
import struct
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageFile
from .base import Severity, DiagnosticIssue, MarkerSegment, RecoveryArtifact, ImageAnalysisResult

ImageFile.LOAD_TRUNCATED_IMAGES = True

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IEND_CHUNK = b"\x00\x00\x00\x00IEND\xaeB\x60\x82"

KNOWN_PNG_CHUNKS = {
    "IHDR": "Image Header (Dimensions, Bit Depth, Color Type)",
    "PLTE": "Color Palette",
    "IDAT": "Image Data (Deflate Compressed Scanlines)",
    "IEND": "Image End (Stream Terminator)",
    "tRNS": "Transparency Information",
    "cHRM": "Primary Chromaticities",
    "gAMA": "Image Gamma",
    "iCCP": "Embedded ICC Profile",
    "sBIT": "Significant Bits",
    "sRGB": "Standard RGB Color Space",
    "tEXt": "Textual Data (Uncompressed)",
    "zTXt": "Compressed Textual Data",
    "iTXt": "International Textual Data",
    "bKGD": "Background Color",
    "pHYs": "Physical Pixel Dimensions",
    "sPLT": "Suggested Palette",
    "hIST": "Palette Histogram",
    "eXIf": "EXIF Metadata"
}

def analyze_png_deep(filepath: str) -> ImageAnalysisResult:
    p = Path(filepath)
    raw_data = p.read_bytes()
    file_size = len(raw_data)

    issues: List[DiagnosticIssue] = []
    segments: List[MarkerSegment] = []
    available_repairs: List[str] = []

    if file_size < 8:
        return ImageAnalysisResult(
            filepath=filepath,
            filename=p.name,
            file_size=file_size,
            image_format="PNG",
            is_corrupt=True,
            integrity_score=0,
            issues=[DiagnosticIssue("ERR_FILE_TOO_SMALL", "File is smaller than 8 bytes, invalid PNG header.", Severity.CRITICAL, 0, file_size)],
            decode_error="File is too small"
        )

    # 1. Check Signature
    has_valid_sig = raw_data.startswith(PNG_SIGNATURE)
    if has_valid_sig:
        segments.append(MarkerSegment(0, 8, "SIG_PNG", "PNG Signature", "Valid 8-byte PNG file signature", True, "89 50 4E 47 0D 0A 1A 0A"))
        offset = 8
    else:
        # Check if signature is corrupted or shifted
        sig_search = raw_data.find(b"PNG\r\n\x1a\n")
        if sig_search != -1:
            issues.append(DiagnosticIssue(
                "WARN_PNG_SIG_CORRUPTED",
                f"PNG signature has corrupted first byte(s) or is shifted at offset {sig_search}.",
                Severity.CRITICAL,
                0,
                sig_search + 7,
                "Restore standard 8-byte PNG signature."
            ))
            available_repairs.append("repair_png_signature")
            offset = sig_search + 7
        else:
            issues.append(DiagnosticIssue(
                "ERR_INVALID_PNG_SIG",
                "Missing standard 8-byte PNG signature (89 50 4E 47 0D 0A 1A 0A).",
                Severity.CRITICAL,
                0,
                8,
                "Prepend standard PNG signature."
            ))
            available_repairs.append("repair_png_signature")
            offset = 0

    has_ihdr = False
    has_idat = False
    has_iend = False
    crc_errors = 0
    idat_bytes_total = 0

    # 2. Parse Chunks
    while offset + 8 <= file_size:
        try:
            length = struct.unpack(">I", raw_data[offset : offset + 4])[0]
            chunk_type_raw = raw_data[offset + 4 : offset + 8]
            chunk_type = chunk_type_raw.decode("ascii", errors="replace")
        except Exception:
            break

        chunk_data_offset = offset + 8
        chunk_crc_offset = chunk_data_offset + length

        if chunk_crc_offset + 4 > file_size:
            issues.append(DiagnosticIssue(
                "ERR_CHUNK_TRUNCATED",
                f"Chunk '{chunk_type}' at offset {offset} is truncated. Expected {length} bytes but reached EOF.",
                Severity.CRITICAL,
                offset,
                file_size - offset,
                "Clamp chunk or append missing bytes."
            ))
            break

        stored_crc = struct.unpack(">I", raw_data[chunk_crc_offset : chunk_crc_offset + 4])[0]
        # Calculate expected CRC32 over type + data
        computed_crc = zlib.crc32(raw_data[offset + 4 : chunk_crc_offset]) & 0xFFFFFFFF

        is_crc_valid = (stored_crc == computed_crc)
        if not is_crc_valid:
            crc_errors += 1
            issues.append(DiagnosticIssue(
                "ERR_CRC_MISMATCH",
                f"Chunk '{chunk_type}' CRC mismatch at offset {chunk_crc_offset}: stored 0x{stored_crc:08X} != computed 0x{computed_crc:08X}.",
                Severity.CRITICAL,
                chunk_crc_offset,
                4,
                f"Recalculate and rewrite valid CRC32 (0x{computed_crc:08X})."
            ))
            available_repairs.append("repair_png_crc")

        chunk_desc = KNOWN_PNG_CHUNKS.get(chunk_type, f"Ancillary Chunk '{chunk_type}'")
        hex_preview = " ".join(f"{b:02X}" for b in raw_data[offset : min(offset + 12, file_size)])

        segments.append(MarkerSegment(
            offset=offset,
            length=length + 12,
            code=f"CHUNK_{chunk_type}",
            name=f"{chunk_type} ({chunk_desc})",
            info=f"Size: {length} bytes, CRC: {'Valid' if is_crc_valid else 'CORRUPTED'}",
            is_valid=is_crc_valid,
            hex_preview=hex_preview
        ))

        if chunk_type == "IHDR":
            has_ihdr = True
        elif chunk_type == "IDAT":
            has_idat = True
            idat_bytes_total += length
        elif chunk_type == "IEND":
            has_iend = True
            offset = chunk_crc_offset + 4
            break

        offset = chunk_crc_offset + 4

    # 3. Check Termination & Essentials
    if not has_ihdr:
        issues.append(DiagnosticIssue("ERR_MISSING_IHDR", "Missing mandatory IHDR chunk.", Severity.CRITICAL))
    if not has_idat:
        issues.append(DiagnosticIssue("ERR_MISSING_IDAT", "Missing IDAT compressed image scanline chunks.", Severity.CRITICAL))
    if not has_iend:
        issues.append(DiagnosticIssue(
            "ERR_MISSING_IEND",
            "Missing mandatory IEND chunk at end of PNG file. Interrupted download or cut-off file.",
            Severity.CRITICAL,
            file_size,
            0,
            "Append valid 12-byte IEND termination chunk."
        ))
        available_repairs.append("append_iend_chunk")

    # 4. Test Decode
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
            available_repairs.append("salvage_idat_scanlines")

    # 5. Calculate Score
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
            score = max(20, min(score, 60))
        else:
            score = max(5, min(score, 30))

    integrity_score = max(0, min(score, 100))
    is_corrupted = integrity_score < 95 or len(issues) > 0

    return ImageAnalysisResult(
        filepath=filepath,
        filename=p.name,
        file_size=file_size,
        image_format="PNG",
        is_corrupt=is_corrupted,
        integrity_score=integrity_score,
        issues=issues,
        segments=segments,
        embedded_previews=[],
        decode_success=decode_success,
        decode_partial=decode_partial,
        decoded_width=decoded_width,
        decoded_height=decoded_height,
        decode_error=decode_error,
        recoverable=len(available_repairs) > 0 or not has_iend or crc_errors > 0 or decode_partial,
        available_repairs=list(set(available_repairs))
    )

def repair_png_advanced(filepath: str, action: str, output_dir: Path) -> List[RecoveryArtifact]:
    """
    Precision PNG repair engine:
    - 'smart_auto': repairs signature, recalculates all bad CRCs, appends missing IEND, and extracts image
    - 'repair_png_crc': rewrites proper IEEE 802.3 CRC32 checksums
    - 'append_iend_chunk': appends missing IEND terminator
    - 'repair_png_signature': restores 8-byte PNG magic header
    """
    p = Path(filepath)
    raw_data = bytearray(p.read_bytes())
    file_size = len(raw_data)
    artifacts: List[RecoveryArtifact] = []

    # 1. Repair Signature
    if not raw_data.startswith(PNG_SIGNATURE):
        png_idx = raw_data.find(b"PNG\r\n\x1a\n")
        if png_idx != -1:
            raw_data = bytearray(PNG_SIGNATURE + raw_data[png_idx + 7:])
        else:
            raw_data = bytearray(PNG_SIGNATURE + raw_data)

    # 2. Parse and recalculate CRCs for all chunks
    offset = 8
    clean_stream = bytearray(raw_data[:8])
    has_iend = False

    while offset + 8 <= len(raw_data):
        try:
            length = struct.unpack(">I", raw_data[offset : offset + 4])[0]
            chunk_type = raw_data[offset + 4 : offset + 8]
        except Exception:
            break

        chunk_data_end = offset + 8 + length
        if chunk_data_end > len(raw_data):
            # Truncated chunk data - clamp to end of file
            actual_len = len(raw_data) - (offset + 8)
            if actual_len > 0:
                length = actual_len
                chunk_data = raw_data[offset + 8 : offset + 8 + actual_len]
                chunk_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
                clean_stream.extend(struct.pack(">I", length))
                clean_stream.extend(chunk_type)
                clean_stream.extend(chunk_data)
                clean_stream.extend(struct.pack(">I", chunk_crc))
            break

        chunk_data = raw_data[offset + 8 : chunk_data_end]
        # Calculate true CRC32
        chunk_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF

        clean_stream.extend(struct.pack(">I", length))
        clean_stream.extend(chunk_type)
        clean_stream.extend(chunk_data)
        clean_stream.extend(struct.pack(">I", chunk_crc))

        if chunk_type == b"IEND":
            has_iend = True
            break

        offset = chunk_data_end + 4

    # 3. Append missing IEND if absent
    if not has_iend:
        clean_stream.extend(PNG_IEND_CHUNK)

    # 4. Save and Test Load
    try:
        with Image.open(io.BytesIO(clean_stream)) as test_img:
            w, h = test_img.size
            out_name = f"{p.stem}_recovered_clean.png"
            out_file = output_dir / out_name
            test_img.save(str(out_file), "PNG")

            buf = io.BytesIO()
            test_img.save(buf, "PNG")
            b64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"

            artifacts.append(RecoveryArtifact(
                method="PNG Chunk & CRC32 Auto-Repair",
                filename=out_name,
                filepath=str(out_file.resolve()),
                width=w,
                height=h,
                size=out_file.stat().st_size,
                preview_base64=b64,
                description="Reconstructed PNG signature, recalculated valid chunk CRC32 checksums, and restored IEND."
            ))
    except Exception:
        # Fallback raw write
        out_name = f"{p.stem}_repaired_raw.png"
        out_file = output_dir / out_name
        out_file.write_bytes(clean_stream)
        artifacts.append(RecoveryArtifact(
            method="PNG Binary Stream Patch",
            filename=out_name,
            filepath=str(out_file.resolve()),
            width=0,
            height=0,
            size=len(clean_stream),
            preview_base64=None,
            description="Patched PNG chunk headers and IEND terminator in raw byte stream."
        ))

    return artifacts
