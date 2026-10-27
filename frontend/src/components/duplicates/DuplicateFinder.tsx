import React, { useState } from 'react';
import { 
  CopyCheck, 
  ArrowLeft, 
  Play, 
  CheckCircle2, 
  Trash2, 
  Eye, 
  SlidersHorizontal 
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { DuplicateCluster } from '../../types';

export const DuplicateFinder: React.FC = () => {
  const { currentPath, setViewMode, setActiveFile } = useAppStore();

  const [threshold, setThreshold] = useState(0.90);
  const [clusters, setClusters] = useState<DuplicateCluster[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [hasScanned, setHasScanned] = useState(false);

  const handleScan = async () => {
    if (!currentPath) return;
    setIsScanning(true);
    setHasScanned(true);
    try {
      const res = await api.scanDuplicates(currentPath, threshold);
      setClusters(res.clusters || []);
    } catch (e: any) {
      alert('Duplicate scan failed: ' + e.message);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-xn-bg overflow-hidden select-none">
      {/* Header */}
      <div className="h-10 bg-xn-panel border-b border-xn-border flex items-center justify-between px-3 text-xs z-10">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('browser')}
            className="flex items-center space-x-1 px-2.5 py-1 bg-xn-surface hover:bg-xn-hover border border-xn-border rounded text-xn-textBright transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Browser</span>
          </button>
          <span className="font-semibold text-xn-textBright flex items-center space-x-1.5">
            <CopyCheck className="w-4 h-4 text-purple-400" />
            <span>Perceptual Duplicate & Exact Match Finder</span>
          </span>
        </div>

        {/* Scan & Threshold Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-xn-surface px-2.5 py-1 rounded border border-xn-border text-[11px]">
            <span className="text-xn-textMuted">Similarity Threshold:</span>
            <input
              type="range"
              min="0.75"
              max="1.0"
              step="0.01"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-24 accent-purple-500 h-1.5 bg-xn-panel rounded cursor-pointer"
            />
            <span className="font-mono text-purple-400 font-bold w-10 text-right">
              {Math.round(threshold * 100)}%
            </span>
          </div>

          <button
            onClick={handleScan}
            disabled={isScanning || !currentPath}
            className="flex items-center space-x-1.5 px-3 py-1 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded font-medium transition shadow"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>{isScanning ? 'Computing Hashes...' : 'Scan Folder'}</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isScanning ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-2 text-xs text-xn-text">
            <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <span>Computing perceptual dHash and SHA-256 for all images...</span>
          </div>
        ) : hasScanned && clusters.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center text-xn-textMuted text-xs">
            <CheckCircle2 className="w-8 h-8 text-green-400 mb-2" />
            <p className="font-semibold text-xn-textBright">No duplicates detected</p>
            <p className="text-[11px] mt-1">All images in this folder are visually distinct at {Math.round(threshold * 100)}% threshold.</p>
          </div>
        ) : !hasScanned ? (
          <div className="h-64 flex flex-col items-center justify-center text-center text-xn-textMuted text-xs">
            <CopyCheck className="w-10 h-10 text-purple-400/40 mb-3" />
            <p className="font-semibold text-xn-textBright">Scan Current Directory for Duplicate Photos</p>
            <p className="text-[11px] max-w-sm mt-1">
              Finds exact binary matches as well as visually similar images (different resolution, re-encoded, or slight crops) using Hamming distance perceptual hashing.
            </p>
            <button
              onClick={handleScan}
              className="mt-3 px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded font-medium shadow text-xs"
            >
              Start Duplicate Scan
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-xs font-semibold text-xn-textBright">
              Found {clusters.length} duplicate cluster{clusters.length === 1 ? '' : 's'}:
            </div>

            {clusters.map((cluster) => (
              <div 
                key={cluster.cluster_id} 
                className="bg-xn-surface border border-xn-border rounded-lg p-3 space-y-2.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-purple-300">
                    Cluster #{cluster.cluster_id} — {cluster.count} matching images
                  </span>
                  <span className="bg-purple-950/70 border border-purple-800 text-purple-300 text-[10px] font-mono px-2 py-0.5 rounded">
                    dHash Match
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  {cluster.items.map((item, idx) => (
                    <div 
                      key={item.filepath} 
                      className="bg-xn-panel border border-xn-border rounded p-2 flex flex-col space-y-1.5 text-xs"
                    >
                      <div className="h-28 bg-black/50 rounded overflow-hidden flex items-center justify-center checkerboard-pattern relative group">
                        <img
                          src={api.getThumbnailUrl(item.filepath, 160)}
                          alt={item.filename}
                          className="max-h-full max-w-full object-contain"
                        />
                        <button
                          onClick={() => {
                            setActiveFile({
                              name: item.filename,
                              path: item.filepath,
                              size: item.size,
                              mtime: Date.now(),
                              ext: item.filename.split('.').pop() || '',
                              is_dir: false
                            });
                            setViewMode('viewer');
                          }}
                          className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs transition"
                        >
                          <Eye className="w-4 h-4 mr-1" /> View Full
                        </button>
                      </div>

                      <div className="truncate font-medium text-xn-textBright" title={item.filename}>
                        {item.filename}
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-xn-textMuted font-mono">
                        <span>{(item.size / 1024).toFixed(1)} KB</span>
                        {item.similarity ? (
                          <span className="text-green-400 font-bold">{item.similarity}% match</span>
                        ) : (
                          <span className="text-blue-400">Reference</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
