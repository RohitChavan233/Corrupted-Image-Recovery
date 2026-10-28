"""
Advanced Image Recovery Service Wrapper
Connects the FastAPI application endpoints with the modular Advanced Recovery Engine
(supporting deep JPEG marker reconstruction, PNG CRC & IEND repair, BMP header realignment, and forensic carving).
"""
from typing import Dict, Any, List, Optional
from .recovery import (
    analyze_image_deep,
    execute_advanced_recovery,
    batch_scan_advanced,
    batch_recover_advanced
)

def analyze_jpeg(filepath: str) -> Dict[str, Any]:
    """Analyzes any image format (JPEG, PNG, BMP) with deep marker/chunk inspection."""
    return analyze_image_deep(filepath).to_dict()

def perform_jpeg_recovery(
    filepath: str,
    recovery_type: str = "auto",
    output_dir: Optional[str] = None,
    donor_filepath: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes precision recovery actions:
      - 'auto' / 'smart_auto': multi-pass automatic repair (thumbnail fusion, donor grafting, lossless bitstream repair, HD thumbnail)
      - 'thumbnail_fusion': reconstruct complete image by blending native scanlines with upscaled intact thumbnail (0% grey)
      - 'thumbnail_hd': upscale and enhance intact embedded thumbnail to high definition (complete scene)
      - 'donor_reference': graft headers from intact donor reference photo in same folder
      - 'extract_thumbnail' / 'carve_embedded_previews': extract raw embedded EXIF previews
      - 'graft_baseline_header': inject standard baseline Annex K DQT/DHT tables
      - 'repair_byte_stuffing': fix rogue 0xFF bytes inside entropy scanlines
      - 'fix_eoi' / 'render_partial_scanlines': decode available scanlines with proper EOI/IEND termination
      - 'repair_png_crc': recalculate and rewrite valid IEEE 802.3 CRC32 checksums for PNG chunks
      - 'deep_binary_carve': forensic scan for all embedded image streams
    """
    action_map = {
        "auto": "smart_auto",
        "thumbnail_fusion": "thumbnail_fusion",
        "pristine_crop": "pristine_crop",
        "inpainted_fill": "inpainted_fill",
        "thumbnail_hd": "thumbnail_hd",
        "donor_reference": "donor_reference",
        "extract_thumbnail": "carve_embedded_previews",
        "fix_eoi": "fix_eoi_and_salvage",
        "render_partial": "render_partial_scanlines",
        "donor_header": "graft_baseline_header",
        "byte_stuffing": "repair_byte_stuffing",
        "crc_repair": "repair_png_crc",
        "deep_carve": "deep_binary_carve"
    }
    action = action_map.get(recovery_type, recovery_type)
    return execute_advanced_recovery(filepath, action, output_dir, donor_filepath=donor_filepath)

def get_suggested_donors(filepath: str) -> List[Dict[str, Any]]:
    """Finds candidate intact reference images in the same folder as filepath."""
    from .recovery import suggest_donors_in_folder
    return suggest_donors_in_folder(filepath)

def batch_scan_corrupted_jpegs(
    folder_path: Optional[str] = None,
    file_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Scans all photos (JPEG, PNG, BMP) in a directory or file list for corruption."""
    return batch_scan_advanced(folder_path, file_list)

def batch_recover_jpegs(
    file_list: List[str],
    recovery_type: str = "auto",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Recovers multiple photos in batch mode."""
    action_map = {
        "auto": "smart_auto",
        "thumbnail_fusion": "thumbnail_fusion",
        "pristine_crop": "pristine_crop",
        "inpainted_fill": "inpainted_fill",
        "thumbnail_hd": "thumbnail_hd",
        "donor_reference": "donor_reference",
        "extract_thumbnail": "carve_embedded_previews",
        "fix_eoi": "fix_eoi_and_salvage",
        "render_partial": "render_partial_scanlines",
        "donor_header": "graft_baseline_header",
        "deep_carve": "deep_binary_carve"
    }
    action = action_map.get(recovery_type, recovery_type)
    return batch_recover_advanced(file_list, action, output_dir)
