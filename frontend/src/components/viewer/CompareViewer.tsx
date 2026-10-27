import React, { useState, useEffect } from 'react';
import { Columns2, ArrowLeft, ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { FileItem, ExifData } from '../../types';

export const CompareViewer: React.FC = () => {
  const { 
    directoryContent, 
    activeFile, 
    selectedFiles, 
    setViewMode 
  } = useAppStore();

  const files = directoryContent?.files || [];

  // Comparison items: default to selected files or first 2 files in directory
  const [leftFile, setLeftFile] = useState<FileItem | null>(
    selectedFiles[0] || activeFile || files[0] || null
  );
  const [rightFile, setRightFile] = useState<FileItem | null>(
    selectedFiles[1] || files.find(f => f.path !== (leftFile?.path)) || files[1] || null
  );

  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const [leftExif, setLeftExif] = useState<ExifData | null>(null);
  const [rightExif, setRightExif] = useState<ExifData | null>(null);

  useEffect(() => {
    if (leftFile) api.getMetadata(leftFile.path).then(setLeftExif).catch(() => setLeftExif(null));
  }, [leftFile]);

  useEffect(() => {
    if (rightFile) api.getMetadata(rightFile.path).then(setRightExif).catch(() => setRightExif(null));
  }, [rightFile]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.85;
    setZoom(prev => Math.max(0.2, Math.min(10, prev * factor)));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="flex-1 flex flex-col bg-xn-bg overflow-hidden select-none">
      {/* Compare Top Toolbar */}
      <div className="h-10 bg-xn-panel border-b border-xn-border flex items-center justify-between px-3 text-xs z-10">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('browser')}
            className="flex items-center space-x-1.5 px-2.5 py-1 bg-xn-surface hover:bg-xn-hover border border-xn-border rounded text-xn-textBright transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Browser</span>
          </button>
          <span className="font-semibold text-xn-textBright flex items-center space-x-1.5">
            <Columns2 className="w-4 h-4 text-blue-400" />
            <span>Synchronized Side-by-Side Comparison</span>
          </span>
        </div>

        {/* Global Zoom Sync Controls */}
        <div className="flex items-center space-x-1.5 bg-xn-surface px-2.5 py-1 rounded border border-xn-border">
          <button 
            onClick={() => setZoom(prev => Math.max(0.2, prev * 0.8))} 
            className="p-1 hover:bg-xn-hover rounded"
          >
            <ZoomOut className="w-3.5 h-3.5 text-xn-text" />
          </button>
          <span className="font-mono text-xs w-12 text-center text-blue-400 font-semibold">
            {Math.round(zoom * 100)}%
          </span>
          <button 
            onClick={() => setZoom(prev => Math.min(10, prev * 1.25))} 
            className="p-1 hover:bg-xn-hover rounded"
          >
            <ZoomIn className="w-3.5 h-3.5 text-xn-text" />
          </button>
          <button 
            onClick={() => { setZoom(1.0); setPan({ x: 0, y: 0 }); }} 
            title="Reset Pan & Zoom" 
            className="p-1 hover:bg-xn-hover rounded ml-1"
          >
            <Maximize className="w-3.5 h-3.5 text-xn-text" />
          </button>
        </div>
      </div>

      {/* Main Dual Viewer Split */}
      <div 
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="flex-1 grid grid-cols-2 divide-x divide-xn-border bg-black relative overflow-hidden cursor-grab active:cursor-grabbing"
      >
        {/* Left View */}
        <div className="relative flex flex-col items-center justify-center overflow-hidden">
          {/* File Picker Header */}
          <div className="absolute top-2 left-2 z-10 bg-black/70 backdrop-blur border border-white/10 rounded px-2 py-1 flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold text-blue-400">Image A:</span>
            <select
              value={leftFile?.path || ''}
              onChange={(e) => {
                const found = files.find(f => f.path === e.target.value);
                if (found) setLeftFile(found);
              }}
              className="bg-transparent text-white text-xs outline-none cursor-pointer max-w-xs truncate"
            >
              {files.map(f => (
                <option key={f.path} value={f.path} className="bg-xn-surface text-white">
                  {f.name}
                </option>
              ))}
            </select>
          </div>

          {/* Left Canvas */}
          {leftFile && (
            <div 
              className="transition-transform duration-75 origin-center pointer-events-none"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              }}
            >
              <img
                src={api.getRawImageUrl(leftFile.path)}
                alt={leftFile.name}
                className="max-w-[45vw] max-h-[70vh] object-contain shadow-2xl"
                draggable={false}
              />
            </div>
          )}
        </div>

        {/* Right View */}
        <div className="relative flex flex-col items-center justify-center overflow-hidden">
          {/* File Picker Header */}
          <div className="absolute top-2 left-2 z-10 bg-black/70 backdrop-blur border border-white/10 rounded px-2 py-1 flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold text-amber-400">Image B:</span>
            <select
              value={rightFile?.path || ''}
              onChange={(e) => {
                const found = files.find(f => f.path === e.target.value);
                if (found) setRightFile(found);
              }}
              className="bg-transparent text-white text-xs outline-none cursor-pointer max-w-xs truncate"
            >
              {files.map(f => (
                <option key={f.path} value={f.path} className="bg-xn-surface text-white">
                  {f.name}
                </option>
              ))}
            </select>
          </div>

          {/* Right Canvas */}
          {rightFile && (
            <div 
              className="transition-transform duration-75 origin-center pointer-events-none"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              }}
            >
              <img
                src={api.getRawImageUrl(rightFile.path)}
                alt={rightFile.name}
                className="max-w-[45vw] max-h-[70vh] object-contain shadow-2xl"
                draggable={false}
              />
            </div>
          )}
        </div>
      </div>

      {/* Side-by-Side Metadata Comparison Table at Bottom */}
      <div className="h-32 bg-xn-panel border-t border-xn-border p-2.5 overflow-y-auto text-xs grid grid-cols-2 divide-x divide-xn-border">
        {/* Left Specs */}
        <div className="pr-4 space-y-1">
          <div className="font-semibold text-blue-400 text-[11px] truncate">{leftFile?.name}</div>
          <div className="grid grid-cols-2 gap-y-0.5 text-[11px]">
            <span className="text-xn-textMuted">Dimensions:</span>
            <span className="text-xn-textBright">{leftFile?.width} × {leftFile?.height} px</span>
            <span className="text-xn-textMuted">File Size:</span>
            <span className="text-xn-textBright">{leftFile ? (leftFile.size / 1024).toFixed(1) : 0} KB</span>
            <span className="text-xn-textMuted">Camera:</span>
            <span className="text-xn-textBright truncate">{leftExif?.camera_make} {leftExif?.camera_model}</span>
            <span className="text-xn-textMuted">Exposure:</span>
            <span className="text-xn-textBright">{leftExif?.exposure_time}s, f/{leftExif?.f_number}, ISO {leftExif?.iso_speed}</span>
          </div>
        </div>

        {/* Right Specs */}
        <div className="pl-4 space-y-1">
          <div className="font-semibold text-amber-400 text-[11px] truncate">{rightFile?.name}</div>
          <div className="grid grid-cols-2 gap-y-0.5 text-[11px]">
            <span className="text-xn-textMuted">Dimensions:</span>
            <span className="text-xn-textBright">{rightFile?.width} × {rightFile?.height} px</span>
            <span className="text-xn-textMuted">File Size:</span>
            <span className="text-xn-textBright">{rightFile ? (rightFile.size / 1024).toFixed(1) : 0} KB</span>
            <span className="text-xn-textMuted">Camera:</span>
            <span className="text-xn-textBright truncate">{rightExif?.camera_make} {rightExif?.camera_model}</span>
            <span className="text-xn-textMuted">Exposure:</span>
            <span className="text-xn-textBright">{rightExif?.exposure_time}s, f/{rightExif?.f_number}, ISO {rightExif?.iso_speed}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
