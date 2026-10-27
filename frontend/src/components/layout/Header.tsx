import React, { useState } from 'react';
import { 
  Images, 
  Eye, 
  Columns2, 
  Sliders, 
  ShieldAlert, 
  Layers, 
  CopyCheck, 
  Camera, 
  Play, 
  Maximize2
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { ViewMode } from '../../types';
import { api } from '../../api/client';

export const Header: React.FC = () => {
  const { 
    viewMode, 
    setViewMode, 
    currentPath, 
    loadDirectory, 
    startSlideshow 
  } = useAppStore();
  const [isCapturing, setIsCapturing] = useState(false);

  const navItems: { mode: ViewMode; label: string; icon: React.ReactNode }[] = [
    { mode: 'browser', label: 'Browser', icon: <Images className="w-4 h-4" /> },
    { mode: 'viewer', label: 'Viewer', icon: <Eye className="w-4 h-4" /> },
    { mode: 'compare', label: 'Compare', icon: <Columns2 className="w-4 h-4" /> },
    { mode: 'editor', label: 'Editor', icon: <Sliders className="w-4 h-4" /> },
    { mode: 'recovery', label: 'JPEG Recovery', icon: <ShieldAlert className="w-4 h-4" /> },
    { mode: 'batch', label: 'Batch Studio', icon: <Layers className="w-4 h-4" /> },
    { mode: 'duplicates', label: 'Duplicates', icon: <CopyCheck className="w-4 h-4" /> },
  ];

  const handleScreenshot = async () => {
    setIsCapturing(true);
    try {
      const res = await api.captureScreenshot(currentPath);
      if (res.success && currentPath) {
        await loadDirectory(currentPath);
      }
    } catch (e) {
      console.error('Screenshot failed', e);
    } finally {
      setIsCapturing(false);
    }
  };

  const handleToggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  return (
    <header className="h-11 bg-xn-surface border-b border-xn-border flex items-center justify-between px-3 text-xs select-none z-30">
      {/* Brand & App Title */}
      <div className="flex items-center space-x-2.5">
        <div className="w-6 h-6 rounded bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold text-xs shadow-sm shadow-blue-500/20">
          PR
        </div>
        <div className="flex flex-col">
          <span className="font-semibold text-xn-textBright tracking-wide text-xs">
            Photorecover
          </span>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <nav className="flex items-center bg-xn-bg/70 p-0.5 rounded-md border border-xn-border">
        {navItems.map((item) => {
          const isActive = viewMode === item.mode;
          return (
            <button
              key={item.mode}
              onClick={() => setViewMode(item.mode)}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded transition-all text-xs font-medium ${
                isActive
                  ? 'bg-xn-accent text-white shadow-sm'
                  : 'text-xn-text hover:text-xn-textBright hover:bg-xn-hover'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Quick Utility Actions */}
      <div className="flex items-center space-x-1.5">
        <button
          onClick={handleScreenshot}
          disabled={isCapturing}
          title="Capture Desktop Screenshot"
          className="flex items-center space-x-1 px-2.5 py-1 bg-xn-hover hover:bg-xn-active border border-xn-border rounded text-xn-textBright text-xs transition"
        >
          <Camera className={`w-3.5 h-3.5 ${isCapturing ? 'animate-pulse text-blue-400' : ''}`} />
          <span>{isCapturing ? 'Capturing...' : 'Screenshot'}</span>
        </button>

        <button
          onClick={startSlideshow}
          title="Start Slideshow (Space to pause, ESC to exit)"
          className="p-1.5 bg-xn-hover hover:bg-xn-active border border-xn-border rounded text-xn-text hover:text-xn-textBright transition"
        >
          <Play className="w-3.5 h-3.5 text-green-400" />
        </button>

        <button
          onClick={handleToggleFullscreen}
          title="Toggle Fullscreen"
          className="p-1.5 bg-xn-hover hover:bg-xn-active border border-xn-border rounded text-xn-text hover:text-xn-textBright transition"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
