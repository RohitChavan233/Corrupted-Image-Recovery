from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

class Severity(str, Enum):
    CRITICAL = "critical"  # Decoder crashes or file unopenable
    WARNING = "warning"    # Partial loss, missing termination, or invalid checksum
    INFO = "info"          # Metadata warning or minor anomaly

@dataclass
class DiagnosticIssue:
    code: str
    message: str
    severity: Severity
    offset: Optional[int] = None
    length: Optional[int] = None
    suggested_fix: Optional[str] = None

@dataclass
class MarkerSegment:
    offset: int
    length: int
    code: str
    name: str
    info: str = ""
    is_valid: bool = True
    hex_preview: str = ""

@dataclass
class EmbeddedPreview:
    offset: int
    size: int
    width: int
    height: int
    format: str
    preview_base64: str

@dataclass
class RecoveryArtifact:
    method: str
    filename: str
    filepath: str
    width: int
    height: int
    size: int
    preview_base64: Optional[str]
    description: str

@dataclass
class ImageAnalysisResult:
    filepath: str
    filename: str
    file_size: int
    image_format: str
    is_corrupt: bool
    integrity_score: int
    issues: List[DiagnosticIssue] = field(default_factory=list)
    segments: List[MarkerSegment] = field(default_factory=list)
    embedded_previews: List[EmbeddedPreview] = field(default_factory=list)
    decode_success: bool = False
    decode_partial: bool = False
    decoded_width: int = 0
    decoded_height: int = 0
    decode_error: Optional[str] = None
    recoverable: bool = False
    available_repairs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["issues_summary"] = [i["message"] for i in d["issues"]]
        # Format compatibility with earlier UI
        d["markers"] = [
            {
                "marker": s["code"],
                "name": s["name"],
                "offset": s["offset"],
                "length": s["length"],
                "info": s.get("info", "")
            }
            for s in d["segments"]
        ]
        d["embedded_thumbnails"] = d["embedded_previews"]
        d["embedded_thumbnail_count"] = len(d["embedded_previews"])
        d["has_soi"] = any(s["code"] == "0xFFD8" for s in d["segments"])
        d["has_eoi"] = any(s["code"] == "0xFFD9" for s in d["segments"])
        d["has_dqt"] = any(s["code"] == "0xFFDB" for s in d["segments"])
        d["has_dht"] = any(s["code"] == "0xFFC4" for s in d["segments"])
        d["has_sof"] = any(s["code"] in ("0xFFC0", "0xFFC2") for s in d["segments"])
        d["has_sos"] = any(s["code"] == "0xFFDA" for s in d["segments"])
        d["has_app1"] = any(s["code"] == "0xFFE1" for s in d["segments"])
        d["sos_offset"] = next((s["offset"] for s in d["segments"] if s["code"] == "0xFFDA"), -1)
        return d
