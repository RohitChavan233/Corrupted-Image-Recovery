import React, { useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';

export const Filmstrip: React.FC = () => {
  const { 
    directoryContent, 
    activeFile, 
    setActiveFile, 
    prevImage, 
    nextImage,
    filmstripVisible 
  } = useAppStore();

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const files = directoryContent?.files || [];

  // Scroll active item into view
  useEffect(() => {
    if (activeFile && scrollContainerRef.current) {
      const activeEl = scrollContainerRef.current.querySelector(`[data-path="${CSS.escape(activeFile.path)}"]`);
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  }, [activeFile]);

  if (!filmstripVisible || files.length === 0) return null;

  return (
    <div className="h-16 bg-xn-surface border-t border-xn-border flex items-center px-2 select-none relative z-10 shrink-0">
      <button
        onClick={prevImage}
        title="Previous Image"
        className="p-1.5 rounded-full bg-xn-panel hover:bg-xn-hover border border-xn-border text-xn-text hover:text-white shrink-0 mr-1.5 shadow"
      >
        <ChevronLeft className="w-3.5 h-3.5" />
      </button>

      <div 
        ref={scrollContainerRef}
        className="flex-1 flex items-center space-x-1.5 overflow-x-auto py-1 scrollbar-none"
      >
        {files.map((file) => {
          const isActive = activeFile?.path === file.path;
          return (
            <div
              key={file.path}
              data-path={file.path}
              onClick={() => setActiveFile(file)}
              className={`h-13 w-16 shrink-0 rounded overflow-hidden cursor-pointer border transition-all relative checkerboard-pattern flex items-center justify-center ${
                isActive 
                  ? 'border-xn-accent ring-2 ring-xn-accent scale-105 shadow-md' 
                  : 'border-xn-border/70 hover:border-xn-accent/60 opacity-70 hover:opacity-100'
              }`}
            >
              <img
                src={api.getThumbnailUrl(file.path, 120)}
                alt={file.name}
                className="max-h-full max-w-full object-contain pointer-events-none"
              />
              {file.color_label && (
                <div 
                  className="absolute bottom-1 right-1 w-2 h-2 rounded-full"
                  style={{ backgroundColor: file.color_label }}
                />
              )}
            </div>
          );
        })}
      </div>

      <button
        onClick={nextImage}
        title="Next Image"
        className="p-1.5 rounded-full bg-xn-panel hover:bg-xn-hover border border-xn-border text-xn-text hover:text-white shrink-0 ml-1.5 shadow"
      >
        <ChevronRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
