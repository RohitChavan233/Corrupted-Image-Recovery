import React, { useState, useEffect } from 'react';
import { Play, Pause, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';

export const Slideshow: React.FC = () => {
  const { 
    isSlideshowActive, 
    stopSlideshow, 
    activeFile, 
    nextImage, 
    prevImage,
    slideshowInterval 
  } = useAppStore();

  const [isPaused, setIsPaused] = useState(false);
  const [intervalSec, setIntervalSec] = useState(slideshowInterval);

  // Auto-advance timer
  useEffect(() => {
    if (!isSlideshowActive || isPaused) return;

    const timer = setInterval(() => {
      nextImage();
    }, intervalSec * 1000);

    return () => clearInterval(timer);
  }, [isSlideshowActive, isPaused, intervalSec, nextImage]);

  // Keyboard navigation during slideshow
  useEffect(() => {
    if (!isSlideshowActive) return;

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        stopSlideshow();
      } else if (e.key === ' ' || e.key === 'p' || e.key === 'P') {
        setIsPaused(prev => !prev);
      } else if (e.key === 'ArrowRight') {
        nextImage();
      } else if (e.key === 'ArrowLeft') {
        prevImage();
      }
    };

    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isSlideshowActive, stopSlideshow, nextImage, prevImage]);

  if (!isSlideshowActive || !activeFile) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black flex items-center justify-center select-none overflow-hidden group">
      {/* Centered Image */}
      <img
        src={api.getRawImageUrl(activeFile.path)}
        alt={activeFile.name}
        className="max-w-full max-h-full object-contain transition-all duration-500"
      />

      {/* Floating Controls Bar on Hover */}
      <div className="absolute bottom-6 inset-x-0 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex items-center space-x-3 bg-black/80 backdrop-blur-md px-4 py-2 rounded-full border border-white/20 shadow-2xl text-white text-xs">
          <button onClick={prevImage} className="p-1 hover:text-blue-400">
            <ChevronLeft className="w-4 h-4" />
          </button>

          <button onClick={() => setIsPaused(!isPaused)} className="p-1 hover:text-blue-400">
            {isPaused ? <Play className="w-4 h-4 fill-white" /> : <Pause className="w-4 h-4 fill-white" />}
          </button>

          <button onClick={nextImage} className="p-1 hover:text-blue-400">
            <ChevronRight className="w-4 h-4" />
          </button>

          <div className="w-px h-4 bg-white/20" />

          {/* Interval selector */}
          <select
            value={intervalSec}
            onChange={(e) => setIntervalSec(Number(e.target.value))}
            className="bg-transparent text-xs text-white outline-none cursor-pointer"
          >
            <option value={2} className="bg-xn-surface">2s</option>
            <option value={3} className="bg-xn-surface">3s</option>
            <option value={5} className="bg-xn-surface">5s</option>
            <option value={10} className="bg-xn-surface">10s</option>
          </select>

          <div className="w-px h-4 bg-white/20" />

          <button 
            onClick={stopSlideshow} 
            className="p-1 text-red-400 hover:text-red-300"
            title="Exit Slideshow (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
