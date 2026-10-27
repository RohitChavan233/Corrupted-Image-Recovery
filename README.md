# Corrupted-Image-Recovery

> **Advanced Digital Asset Management & In-Depth Image Recovery Suite**  
> *(Inspired by XnView MP — Rebuilt with Python FastAPI + Pillow + React 19 + TypeScript + Vite)*

**Corrupted-Image-Recovery (Photorecover)** is a high-performance desktop image viewer, digital asset manager, photo editor, batch converter, and deep binary image recovery suite. It detects and repairs damaged, truncated, or unopenable photos across JPEG, PNG, BMP, and WebP using byte-level marker manipulation, donor header grafting, CRC32 recalculation, and forensic carving.

---

## 🌟 Key Features

### 1. 🛡️ In-Depth & Advanced Image Recovery Studio
* **Multi-Format Binary Repair Engine**:
  * **JPEG / JPG Recovery**:
    * **Standard Baseline Header Grafting**: Injects standard JPEG Annex K Quantization Tables (DQT Table 0 Luma, Table 1 Chroma) and standard Huffman Tables (DHT DC/AC Luma & Chroma) and SOF0 frame headers into JPEGs with missing or damaged headers.
    * **Rogue Byte-Stuffing Repair**: Detects and sanitizes unescaped `0xFF` bytes inside compressed entropy scanlines that cause decoders to abort or crash with premature EOF.
    * **Embedded EXIF Preview Carving**: Automatically extracts 100% uncorrupted embedded preview thumbnails stored in the EXIF APP1 segment. Even if 60% of a 25MB photo's scanlines are lost, the carved preview is crystal clear.
    * **Partial Scanline Salvage & EOI Termination**: Decodes all readable scanlines up to the point of corruption and applies proper `0xFFD9 EOI` termination.
  * **PNG Deep Recovery**:
    * **8-Byte Signature Repair**: Restores corrupted or byte-shifted PNG headers (`\x89PNG\r\n\x1a\n`).
    * **Chunk-Level CRC32 Recalculation**: Verifies and rewrites valid IEEE 802.3 CRC32 checksums for `IHDR`, `PLTE`, `IDAT`, `IEND` so operating systems and photo viewers don't reject them with "CRC error".
    * **Missing IEND Chunk Rebuilding**: Appends the mandatory 12-byte `IEND` chunk (`\x00\x00\x00\x00IEND\xaeB\x60\x82`) to interrupted or truncated PNG downloads.
  * **BMP Header Reconstruction**:
    * Injects missing `BM` magic bytes (`0x42 0x4D`), recalculates correct file sizes, and repairs corrupted pixel data offsets (`bfOffBits`).
  * **Forensic Deep Binary Stream Carving**:
    * Scans arbitrary files, memory dumps, or damaged storage for embedded JPEG (`\xFF\xD8...\xFF\xD9`) and PNG image streams.
* **Dual Studio Interface**:
  * **Multi-Photo Batch Recovery**: One-click folder scanning, corruption diagnosis matrix, batch repair execution, and interactive recovery gallery with live previews.
  * **Single Photo Deep Inspector**: Hex/marker offsets breakdown, severity-tagged corruption issues, suggested fixes, and side-by-side artifact comparison.

### 3. 🎨 Non-Destructive Photo Editor
- **Adjustments**: Brightness, Contrast, Saturation, Gamma correction with live server preview.
- **Filters**: Sharpen, Gaussian Blur, Vintage Sepia, Grayscale, Invert Colors, Edge Detection, Median Noise Reduction.
- **Transformations**: Lossless 90°/180° rotation, Horizontal & Vertical flipping.
- **Geometry & Resize**: Custom width/height or percentage scaling with aspect ratio locking.
- **Watermarking**: Text overlay with customizable position, font color, and opacity.
- **Safety First**: Saves copies (`_edited.jpg`) by default to protect original files.

### 4. ⚡ Batch Processing Studio
- **Multi-File Queue**: Add individual files or entire folders to the batch queue.
- **Format Conversion**: Convert between WebP, JPEG, PNG, TIFF, BMP, and GIF with custom quality sliders.
- **Template Renaming Engine**: Customize filenames using token patterns:
  - `{name}` — Original filename without extension
  - `{index}` — Zero-padded index number (e.g. `001`, `002`)
  - `{width}x{height}` — Target or original pixel dimensions
  - `{date}` — Current date (e.g. `20261027`)
- **Real-Time Progress**: Live progress bar, status badges, cancel support, and error logs.

