import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path.home() / ".photorecover"
DATA_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_CACHE_DIR = DATA_DIR / "thumbnails"
THUMBNAIL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

RECOVERED_DIR = DATA_DIR / "recovered"
RECOVERED_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "catalog.db"

# Server configuration
HOST = "127.0.0.1"
PORT = 8765

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif",
    ".ico", ".ppm", ".pgm", ".pbm", ".avif", ".heic"
}
