import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .config import HOST, PORT, RECOVERED_DIR
from .database import init_db, get_favorites, add_favorite, remove_favorite
from .services.filesystem_service import get_system_drives_and_places, list_directory
from .services.image_service import get_or_generate_thumbnail, process_image
from .services.jpeg_recovery_service import (
    analyze_jpeg, 
    perform_jpeg_recovery, 
    batch_scan_corrupted_jpegs, 
    batch_recover_jpegs
)
from .services.duplicate_service import scan_folder_for_duplicates
from .services.screenshot_service import capture_desktop_screenshot

# Initialize database
init_db()

app = FastAPI(title="Photorecover / XnView MP Rebuild API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Models -----------------
class BrowseRequest(BaseModel):
    folder_path: str

class FavoriteRequest(BaseModel):
    folder_path: str

class MetadataUpdateRequest(BaseModel):
    filepath: str
    rating: Optional[int] = None
    color_label: Optional[str] = None
    tags: Optional[str] = None
    comment: Optional[str] = None

class StripMetadataRequest(BaseModel):
    filepath: str
    output_path: Optional[str] = None

class ImageProcessRequest(BaseModel):
    filepath: str
    crop: Optional[Dict[str, int]] = None
    resize: Optional[Dict[str, int]] = None
    rotate: Optional[float] = None
    flip_h: bool = False
    flip_v: bool = False
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0
    hue: float = 0.0
    filter_name: Optional[str] = None
    watermark_text: Optional[str] = None
    watermark_color: str = "#ffffff"
    watermark_opacity: float = 0.8
    watermark_position: str = "bottom-right"
    output_format: Optional[str] = None
    output_quality: int = 90
    save_as: Optional[str] = None # If provided, saves to disk

class JpegRecoveryRequest(BaseModel):
    filepath: str
    recovery_type: str = "auto"

class BatchJobRequest(BaseModel):
    file_list: List[str]
    output_dir: str
    target_format: Optional[str] = None
    output_quality: int = 90
    resize_mode: Optional[str] = None
    resize_percent: int = 100
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    rename_pattern: Optional[str] = None
    filter_name: Optional[str] = None
    watermark_text: Optional[str] = None

class DuplicateScanRequest(BaseModel):
    folder_path: str
    similarity_threshold: float = 0.90

class ScreenshotRequest(BaseModel):
    target_folder: str = ""

# ----------------- Filesystem Endpoints -----------------
@app.get("/api/filesystem/places")
def api_places():
    return get_system_drives_and_places()

@app.post("/api/filesystem/browse")
def api_browse(req: BrowseRequest):
    try:
        return list_directory(req.folder_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/filesystem/favorites")
def api_get_favorites():
    return {"favorites": get_favorites()}

@app.post("/api/filesystem/favorites/add")
def api_add_favorite(req: FavoriteRequest):
    add_favorite(req.folder_path)
    return {"success": True, "favorites": get_favorites()}

@app.post("/api/filesystem/favorites/remove")
def api_remove_favorite(req: FavoriteRequest):
    remove_favorite(req.folder_path)
    return {"success": True, "favorites": get_favorites()}

@app.post("/api/filesystem/reveal")
def api_reveal_path(req: BrowseRequest):
    import subprocess
    import os
    target = os.path.normpath(req.folder_path)
    if os.path.exists(target):
        try:
            if os.path.isdir(target):
                subprocess.Popen(f'explorer "{target}"')
            else:
                subprocess.Popen(f'explorer /select,"{target}"')
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Path does not exist"}

# ----------------- Image Endpoints -----------------
@app.get("/api/images/thumbnail")
def api_thumbnail(path: str = Query(...), size: int = Query(256)):
    try:
        data, mime = get_or_generate_thumbnail(path, size)
        return Response(content=data, media_type=mime, headers={"Cache-Control": "public, max-age=86400"})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/images/raw")
def api_raw_image(path: str = Query(...)):
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

@app.post("/api/images/process")
def api_process_image(req: ImageProcessRequest):
    try:
        processed_bytes, mime = process_image(
            filepath=req.filepath,
            crop=req.crop,
            resize=req.resize,
            rotate=req.rotate,
            flip_h=req.flip_h,
            flip_v=req.flip_v,
            brightness=req.brightness,
            contrast=req.contrast,
            saturation=req.saturation,
            gamma=req.gamma,
            hue=req.hue,
            filter_name=req.filter_name,
            watermark_text=req.watermark_text,
            watermark_color=req.watermark_color,
            watermark_opacity=req.watermark_opacity,
            watermark_position=req.watermark_position,
            output_format=req.output_format,
            output_quality=req.output_quality
        )
        
        if req.save_as:
            out_p = Path(req.save_as)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_bytes(processed_bytes)
            return {
                "success": True,
                "saved_to": str(out_p.resolve()),
                "size": len(processed_bytes)
            }
            
        return Response(content=processed_bytes, media_type=mime)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Metadata Endpoints -----------------
@app.get("/api/metadata")
def api_metadata(path: str = Query(...)):
    try:
        return get_exif_data(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/metadata/update")
def api_update_metadata(req: MetadataUpdateRequest):
    try:
        return update_annotations(
            filepath=req.filepath,
            rating=req.rating,
            color_label=req.color_label,
            tags=req.tags,
            comment=req.comment
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/metadata/strip")
def api_strip_metadata(req: StripMetadataRequest):
    try:
        saved_path = strip_metadata(req.filepath, req.output_path)
        return {"success": True, "saved_path": saved_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Corrupted JPEG & Recovery Endpoints -----------------
class BatchRecoveryScanRequest(BaseModel):
    folder_path: Optional[str] = None
    file_list: Optional[List[str]] = None

class BatchRecoveryExecuteRequest(BaseModel):
    file_list: List[str]
    recovery_type: str = "auto"
    output_dir: Optional[str] = None

@app.get("/api/recovery/inspect")
def api_inspect_jpeg(path: str = Query(...)):
    try:
        return analyze_jpeg(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/recovery/execute")
def api_execute_recovery(req: JpegRecoveryRequest):
    try:
        return perform_jpeg_recovery(req.filepath, req.recovery_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recovery/batch-scan")
def api_batch_scan_recovery(req: BatchRecoveryScanRequest):
    try:
        return batch_scan_corrupted_jpegs(req.folder_path, req.file_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/recovery/batch-execute")
def api_batch_execute_recovery(req: BatchRecoveryExecuteRequest):
    try:
        return batch_recover_jpegs(req.file_list, req.recovery_type, req.output_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Batch Processing Endpoints -----------------
@app.post("/api/batch/start")
def api_start_batch(req: BatchJobRequest, background_tasks: BackgroundTasks):
    try:
        job_id = start_batch_job(
            file_list=req.file_list,
            output_dir=req.output_dir,
            target_format=req.target_format,
            output_quality=req.output_quality,
            resize_mode=req.resize_mode,
            resize_percent=req.resize_percent,
            resize_width=req.resize_width,
            resize_height=req.resize_height,
            rename_pattern=req.rename_pattern,
            filter_name=req.filter_name,
            watermark_text=req.watermark_text
        )
        return {"job_id": job_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/batch/status/{job_id}")
def api_batch_status(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.post("/api/batch/cancel/{job_id}")
def api_batch_cancel(job_id: str):
    success = cancel_job(job_id)
    return {"success": success}

# ----------------- Duplicate Detection Endpoints -----------------
@app.post("/api/duplicates/scan")
def api_scan_duplicates(req: DuplicateScanRequest):
    try:
        clusters = scan_folder_for_duplicates(req.folder_path, req.similarity_threshold)
        return {"clusters": clusters, "total_clusters": len(clusters)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- Screenshot Endpoints -----------------
@app.post("/api/screenshot/capture")
def api_capture_screenshot(req: ScreenshotRequest):
    try:
        res = capture_desktop_screenshot(req.target_folder)
        return {"success": True, "screenshot": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def api_health():
    return {"status": "ok", "app": "Photorecover"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=True)