### 5. 🔍 Perceptual Duplicate Finder
- **dHash & SHA-256**: Uses 64-bit difference hashing (dHash) and SHA-256 binary matching to detect exact copies and visually similar photos (different resolution, crops, or re-compressed).
- **Similarity Threshold**: Adjustable slider (75% to 100%).
- **Cluster Grouping**: Groups matches with similarity percentage badges.

### 6. 📊 Metadata & EXIF Inspector
- **Comprehensive Camera Data**: Camera Make, Model, Lens, Shutter Speed, Aperture, ISO, Focal Length, Date Taken.
- **GPS Coordinates**: Displays latitude/longitude with one-click Google Maps links.
- **Digital Asset Tagging**: Interactive 5-star ratings, 5 color labels, keywords/tags, and user comments stored in local SQLite database (`catalog.db`).
- **Privacy Stripper**: One-click "Strip Sensitive EXIF / GPS" scrubs personal metadata before publishing.

---

## 🛠️ Technology Stack & Rationale

| Layer | Technology | Rationale |
|---|---|---|
| **Backend API** | Python 3.14 + FastAPI + Uvicorn | Native performance with Pillow 12.2 and NumPy 2.5 without requiring bulky C++ build toolchains. Extremely fast binary streaming. |
| **Image Engine** | Pillow (PIL) + NumPy | SIMD-accelerated resizing, filtering, format encoding, and low-level JPEG byte stream manipulation. |
| **Catalog & Cache** | SQLite (WAL mode) | Fast persistent indexing of ratings, color labels, tags, comments, and thumbnail disk caching. |
| **Frontend Framework** | React 19 + TypeScript + Vite | Instant hot reload, modular state management, modern component architecture. |
| **Styling & Theme** | Tailwind CSS + Custom Dark Theme | Dense, information-rich workstation UI replicating XnView MP's dark aesthetic. |
| **State Management** | Zustand | Single unified reactive store for navigation, view modes, zoom, pan, and selections. |
| **Icons** | Lucide React | High-clarity desktop iconography. |

---

## 🚀 Quick Start Instructions

### Prerequisites
- Python 3.10+ (with `fastapi`, `uvicorn`, `pillow`, `numpy`, `mss`)
- Node.js 18+ and npm

### 1. One-Click Launch (Windows)
Double-click `run.bat` or run:
```powershell
.\run.ps1
```

### 2. Manual Launch
**Terminal 1 — Backend:**
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 📁 Project Structure

```
Photorecover/
├── backend/
│   ├── app/
│   │   ├── config.py                  # Paths, ports, supported extensions
│   │   ├── database.py                # SQLite catalog, ratings, favorites
│   │   ├── main.py                    # FastAPI server & endpoints
│   │   └── services/
│   │       ├── filesystem_service.py  # Drive discovery & folder scanning
│   │       ├── image_service.py       # Thumbnails, filters, adjustments
│   │       ├── jpeg_recovery_service.py # Binary marker parsing & carving
│   │       ├── metadata_service.py    # EXIF, GPS, privacy stripping
│   │       ├── batch_service.py       # Async batch processor & renamer
│   │       ├── duplicate_service.py   # dHash perceptual duplicate scanner
│   │       └── screenshot_service.py  # Desktop screenshot grabber
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts              # API client methods
│   │   ├── store/useAppStore.ts       # Zustand unified store
│   │   ├── types/index.ts             # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── layout/                # Header, Toolbar, StatusBar
│   │   │   ├── browser/               # FolderTree, ThumbnailGrid, Filmstrip
│   │   │   ├── viewer/                # ImageViewer, CompareViewer, Slideshow
│   │   │   ├── editor/                # ImageEditor
│   │   │   ├── recovery/              # RecoveryStudio
│   │   │   ├── batch/                 # BatchStudio
│   │   │   ├── duplicates/            # DuplicateFinder
│   │   │   └── metadata/              # MetadataPanel
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── scripts/
│   └── create_test_samples.py         # Test photo & corrupted sample generator
├── test_samples/                      # Generated test photos & damaged files
├── run.bat                            # Windows batch launcher
├── run.ps1                            # PowerShell launcher
└── README.md
```

---

## 🧪 Verification & Testing

To generate or regenerate the test sample suite:
```powershell
python scripts/create_test_samples.py
```
This generates:
1. `sample_nature.jpg` — Pristine photo with embedded EXIF preview thumbnail.
2. `corrupted_truncated_photo.jpg` — Truncated at 55% with intact embedded thumbnail.
3. `corrupted_missing_eoi.jpg` — Missing 0xFFD9 termination marker.
4. `sample_nature_copy.jpg` & `sample_nature_web_version.jpg` — Duplicates for testing the Duplicate Finder.
5. `sample_graphic.png`, `sample_compressed.webp`, `sample_legacy.bmp`, `sample_animated.gif` — Multi-format testing.
