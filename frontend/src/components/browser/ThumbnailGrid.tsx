import React, { useMemo } from 'react';
import { Star, ShieldAlert, Sliders, Columns2, Eye, Layers } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { FileItem } from '../../types';

export const ThumbnailGrid: React.FC = () => {
  const {
    directoryContent,
    isLoadingDirectory,
    directoryError,
    activeFile,
    setActiveFile,
    selectedFiles,
    setSelectedFiles,
    toggleSelectFile,
    thumbnailSize,
    sortField,
    sortOrder,
    filterRating,
    filterColor,
    filterQuery,
    setViewMode
  } = useAppStore();

  // Filter & Sort
  const filteredFiles = useMemo(() => {
    if (!directoryContent?.files) return [];
    let list = [...directoryContent.files];

    // Search query
    if (filterQuery.trim()) {
      const q = filterQuery.toLowerCase();
      list = list.filter(f => f.name.toLowerCase().includes(q));
    }

    // Rating filter
    if (filterRating > 0) {
      list = list.filter(f => (f.rating || 0) >= filterRating);
    }

    // Color filter
    if (filterColor) {
      list = list.filter(f => (f.color_label || '').toLowerCase() === filterColor.toLowerCase());
    }

    // Sort
    list.sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];

      if (sortField === 'name') {
        valA = a.name.toLowerCase();
        valB = b.name.toLowerCase();
      } else if (sortField === 'mtime' || sortField === 'size' || sortField === 'rating') {
        valA = Number(valA || 0);
        valB = Number(valB || 0);
      } else if (sortField === 'ext') {
        valA = a.ext.toLowerCase();
        valB = b.ext.toLowerCase();
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return list;
  }, [directoryContent, sortField, sortOrder, filterRating, filterColor, filterQuery]);

  const handleRatingClick = async (e: React.MouseEvent, file: FileItem, rating: number) => {
    e.stopPropagation();
    const newRating = file.rating === rating ? 0 : rating;
    await api.updateAnnotations({ filepath: file.path, rating: newRating });
    file.rating = newRating;
    setActiveFile({ ...file });
  };

  const handleCardClick = (e: React.MouseEvent, file: FileItem) => {
    if (e.ctrlKey || e.metaKey) {
      toggleSelectFile(file, true);
    } else if (e.shiftKey && selectedFiles.length > 0) {
      // Range select
      const lastSelected = selectedFiles[selectedFiles.length - 1];
      const startIdx = filteredFiles.findIndex(f => f.path === lastSelected.path);
      const endIdx = filteredFiles.findIndex(f => f.path === file.path);
      if (startIdx !== -1 && endIdx !== -1) {
        const min = Math.min(startIdx, endIdx);
        const max = Math.max(startIdx, endIdx);
        const range = filteredFiles.slice(min, max + 1);
        setSelectedFiles(range);
        setActiveFile(file);
      }
    } else {
      toggleSelectFile(file, false);
    }
  };

  const handleDoubleClick = (file: FileItem) => {
    setActiveFile(file);
    setViewMode('viewer');
  };

  if (isLoadingDirectory) {
    return (
      <div className="flex-1 flex items-center justify-center bg-xn-bg text-xn-text text-xs space-x-2">
        <div className="w-4 h-4 border-2 border-xn-accent border-t-transparent rounded-full animate-spin" />
        <span>Loading folder items...</span>
      </div>
    );
  }

  if (directoryError) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-xn-bg p-6 text-center">
        <div className="text-red-400 font-semibold mb-2">Error accessing directory</div>
        <div className="text-xs text-xn-textMuted max-w-md">{directoryError}</div>
      </div>
    );
  }

  if (filteredFiles.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-xn-bg p-6 text-center text-xn-textMuted text-xs">
        <div className="w-12 h-12 rounded-full bg-xn-surface flex items-center justify-center mb-3">
          📁
        </div>
        <p className="font-medium text-xn-textBright">No images in this folder</p>
        <p className="text-[11px] mt-1">Select a folder with JPG, PNG, WEBP, GIF, BMP, or TIFF images from the sidebar.</p>
      </div>
    );
  }

  return (
    <div 
      className="flex-1 overflow-y-auto p-3 bg-xn-bg select-none"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(${thumbnailSize}px, 1fr))`,
        gap: '10px',
        alignContent: 'start'
      }}
    >
      {filteredFiles.map((file) => {
        const isSelected = selectedFiles.some(f => f.path === file.path);
        const isActive = activeFile?.path === file.path;

        return (
          <div
            key={file.path}
            onClick={(e) => handleCardClick(e, file)}
            onDoubleClick={() => handleDoubleClick(file)}
            className={`group flex flex-col rounded-md border p-1 transition-all cursor-pointer relative bg-xn-surface ${
              isActive 
                ? 'border-xn-accent ring-1 ring-xn-accent bg-xn-hover shadow-md' 
                : isSelected 
                  ? 'border-xn-accent/60 bg-xn-hover/60' 
                  : 'border-xn-border/60 hover:border-xn-accent/40 hover:bg-xn-hover/40'
            }`}
          >
            {/* Thumbnail Canvas / Container */}
            <div 
              className="relative w-full rounded overflow-hidden flex items-center justify-center bg-black/40 checkerboard-pattern"
              style={{ height: `${thumbnailSize * 0.75}px` }}
            >
              <img
                src={api.getThumbnailUrl(file.path, thumbnailSize)}
                alt={file.name}
                loading="lazy"
                className="max-w-full max-h-full object-contain transition-transform duration-200 group-hover:scale-105"
              />

              {/* Color Label indicator top-left */}
              {file.color_label && (
                <div 
                  className="absolute top-1 left-1 w-2.5 h-2.5 rounded-full ring-1 ring-black shadow"
                  style={{ backgroundColor: file.color_label }}
                />
              )}

              {/* Quick Action Badges on Hover */}
              <div className="absolute inset-x-0 bottom-0 p-1 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-between text-white text-[10px]">
                <div className="flex items-center space-x-1">
                  <button 
                    onClick={(e) => { e.stopPropagation(); setActiveFile(file); setViewMode('viewer'); }}
                    title="Open Viewer" 
                    className="p-1 hover:bg-white/20 rounded"
                  >
                    <Eye className="w-3 h-3" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setActiveFile(file); setViewMode('editor'); }}
                    title="Edit Image" 
                    className="p-1 hover:bg-white/20 rounded"
                  >
                    <Sliders className="w-3 h-3" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setActiveFile(file); setViewMode('recovery'); }}
                    title="Inspect & Recover Corrupted JPEG" 
                    className="p-1 hover:bg-white/20 rounded text-amber-300"
                  >
                    <ShieldAlert className="w-3 h-3" />
                  </button>
                </div>
                <span className="font-mono text-[9px] uppercase tracking-wide bg-black/40 px-1 rounded">
                  {file.ext}
                </span>
              </div>
            </div>

            {/* File Info Bar */}
            <div className="mt-1 px-1 flex flex-col min-w-0">
              <span className="truncate text-xs font-medium text-xn-textBright" title={file.name}>
                {file.name}
              </span>

              <div className="flex items-center justify-between mt-0.5 text-[10px] text-xn-textMuted">
                <span>
                  {file.width && file.height ? `${file.width}×${file.height}` : file.ext.toUpperCase()}
                </span>
                <span>
                  {(file.size / 1024).toFixed(0)} KB
                </span>
              </div>

              {/* Rating Stars */}
              <div className="flex items-center space-x-0.5 mt-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={(e) => handleRatingClick(e, file, star)}
                    className="hover:scale-125 transition"
                  >
                    <Star
                      className={`w-2.5 h-2.5 ${
                        (file.rating || 0) >= star
                          ? 'text-yellow-400 fill-yellow-400'
                          : 'text-xn-textMuted/40 hover:text-yellow-300'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
