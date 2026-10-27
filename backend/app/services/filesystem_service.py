import os
import string
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..config import SUPPORTED_EXTENSIONS
from ..database import get_connection

def get_system_drives_and_places() -> Dict[str, Any]:
    places = []
    home = Path.home()
    
    # Common user folders
    common_folders = [
        {"name": "Pictures", "path": str(home / "Pictures"), "icon": "image"},
        {"name": "Downloads", "path": str(home / "Downloads"), "icon": "download"},
        {"name": "Desktop", "path": str(home / "Desktop"), "icon": "monitor"},
        {"name": "Documents", "path": str(home / "Documents"), "icon": "folder"},
        {"name": "Home", "path": str(home), "icon": "home"},
    ]
    for cf in common_folders:
        if Path(cf["path"]).exists():
            places.append(cf)
            
    drives = []
    if platform.system() == "Windows":
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                try:
                    # check if accessible
                    os.listdir(drive_path)
                    drives.append({
                        "name": f"Drive ({letter}:)",
                        "path": drive_path,
                        "type": "drive"
                    })
                except (PermissionError, OSError):
                    drives.append({
                        "name": f"Drive ({letter}:)",
                        "path": drive_path,
                        "type": "drive_locked"
                    })
    else:
        drives.append({"name": "Root (/)", "path": "/", "type": "drive"})
        
    return {"places": places, "drives": drives}

def list_directory(folder_path: str) -> Dict[str, Any]:
    p = Path(folder_path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {folder_path}")
        
    subdirs = []
    files = []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        with os.scandir(folder_path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if not entry.name.startswith("."):
                            subdirs.append({
                                "name": entry.name,
                                "path": entry.path,
                                "is_dir": True
                            })
                    elif entry.is_file(follow_symlinks=False):
                        ext = Path(entry.name).suffix.lower()
                        if ext in SUPPORTED_EXTENSIONS:
                            stat = entry.stat()
                            files.append({
                                "name": entry.name,
                                "path": entry.path,
                                "size": stat.st_size,
                                "mtime": stat.st_mtime,
                                "ext": ext[1:],
                                "is_dir": False
                            })
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError) as e:
        conn.close()
        raise PermissionError(f"Cannot access directory: {e}")

    subdirs.sort(key=lambda x: x["name"].lower())
    
    # Query database for existing cached metadata for these files
    if files:
        file_paths = [f["path"] for f in files]
        placeholders = ",".join(["?"] * len(file_paths))
        cursor.execute(f"""
            SELECT filepath, width, height, format, rating, color_label, tags, comment, is_corrupt 
            FROM file_metadata 
            WHERE filepath IN ({placeholders})
        """, file_paths)
        meta_dict = {row["filepath"]: dict(row) for row in cursor.fetchall()}
        
        for f in files:
            m = meta_dict.get(f["path"])
            if m:
                f.update({
                    "width": m.get("width"),
                    "height": m.get("height"),
                    "format": m.get("format"),
                    "rating": m.get("rating", 0),
                    "color_label": m.get("color_label", ""),
                    "tags": m.get("tags", ""),
                    "is_corrupt": m.get("is_corrupt", 0)
                })
            else:
                f.update({
                    "width": None,
                    "height": None,
                    "format": None,
                    "rating": 0,
                    "color_label": "",
                    "tags": "",
                    "is_corrupt": 0
                })

    conn.close()
    
    return {
        "current_path": str(p.resolve()),
        "parent_path": str(p.parent.resolve()) if p.parent != p else None,
        "subdirectories": subdirs,
        "files": files,
        "total_files": len(files),
        "total_subdirs": len(subdirs)
    }
