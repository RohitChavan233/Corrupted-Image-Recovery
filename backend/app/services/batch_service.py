import os
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageOps
from .image_service import process_image

# In-memory batch job tracking
BATCH_JOBS: Dict[str, Dict[str, Any]] = {}

def start_batch_job(
    file_list: List[str],
    output_dir: str,
    target_format: Optional[str] = None,
    output_quality: int = 90,
    resize_mode: Optional[str] = None, # 'percent', 'dimensions', None
    resize_percent: int = 100,
    resize_width: Optional[int] = None,
    resize_height: Optional[int] = None,
    rename_pattern: Optional[str] = None, # e.g. "{index}_{name}_{width}x{height}"
    filter_name: Optional[str] = None,
    watermark_text: Optional[str] = None
) -> str:
    job_id = str(uuid.uuid4())
    
    BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "total": len(file_list),
        "completed": 0,
        "failed": 0,
        "is_cancelled": False,
        "status": "in_progress",
        "results": [],
        "created_at": datetime.datetime.now().isoformat()
    }
    
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Process sequentially or in thread
    for idx, filepath in enumerate(file_list, start=1):
        if BATCH_JOBS[job_id]["is_cancelled"]:
            BATCH_JOBS[job_id]["status"] = "cancelled"
            break
            
        p = Path(filepath)
        if not p.exists():
            BATCH_JOBS[job_id]["failed"] += 1
            BATCH_JOBS[job_id]["results"].append({
                "original": filepath,
                "status": "error",
                "error": "File does not exist"
            })
            continue
            
        try:
            with Image.open(filepath) as img_orig:
                orig_w, orig_h = img_orig.size
                
            # Determine target dimensions if resizing
            resize_dict = None
            if resize_mode == "percent" and resize_percent != 100:
                scale = resize_percent / 100.0
                resize_dict = {
                    "width": max(1, int(orig_w * scale)),
                    "height": max(1, int(orig_h * scale))
                }
            elif resize_mode == "dimensions" and resize_width and resize_height:
                resize_dict = {"width": resize_width, "height": resize_height}
                
            # Execute processing
            processed_bytes, mime = process_image(
                filepath=filepath,
                resize=resize_dict,
                filter_name=filter_name,
                watermark_text=watermark_text,
                output_format=target_format,
                output_quality=output_quality
            )
            
            # Format filename
            ext = (target_format or p.suffix.replace(".", "")).lower()
            if ext == "jpeg":
                ext = "jpg"
                
            final_w = resize_dict["width"] if resize_dict else orig_w
            final_h = resize_dict["height"] if resize_dict else orig_h
            
            if rename_pattern:
                now_str = datetime.datetime.now().strftime("%Y%m%d")
                clean_name = rename_pattern.format(
                    name=p.stem,
                    index=f"{idx:03d}",
                    width=final_w,
                    height=final_h,
                    date=now_str
                )
                out_filename = f"{clean_name}.{ext}"
            else:
                out_filename = f"{p.stem}_converted.{ext}"
                
            target_file_path = out_dir_path / out_filename
            target_file_path.write_bytes(processed_bytes)
            
            BATCH_JOBS[job_id]["completed"] += 1
            BATCH_JOBS[job_id]["results"].append({
                "original": filepath,
                "output": str(target_file_path.resolve()),
                "status": "success",
                "width": final_w,
                "height": final_h,
                "size": len(processed_bytes)
            })
        except Exception as e:
            BATCH_JOBS[job_id]["failed"] += 1
            BATCH_JOBS[job_id]["results"].append({
                "original": filepath,
                "status": "error",
                "error": str(e)
            })
            
    if not BATCH_JOBS[job_id]["is_cancelled"]:
        BATCH_JOBS[job_id]["status"] = "completed"
        
    return job_id

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return BATCH_JOBS.get(job_id)

def cancel_job(job_id: str) -> bool:
    if job_id in BATCH_JOBS:
        BATCH_JOBS[job_id]["is_cancelled"] = True
        BATCH_JOBS[job_id]["status"] = "cancelling"
        return True
    return False
