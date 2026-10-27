import React, { useState } from 'react';
import { 
  Layers, 
  ArrowLeft, 
  Play, 
  XCircle, 
  CheckCircle2, 
  AlertCircle, 
  FolderOutput, 
  Sliders, 
  Trash2,
  Plus
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { BatchStatus } from '../../types';

export const BatchStudio: React.FC = () => {
  const { 
    directoryContent, 
    selectedFiles, 
    currentPath, 
    loadDirectory, 
    setViewMode 
  } = useAppStore();

  const allFiles = directoryContent?.files || [];
  
  // File Queue: Default to selected files, or all files if none selected
  const [queue, setQueue] = useState<string[]>(
    selectedFiles.length > 0 
      ? selectedFiles.map(f => f.path) 
      : allFiles.map(f => f.path)
  );

  // Conversion Options
  const [targetFormat, setTargetFormat] = useState('webp');
  const [quality, setQuality] = useState(85);
  const [resizeMode, setResizeMode] = useState<string>('none'); // 'none', 'percent', 'dimensions'
  const [resizePercent, setResizePercent] = useState(80);
  const [resizeWidth, setResizeWidth] = useState(1920);
  const [resizeHeight, setResizeHeight] = useState(1080);
  const [filterName, setFilterName] = useState('none');
  const [watermarkText, setWatermarkText] = useState('');
  const [renamePattern, setRenamePattern] = useState('{name}_{width}x{height}');
  const [outputDir, setOutputDir] = useState(`${currentPath || 'C:\\'}\\converted`);

  // Job Execution State
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<BatchStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleStartBatch = async () => {
    if (queue.length === 0) return;
    setIsProcessing(true);
    try {
      const res = await api.startBatch({
        file_list: queue,
        output_dir: outputDir,
        target_format: targetFormat.toUpperCase(),
        output_quality: quality,
        resize_mode: resizeMode === 'none' ? undefined : resizeMode,
        resize_percent: resizePercent,
        resize_width: resizeMode === 'dimensions' ? resizeWidth : undefined,
        resize_height: resizeMode === 'dimensions' ? resizeHeight : undefined,
        rename_pattern: renamePattern.trim() || undefined,
        filter_name: filterName === 'none' ? undefined : filterName,
        watermark_text: watermarkText.trim() || undefined
      });

      setJobId(res.job_id);

      // Poll status
      const interval = setInterval(async () => {
        try {
          const status = await api.getBatchStatus(res.job_id);
          setJobStatus(status);
          if (status.status === 'completed' || status.status === 'cancelled') {
            clearInterval(interval);
            setIsProcessing(false);
            if (currentPath) loadDirectory(currentPath);
          }
        } catch {
          clearInterval(interval);
          setIsProcessing(false);
        }
      }, 500);

    } catch (e: any) {
      alert('Failed to start batch: ' + e.message);
      setIsProcessing(false);
    }
  };

  const handleCancelBatch = async () => {
    if (jobId) {
      await api.cancelBatch(jobId);
    }
  };

  const handleRemoveFromQueue = (path: string) => {
    setQueue(q => q.filter(p => p !== path));
  };

  const handleAddAll = () => {
    setQueue(allFiles.map(f => f.path));
  };

  const progressPercent = jobStatus 
    ? Math.round(((jobStatus.completed + jobStatus.failed) / Math.max(1, jobStatus.total)) * 100)
    : 0;

  return (
    <div className="flex-1 flex flex-col bg-xn-bg overflow-hidden select-none">
      {/* Batch Header */}
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
            <Layers className="w-4 h-4 text-blue-400" />
            <span>Batch Image Processing & Format Converter Studio</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {isProcessing ? (
            <button
              onClick={handleCancelBatch}
              className="flex items-center space-x-1.5 px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded font-medium transition shadow"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Cancel Batch</span>
            </button>
          ) : (
            <button
              onClick={handleStartBatch}
              disabled={queue.length === 0}
              className="flex items-center space-x-1.5 px-3 py-1 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded font-medium transition shadow"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Start Batch Processing ({queue.length} files)</span>
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        {/* Left 4 Cols: Queue Management */}
        <div className="col-span-4 bg-xn-surface border-r border-xn-border flex flex-col h-full overflow-hidden text-xs">
          <div className="p-2.5 border-b border-xn-border flex items-center justify-between">
            <span className="font-semibold text-xn-textBright uppercase tracking-wide text-[10px]">
              Processing Queue ({queue.length})
            </span>
            <div className="flex items-center space-x-1">
              <button
                onClick={handleAddAll}
                className="px-2 py-0.5 rounded bg-xn-panel hover:bg-xn-hover text-xn-text hover:text-white text-[10px]"
              >
                Add All ({allFiles.length})
              </button>
              <button
                onClick={() => setQueue([])}
                className="px-2 py-0.5 rounded bg-xn-panel hover:bg-xn-hover text-red-400 text-[10px]"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {queue.map((path) => {
              const name = path.split(/[/\\]/).pop() || path;
              return (
                <div
                  key={path}
                  className="flex items-center justify-between p-1.5 rounded bg-xn-panel hover:bg-xn-hover border border-xn-border/60 group text-xn-text text-[11px]"
                >
                  <span className="truncate flex-1 font-mono">{name}</span>
                  <button
                    onClick={() => handleRemoveFromQueue(path)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 text-red-400 hover:text-red-300 ml-2"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 8 Cols: Batch Settings & Execution Dashboard */}
        <div className="col-span-8 bg-xn-bg flex flex-col h-full overflow-y-auto p-4 space-y-4 text-xs">
          {/* Progress Banner (when active or finished) */}
          {jobStatus && (
            <div className="bg-xn-surface border border-xn-border rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xn-textBright">
                  Status: <span className="uppercase text-blue-400">{jobStatus.status}</span>
                </span>
                <span className="font-mono text-xn-accent font-bold">
                  {jobStatus.completed} / {jobStatus.total} ({progressPercent}%)
                </span>
              </div>
              <div className="w-full bg-xn-panel h-2.5 rounded-full overflow-hidden border border-xn-border">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-green-500 transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}

          {/* Configuration Card */}
          <div className="bg-xn-surface border border-xn-border rounded-lg p-3.5 space-y-3.5">
            <span className="font-semibold text-xn-textBright text-xs uppercase tracking-wide block border-b border-xn-border pb-1.5">
              Conversion & Transformation Parameters
            </span>

            <div className="grid grid-cols-2 gap-4">
              {/* Target Format */}
              <div className="space-y-1">
                <label className="text-xn-textMuted font-medium text-[11px]">Output Format:</label>
                <select
                  value={targetFormat}
                  onChange={(e) => setTargetFormat(e.target.value)}
                  className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
                >
                  <option value="webp">WebP (Modern, High Compression)</option>
                  <option value="jpg">JPEG (Standard Photo)</option>
                  <option value="png">PNG (Lossless with Alpha)</option>
                  <option value="tiff">TIFF (Professional Master)</option>
                  <option value="bmp">BMP (Uncompressed)</option>
                  <option value="gif">GIF</option>
                </select>
              </div>

              {/* Quality Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xn-textMuted text-[11px]">
                  <span>Compression Quality</span>
                  <span className="font-mono text-xn-textBright">{quality}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="100"
                  value={quality}
                  onChange={(e) => setQuality(parseInt(e.target.value))}
                  className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                />
              </div>

              {/* Resize Mode */}
              <div className="space-y-1">
                <label className="text-xn-textMuted font-medium text-[11px]">Geometry Resize:</label>
                <select
                  value={resizeMode}
                  onChange={(e) => setResizeMode(e.target.value)}
                  className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
                >
                  <option value="none">Original Dimensions (No Resize)</option>
                  <option value="percent">Percentage Scale</option>
                  <option value="dimensions">Custom Width × Height</option>
                </select>
              </div>

              {/* Dynamic Resize Fields */}
              {resizeMode === 'percent' ? (
                <div className="space-y-1">
                  <div className="flex justify-between text-xn-textMuted text-[11px]">
                    <span>Scale Percentage</span>
                    <span className="font-mono text-xn-textBright">{resizePercent}%</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="200"
                    step="5"
                    value={resizePercent}
                    onChange={(e) => setResizePercent(parseInt(e.target.value))}
                    className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                  />
                </div>
              ) : resizeMode === 'dimensions' ? (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-xn-textMuted">Width</label>
                    <input
                      type="number"
                      value={resizeWidth}
                      onChange={(e) => setResizeWidth(parseInt(e.target.value) || 0)}
                      className="w-full bg-xn-bg border border-xn-border rounded px-2 py-0.5 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-xn-textMuted">Height</label>
                    <input
                      type="number"
                      value={resizeHeight}
                      onChange={(e) => setResizeHeight(parseInt(e.target.value) || 0)}
                      className="w-full bg-xn-bg border border-xn-border rounded px-2 py-0.5 text-xs text-white"
                    />
                  </div>
                </div>
              ) : (
                <div />
              )}

              {/* Filters */}
              <div className="space-y-1">
                <label className="text-xn-textMuted font-medium text-[11px]">Apply Filter:</label>
                <select
                  value={filterName}
                  onChange={(e) => setFilterName(e.target.value)}
                  className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
                >
                  <option value="none">None</option>
                  <option value="grayscale">Grayscale</option>
                  <option value="sharpen">Sharpen</option>
                  <option value="sepia">Sepia</option>
                  <option value="noise_reduction">Noise Reduction</option>
                </select>
              </div>

              {/* Watermark */}
              <div className="space-y-1">
                <label className="text-xn-textMuted font-medium text-[11px]">Batch Watermark Text:</label>
                <input
                  type="text"
                  placeholder="Optional overlay text"
                  value={watermarkText}
                  onChange={(e) => setWatermarkText(e.target.value)}
                  className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 text-xs text-xn-textBright outline-none"
                />
              </div>
            </div>

            {/* Renaming Pattern Engine */}
            <div className="pt-2 border-t border-xn-border space-y-1.5">
              <label className="text-xn-textMuted font-medium text-[11px]">File Renaming Pattern Template:</label>
              <input
                type="text"
                value={renamePattern}
                onChange={(e) => setRenamePattern(e.target.value)}
                className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 font-mono text-xs text-blue-300 outline-none"
              />
              <div className="flex items-center justify-between text-[10px] text-xn-textMuted">
                <span>Tokens: <code className="text-xn-accent font-mono">{`{name}`}</code>, <code className="text-xn-accent font-mono">{`{index}`}</code>, <code className="text-xn-accent font-mono">{`{width}`}</code>, <code className="text-xn-accent font-mono">{`{height}`}</code>, <code className="text-xn-accent font-mono">{`{date}`}</code></span>
                <span>Example: <strong className="text-xn-textBright font-mono">photo_1920x1080.{targetFormat}</strong></span>
              </div>
            </div>

            {/* Destination Directory */}
            <div className="pt-2 border-t border-xn-border space-y-1">
              <label className="text-xn-textMuted font-medium text-[11px]">Destination Folder:</label>
              <input
                type="text"
                value={outputDir}
                onChange={(e) => setOutputDir(e.target.value)}
                className="w-full bg-xn-bg border border-xn-border rounded px-2.5 py-1 font-mono text-xs text-xn-textBright outline-none"
              />
            </div>
          </div>

          {/* Results Table */}
          {jobStatus && jobStatus.results.length > 0 && (
            <div className="bg-xn-surface border border-xn-border rounded-lg p-3 space-y-2">
              <span className="font-semibold text-xn-textBright text-xs uppercase tracking-wide">
                Processed Results Log ({jobStatus.results.length})
              </span>
              <div className="border border-xn-border rounded bg-xn-bg overflow-hidden max-h-48 overflow-y-auto">
                <table className="w-full text-[11px] text-left">
                  <thead className="bg-xn-panel text-xn-textMuted text-[10px] uppercase font-mono">
                    <tr>
                      <th className="p-1.5">File</th>
                      <th className="p-1.5">Status</th>
                      <th className="p-1.5 text-right">Size</th>
                      <th className="p-1.5">Output Path</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-xn-border/40 font-mono text-[10px]">
                    {jobStatus.results.map((res, i) => (
                      <tr key={i} className="hover:bg-xn-hover">
                        <td className="p-1.5 truncate max-w-xs">{res.original.split(/[/\\]/).pop()}</td>
                        <td className="p-1.5">
                          {res.status === 'success' ? (
                            <span className="text-green-400 font-bold">SUCCESS</span>
                          ) : (
                            <span className="text-red-400 font-bold">ERROR: {res.error}</span>
                          )}
                        </td>
                        <td className="p-1.5 text-right text-xn-textMuted">
                          {res.size ? `${(res.size / 1024).toFixed(1)} KB` : '-'}
                        </td>
                        <td className="p-1.5 truncate max-w-xs text-xn-textMuted">{res.output || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
