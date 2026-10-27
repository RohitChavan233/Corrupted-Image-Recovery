import io
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ExifTags
from ..database import update_file_record, get_file_record

def get_exif_data(filepath: str) -> Dict[str, Any]:
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
        
    exif_dict: Dict[str, Any] = {}
    gps_info: Dict[str, Any] = {}
    
    try:
        with Image.open(filepath) as img:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, val in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    # Handle bytes / non-serializable objects
                    if isinstance(val, bytes):
                        try:
                            val = val.decode("utf-8", errors="replace").strip("\x00")
                        except Exception:
                            val = f"<bytes length={len(val)}>"
                    exif_dict[tag_name] = str(val)
                    
                # Check for GPS IFD
                gps_ifd = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_ifd:
                    for g_id, g_val in gps_ifd.items():
                        g_name = ExifTags.GPSTAGS.get(g_id, str(g_id))
                        gps_info[g_name] = str(g_val)
                        
                    # Calculate Decimal Degrees for GPS
                    try:
                        lat = gps_ifd.get(2) # GPSLatitude
                        lat_ref = gps_ifd.get(1) # GPSLatitudeRef
                        lon = gps_ifd.get(4) # GPSLongitude
                        lon_ref = gps_ifd.get(3) # GPSLongitudeRef
                        
                        if lat and lon and lat_ref and lon_ref:
                            lat_deg = float(lat[0]) + float(lat[1])/60.0 + float(lat[2])/3600.0
                            if lat_ref in ("S", "s"):
                                lat_deg = -lat_deg
                                
                            lon_deg = float(lon[0]) + float(lon[1])/60.0 + float(lon[2])/3600.0
                            if lon_ref in ("W", "w"):
                                lon_deg = -lon_deg
                                
                            gps_info["latitude_decimal"] = round(lat_deg, 6)
                            gps_info["longitude_decimal"] = round(lon_deg, 6)
                            gps_info["maps_url"] = f"https://www.google.com/maps?q={lat_deg},{lon_deg}"
                    except Exception:
                        pass
    except Exception:
        pass
        
    # Get user annotations from SQLite
    db_rec = get_file_record(filepath) or {}
    
    return {
        "filename": p.name,
        "filepath": filepath,
        "filesize": p.stat().st_size,
        "mtime": p.stat().st_mtime,
        "camera_make": exif_dict.get("Make", "Unknown"),
        "camera_model": exif_dict.get("Model", "Unknown"),
        "lens_model": exif_dict.get("LensModel", exif_dict.get("Lens", "Unknown")),
        "date_taken": exif_dict.get("DateTimeOriginal", exif_dict.get("DateTime", "Unknown")),
        "exposure_time": exif_dict.get("ExposureTime", "Unknown"),
        "f_number": exif_dict.get("FNumber", "Unknown"),
        "iso_speed": exif_dict.get("ISOSpeedRatings", exif_dict.get("PhotographicSensitivity", "Unknown")),
        "focal_length": exif_dict.get("FocalLength", "Unknown"),
        "software": exif_dict.get("Software", "Unknown"),
        "artist_copyright": exif_dict.get("Artist", exif_dict.get("Copyright", "Unknown")),
        "gps": gps_info,
        "all_exif": exif_dict,
        "user_rating": db_rec.get("rating", 0),
        "color_label": db_rec.get("color_label", ""),
        "user_tags": db_rec.get("tags", ""),
        "user_comment": db_rec.get("comment", "")
    }

def update_annotations(
    filepath: str,
    rating: Optional[int] = None,
    color_label: Optional[str] = None,
    tags: Optional[str] = None,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    fields = {}
    if rating is not None:
        fields["rating"] = max(0, min(5, rating))
    if color_label is not None:
        fields["color_label"] = color_label
    if tags is not None:
        fields["tags"] = tags
    if comment is not None:
        fields["comment"] = comment
        
    if fields:
        update_file_record(filepath, fields)
        
    return get_exif_data(filepath)

def strip_metadata(filepath: str, output_path: Optional[str] = None) -> str:
    p = Path(filepath)
    target = Path(output_path) if output_path else p.with_name(f"{p.stem}_clean{p.suffix}")
    
    with Image.open(filepath) as img:
        # Create a new clean image copying pixel data without EXIF or metadata
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        
        # Save without any EXIF
        fmt = img.format or "JPEG"
        clean_img.save(str(target), format=fmt)
        
    return str(target.resolve())
