import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from ...config import RECOVERED_DIR
from .base import ImageAnalysisResult, RecoveryArtifact
from .jpeg_engine import analyze_jpeg_deep, repair_jpeg_advanced
from .png_engine import analyze_png_deep, repair_png_advanced
from .bmp_engine import analyze_bmp_deep, repair_bmp_advanced
from .deep_carver import deep_carve_all_images

def detect_image_format(filepath: str) -> str:
    p = Path(filepath)
    ext = p.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "JPEG"
    if ext == ".png":
        return "PNG"
    if ext == ".bmp":
        return "BMP"

    # Inspect magic bytes
    try:
        with open(filepath, "rb") as f:
            header = f.read(32)
            if header.startswith(b"\xff\xd8"):
                return "JPEG"
            if header.startswith(b"\x89PNG\r\n\x1a\n") or b"PNG\r\n" in header:
                return "PNG"
            if header.startswith(b"BM"):
                return "BMP"
    except Exception:
        pass

    return "JPEG" # Default to JPEG

def analyze_image_deep(filepath: str) -> ImageAnalysisResult:
    fmt = detect_image_format(filepath)
    if fmt == "PNG":
        return analyze_png_deep(filepath)
    elif fmt == "BMP":
        return analyze_bmp_deep(filepath)
    else:
        return analyze_jpeg_deep(filepath)

def execute_advanced_recovery(
    filepath: str,
    action: str = "smart_auto",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    target_dir = Path(output_dir) if output_dir else RECOVERED_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    analysis = analyze_image_deep(filepath)
    fmt = analysis.image_format

    artifacts: List[RecoveryArtifact] = []

    if action == "deep_binary_carve":
        artifacts = deep_carve_all_images(filepath, target_dir)
    elif fmt == "PNG":
        artifacts = repair_png_advanced(filepath, action, target_dir)
    elif fmt == "BMP":
        artifacts = repair_bmp_advanced(filepath, action, target_dir)
    else:
        artifacts = repair_jpeg_advanced(filepath, action, target_dir)

    # If primary repair yielded 0 artifacts and action was smart_auto, attempt deep carver fallback
    if len(artifacts) == 0 and action in ("smart_auto", "auto"):
        carved = deep_carve_all_images(filepath, target_dir)
        if carved:
            artifacts.extend(carved)

    # CRITICAL: Always ensure highest resolution artifacts are sorted to the very top
    artifacts.sort(key=lambda a: (a.width * a.height, a.size), reverse=True)

    # Format recovery files
    recovered_files = [
        {
            "method": art.method,
            "filename": art.filename,
            "filepath": art.filepath,
            "width": art.width,
            "height": art.height,
            "size": art.size,
            "preview_base64": art.preview_base64,
            "description": art.description
        }
        for art in artifacts
    ]

    return {
        "original_file": filepath,
        "analysis": analysis.to_dict(),
        "recovered_count": len(recovered_files),
        "recovered_files": recovered_files,
        "message": f"Advanced recovery complete. {len(recovered_files)} artifact(s) generated in {target_dir}."
    }

def batch_scan_advanced(
    folder_path: Optional[str] = None,
    file_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    targets = []
    if file_list:
        targets = [f for f in file_list if Path(f).exists()]
    elif folder_path and Path(folder_path).is_dir():
        for entry in Path(folder_path).iterdir():
            if entry.is_file() and entry.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
                targets.append(str(entry.resolve()))

    results = []
    corrupt_count = 0
    recoverable_count = 0

    for filepath in targets:
        try:
            analysis = analyze_image_deep(filepath)
            ad = analysis.to_dict()
            if ad.get("is_corrupt", False):
                corrupt_count += 1
            if ad.get("recoverable", False):
                recoverable_count += 1
            results.append(ad)
        except Exception as e:
            results.append({
                "filepath": filepath,
                "filename": Path(filepath).name,
                "file_size": 0,
                "image_format": "UNKNOWN",
                "is_corrupt": True,
                "integrity_score": 0,
                "issues": [{"code": "ERR_UNKNOWN", "message": str(e), "severity": "critical"}],
                "issues_summary": [str(e)],
                "markers": [],
                "embedded_thumbnails": [],
                "recoverable": False
            })
            corrupt_count += 1

    return {
        "total_scanned": len(targets),
        "corrupt_count": corrupt_count,
        "recoverable_count": recoverable_count,
        "results": results
    }

def batch_recover_advanced(
    file_list: List[str],
    action: str = "smart_auto",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    target_dir = Path(output_dir) if output_dir else RECOVERED_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_recovered_artifacts = 0

    for filepath in file_list:
        if not Path(filepath).exists():
            continue
        try:
            rec = execute_advanced_recovery(filepath, action, str(target_dir))
            total_recovered_artifacts += rec["recovered_count"]
            results.append(rec)
        except Exception as e:
            results.append({
                "original_file": filepath,
                "recovered_count": 0,
                "recovered_files": [],
                "error": str(e)
            })

    return {
        "total_files_processed": len(file_list),
        "total_recovered_artifacts": total_recovered_artifacts,
        "output_dir": str(target_dir.resolve()),
        "results": results
    }
