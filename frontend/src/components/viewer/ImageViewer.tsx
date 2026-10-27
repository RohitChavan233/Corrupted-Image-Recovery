import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCw, 
  FlipHorizontal, 
  FlipVertical, 
  Maximize, 
  ChevronLeft, 
  ChevronRight, 
  Info, 
  Sliders, 
  ShieldAlert,
  ArrowLeft
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { ExifData } from '../../types';

export const ImageViewer: React.FC = () => {
  const {
    activeFile,
    prevImage,
    nextImage,
    zoomLevel,
    setZoomLevel,
    panOffset,
    setPanOffset,
    rotation,
    rotateClockwise,
    flipH,
    toggleFlipH,
    flipV,
    toggleFlipV,
    resetTransform,
    setViewMode
  } = useAppStore();

  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showExifOverlay, setShowExifOverlay] = useState(false);
  const [exifData, setExifData] = useState<ExifData | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Load EXIF for overlay
  useEffect(() => {
    if (activeFile) {
      api.getMetadata(activeFile.path).then(setExifData).catch(() => setExifData(null));
    }
  }, [activeFile]);

  // Handle Mouse Wheel Zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.85;
    setZoomLevel(zoomLevel * factor);
  };

  // Handle Drag / Pan
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPanOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Keyboard Shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

    switch (e.key) {
      case 'ArrowLeft':
      case 'PageUp':
        prevImage();
        break;
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        nextImage();
        break;
      case 'r':
      case 'R':
        rotateClockwise();
        break;
      case 'h':
      case 'H':
        toggleFlipH();
        break;
      case 'v':
      case 'V':
        toggleFlipV();
        break;
      case '1':
        setZoomLevel(1.0);
        setPanOffset({ x: 0, y: 0 });
        break;
      case '0':
        resetTransform();
        break;
      case 'i':
      case 'I':
        setShowExifOverlay(prev => !prev);
        break;
      case 'e':
      case 'E':
        setViewMode('editor');
        break;
      case 'Escape':
        setViewMode('browser');
        break;
    }
  }, [prevImage, nextImage, rotateClockwise, toggleFlipH, toggleFlipV, setZoomLevel, setPanOffset, resetTransform, setViewMode]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (!activeFile) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-xn-bg text-xn-textMuted text-xs">
        <p>No image selected.</p>
        <button
          onClick={() => setViewMode('browser')}
          className="mt-2 px-3 py-1 bg-xn-accent text-white rounded"
        >
          Back to Browser
        </button>
      </div>
    );
  }

  const rawUrl = api.getRawImageUrl(activeFile.path);

  return (
    <div 
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      className="flex-1 relative overflow-hidden bg-black flex items-center justify-center select-none cursor-grab active:cursor-grabbing"
    >
      {/* Centered Image with Transform Matrix */}
      <div 
        className="transition-transform duration-75 origin-center pointer-events-none"
        style={{
          transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel}) rotate(${rotation}deg) scaleX(${flipH ? -1 : 1}) scaleY(${flipV ? -1 : 1})`,
        }}
      >
        <img
          src={rawUrl}
          alt={activeFile.name}
          className="max-w-[95vw] max-h-[85vh] object-contain shadow-2xl"
          draggable={false}
        />
      </div>

      {/* Top Left Navigation Back */}
      <div className="absolute top-3 left-3 flex items-center space-x-2 z-10">
        <button
          onClick={() => setViewMode('browser')}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-black/60 hover:bg-black/90 backdrop-blur border border-white/10 rounded text-xs text-white shadow-lg transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Browser (Esc)</span>
        </button>
        <span className="text-xs text-white/80 font-mono bg-black/50 px-2.5 py-1.5 rounded backdrop-blur border border-white/10">
          {activeFile.name}
        </span>
      </div>

      {/* Next / Prev Side Chevrons */}
      <button
        onClick={(e) => { e.stopPropagation(); prevImage(); }}
        title="Previous Image (Left Arrow)"
        className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/50 hover:bg-black/80 text-white/70 hover:text-white border border-white/10 backdrop-blur shadow-xl transition"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>

      <button
        onClick={(e) => { e.stopPropagation(); nextImage(); }}
        title="Next Image (Right Arrow / Space)"
        className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-black/50 hover:bg-black/80 text-white/70 hover:text-white border border-white/10 backdrop-blur shadow-xl transition"
      >
        <ChevronRight className="w-5 h-5" />
      </button>

      {/* Floating HUD Controls at Bottom */}
      <div className="absolute bottom-4 inset-x-0 flex justify-center z-10 pointer-events-none">
        <div className="flex items-center space-x-1 bg-black/75 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/15 shadow-2xl pointer-events-auto text-white text-xs">
          <button
            onClick={() => setZoomLevel(zoomLevel * 0.8)}
            title="Zoom Out (-)"
            className="p-1.5 rounded hover:bg-white/20 transition"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>

          <span className="font-mono text-xs w-12 text-center text-blue-400 font-semibold">
            {Math.round(zoomLevel * 100)}%
          </span>

          <button
            onClick={() => setZoomLevel(zoomLevel * 1.25)}
            title="Zoom In (+)"
            className="p-1.5 rounded hover:bg-white/20 transition"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          <div className="w-px h-4 bg-white/20 mx-1" />

          <button
            onClick={() => { setZoomLevel(1.0); setPanOffset({ x: 0, y: 0 }); }}
            title="1:1 Actual Size (1)"
            className="px-2 py-1 rounded hover:bg-white/20 text-[11px] font-mono transition"
          >
            1:1
          </button>

          <button
            onClick={resetTransform}
            title="Fit to Window (0)"
            className="p-1.5 rounded hover:bg-white/20 transition"
          >
            <Maximize className="w-3.5 h-3.5" />
          </button>

          <div className="w-px h-4 bg-white/20 mx-1" />

          <button
            onClick={rotateClockwise}
            title="Rotate 90° Clockwise (R)"
            className="p-1.5 rounded hover:bg-white/20 transition"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFlipH}
            title="Flip Horizontal (H)"
            className={`p-1.5 rounded transition ${flipH ? 'bg-blue-600' : 'hover:bg-white/20'}`}
          >
            <FlipHorizontal className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFlipV}
            title="Flip Vertical (V)"
            className={`p-1.5 rounded transition ${flipV ? 'bg-blue-600' : 'hover:bg-white/20'}`}
          >
            <FlipVertical className="w-3.5 h-3.5" />
          </button>

          <div className="w-px h-4 bg-white/20 mx-1" />

          <button
            onClick={() => setShowExifOverlay(prev => !prev)}
            title="Toggle EXIF Info Overlay (I)"
            className={`p-1.5 rounded transition ${showExifOverlay ? 'bg-blue-600' : 'hover:bg-white/20'}`}
          >
            <Info className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setViewMode('editor')}
            title="Open in Image Editor (E)"
            className="p-1.5 rounded hover:bg-white/20 transition text-amber-300"
          >
            <Sliders className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setViewMode('recovery')}
            title="Inspect & Recover Corrupted JPEG"
            className="p-1.5 rounded hover:bg-white/20 transition text-red-400"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* EXIF Heads-Up Display Overlay */}
      {showExifOverlay && exifData && (
        <div className="absolute top-14 left-4 bg-black/85 backdrop-blur-md border border-white/15 p-3 rounded-lg text-white text-xs max-w-sm z-20 shadow-2xl pointer-events-auto">
          <div className="flex items-center justify-between border-b border-white/20 pb-1.5 mb-2">
            <span className="font-semibold text-blue-400 uppercase tracking-wide text-[10px]">
              EXIF Information
            </span>
            <button 
              onClick={() => setShowExifOverlay(false)} 
              className="text-white/60 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
            <span className="text-white/60">Camera:</span>
            <span className="font-medium truncate">{exifData.camera_make} {exifData.camera_model}</span>

            <span className="text-white/60">Lens:</span>
            <span className="font-medium truncate">{exifData.lens_model}</span>

            <span className="text-white/60">Exposure:</span>
            <span className="font-medium">{exifData.exposure_time}s</span>

            <span className="text-white/60">Aperture:</span>
            <span className="font-medium">f/{exifData.f_number}</span>

            <span className="text-white/60">ISO:</span>
            <span className="font-medium">{exifData.iso_speed}</span>

            <span className="text-white/60">Focal Length:</span>
            <span className="font-medium">{exifData.focal_length}mm</span>

            <span className="text-white/60">Date Taken:</span>
            <span className="font-medium truncate">{exifData.date_taken}</span>
          </div>
        </div>
      )}
    </div>
  );
};
