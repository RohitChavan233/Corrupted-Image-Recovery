import datetime
from pathlib import Path
from typing import Dict, Any
import mss
from PIL import Image
from ..config import DATA_DIR

def capture_desktop_screenshot(target_folder: str = "") -> Dict[str, Any]:
    with mss.mss() as sct:
        monitor = sct.monitors[0] # primary all-monitor bounding box
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Screenshot_{now_str}.png"
        
        if target_folder and Path(target_folder).is_dir():
            out_path = Path(target_folder) / filename
        else:
            out_path = DATA_DIR / filename
            
        img.save(str(out_path), "PNG")
        
        return {
            "filename": filename,
            "filepath": str(out_path.resolve()),
            "width": img.width,
            "height": img.height,
            "size": out_path.stat().st_size
        }
