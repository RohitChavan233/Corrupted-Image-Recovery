import hashlib
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image, ImageOps
import numpy as np
from ..config import SUPPORTED_EXTENSIONS

def calculate_dhash(image_path: str, hash_size: int = 8) -> str:
    """Compute difference hash (dHash) for fast perceptual image matching."""
    try:
        with Image.open(image_path) as img:
            img = ImageOps.grayscale(img)
            # resize to (hash_size + 1, hash_size)
            img = img.resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
            pixels = np.array(img, dtype=np.int32)
            # compute differences between adjacent columns
            diff = pixels[:, 1:] > pixels[:, :-1]
            # convert boolean array to hex string
            binary_str = "".join(["1" if b else "0" for b in diff.flatten()])
            return f"{int(binary_str, 2):0{hash_size * hash_size // 4}x}"
    except Exception:
        return ""

def calculate_sha256(filepath: str) -> str:
    """Compute exact binary SHA-256 hash."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hex hashes."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 999
    try:
        v1 = int(hash1, 16)
        v2 = int(hash2, 16)
        x = v1 ^ v2
        return bin(x).count("1")
    except Exception:
        return 999

def scan_folder_for_duplicates(folder_path: str, similarity_threshold: float = 0.90) -> List[Dict[str, Any]]:
    p = Path(folder_path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Invalid directory: {folder_path}")
        
    image_files = []
    for entry in p.iterdir():
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_files.append(str(entry.resolve()))
            
    if len(image_files) < 2:
        return []
        
    # Calculate hashes
    records = []
    for fp in image_files:
        dh = calculate_dhash(fp)
        sha = calculate_sha256(fp)
        p_obj = Path(fp)
        records.append({
            "filepath": fp,
            "filename": p_obj.name,
            "size": p_obj.stat().st_size,
            "dhash": dh,
            "sha256": sha
        })
        
    # Max distance allowed based on 64-bit dHash:
    # 64 bits * (1.0 - threshold)
    max_dist = int(64 * (1.0 - similarity_threshold))
    
    clusters = []
    visited = set()
    
    for i in range(len(records)):
        if records[i]["filepath"] in visited:
            continue
            
        group = [records[i]]
        
        for j in range(i + 1, len(records)):
            if records[j]["filepath"] in visited:
                continue
                
            # Exact match check
            if records[i]["sha256"] == records[j]["sha256"]:
                group.append(records[j])
                visited.add(records[j]["filepath"])
                continue
                
            # Perceptual match check
            dist = hamming_distance(records[i]["dhash"], records[j]["dhash"])
            if dist <= max_dist:
                similarity = round((1.0 - (dist / 64.0)) * 100, 1)
                rec_copy = dict(records[j])
                rec_copy["similarity"] = similarity
                group.append(rec_copy)
                visited.add(records[j]["filepath"])
                
        if len(group) > 1:
            visited.add(records[i]["filepath"])
            clusters.append({
                "cluster_id": len(clusters) + 1,
                "count": len(group),
                "items": group
            })
            
    return clusters
