import React from 'react';
import { useAppStore } from '../../store/useAppStore';

function formatBytes(bytes: number, decimals = 1) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export const StatusBar: React.FC = () => {
  const { 
    directoryContent, 
    selectedFiles, 
    activeFile, 
    zoomLevel, 
    viewMode,
    isLoadingDirectory 
  } = useAppStore();

  const totalFiles = directoryContent?.total_files || 0;
  const selectedCount = selectedFiles.length;

  return (
    <footer className="h-6 bg-xn-surface border-t border-xn-border flex items-center justify-between px-3 text-[11px] text-xn-text select-none z-20">
      {/* Left: Counts and Status */}
      <div className="flex items-center space-x-3">
        <span className="flex items-center space-x-1.5">
          <span className={`w-2 h-2 rounded-full ${isLoadingDirectory ? 'bg-yellow-400 animate-ping' : 'bg-green-500'}`} />
          <span className="text-xn-textBright font-medium">
            {isLoadingDirectory ? 'Scanning...' : 'Ready'}
          </span>
        </span>

        <span className="text-xn-border">|</span>

        <span>
          <strong className="text-xn-textBright">{totalFiles}</strong> image{totalFiles === 1 ? '' : 's'}
        </span>

        {selectedCount > 0 && (
          <span>
            (<strong className="text-xn-accent font-semibold">{selectedCount}</strong> selected)
          </span>
        )}
      </div>

      {/* Center/Right: Active File Dimensions, Size, Format, and Zoom */}
      <div className="flex items-center space-x-3">
        {activeFile && (
          <>
            <span className="truncate max-w-xs text-xn-textBright font-mono">
              {activeFile.name}
            </span>

            <span className="text-xn-border">|</span>

            {activeFile.width && activeFile.height ? (
              <span className="text-xn-textBright">
                {activeFile.width} × {activeFile.height} px
              </span>
            ) : (
              <span className="text-xn-textMuted">{activeFile.ext.toUpperCase()}</span>
            )}

            <span className="text-xn-border">|</span>

            <span className="text-xn-textBright">
              {formatBytes(activeFile.size)}
            </span>
          </>
        )}

        {viewMode === 'viewer' && (
          <>
            <span className="text-xn-border">|</span>
            <span className="font-mono text-xn-accent font-semibold">
              {Math.round(zoomLevel * 100)}%
            </span>
          </>
        )}
      </div>
    </footer>
  );
};
