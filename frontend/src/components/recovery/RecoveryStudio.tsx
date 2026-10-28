import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  ArrowLeft, 
  CheckCircle2, 
  AlertTriangle, 
  Download, 
  Layers, 
  Search, 
  Eye, 
  Sparkles,
  Info,
  FolderSearch,
  CheckSquare,
  Square,
  Play,
  RotateCw,
  FolderOpen
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { JpegAnalysis, RecoveryExecutionResult, BatchRecoveryScanResponse, BatchRecoveryExecuteResponse } from '../../types';

export const RecoveryStudio: React.FC = () => {
  const { activeFile, setActiveFile, setViewMode, currentPath, loadDirectory, directoryContent, selectedFiles } = useAppStore();

  // Mode: 'single' (Deep Inspector) or 'batch' (Multi-Photo Batch Recovery)
  const [studioMode, setStudioMode] = useState<'single' | 'batch'>('batch');

  // Single File State
  const [analysis, setAnalysis] = useState<JpegAnalysis | null>(null);
  const [isLoadingSingle, setIsLoadingSingle] = useState(false);
  const [singleRecoveryResult, setSingleRecoveryResult] = useState<RecoveryExecutionResult | null>(null);
  const [isRecoveringSingle, setIsRecoveringSingle] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);

  // Batch Multi-Photo State
  const [batchScanData, setBatchScanData] = useState<BatchRecoveryScanResponse | null>(null);
  const [isScanningBatch, setIsScanningBatch] = useState(false);
  const [selectedPaths, setSelectedPaths] = useState<string[]>([]);
  const [onlyCorruptedFilter, setOnlyCorruptedFilter] = useState(true);
  const [batchRecoveryType, setBatchRecoveryType] = useState('auto');
  const [isRecoveringBatch, setIsRecoveringBatch] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchRecoveryExecuteResponse | null>(null);
  const [suggestedDonors, setSuggestedDonors] = useState<Array<{ path: string; name: string; size: number; width: number; height: number; is_same_session: boolean }>>([]);
  const [selectedDonor, setSelectedDonor] = useState<string>('');

  // Load single inspection when activeFile changes
  useEffect(() => {
    if (activeFile && studioMode === 'single') {
      setIsLoadingSingle(true);
      setSingleError(null);
      setSingleRecoveryResult(null);
      setSuggestedDonors([]);
      setSelectedDonor('');

      api.inspectJpeg(activeFile.path)
        .then(setAnalysis)
        .catch(err => setSingleError(err.message || 'Inspection failed'))
        .finally(() => setIsLoadingSingle(false));

      api.suggestDonors(activeFile.path)
        .then(res => {
          setSuggestedDonors(res.donors || []);
          if (res.donors && res.donors.length > 0) {
            setSelectedDonor(res.donors[0].path);
          }
        })
        .catch(() => setSuggestedDonors([]));
    }
  }, [activeFile, studioMode]);

  // Execute single file recovery
  const handleExecuteSingleRecovery = async (recoveryType: string = 'auto') => {
    if (!activeFile) return;
    setIsRecoveringSingle(true);
    try {
      const res = await api.executeRecovery(activeFile.path, recoveryType, selectedDonor || undefined);
      setSingleRecoveryResult(res);
      if (currentPath) loadDirectory(currentPath);
    } catch (e: any) {
      alert('Recovery failed: ' + e.message);
    } finally {
      setIsRecoveringSingle(false);
    }
  };

  // Run Batch Scan across current folder or selected files
  const handleBatchScan = async () => {
    if (!currentPath) return;
    setIsScanningBatch(true);
    setBatchResult(null);
    try {
      // If user selected multiple files in the browser, scan those; otherwise scan the entire folder
      const fileList = selectedFiles.length > 1 ? selectedFiles.map(f => f.path) : undefined;
      const res = await api.batchScanCorrupted({
        folder_path: currentPath,
        file_list: fileList
      });
      setBatchScanData(res);
      // Automatically select all corrupted or recoverable files
      const toSelect = res.results.filter(r => r.is_corrupt || r.recoverable).map(r => r.filepath);
      setSelectedPaths(toSelect);
    } catch (e: any) {
      alert('Batch scan failed: ' + e.message);
    } finally {
      setIsScanningBatch(false);
    }
  };

  // Run Batch Recovery on selected files
  const handleBatchExecute = async () => {
    if (selectedPaths.length === 0) return;
    setIsRecoveringBatch(true);
    try {
      const res = await api.batchExecuteRecovery({
        file_list: selectedPaths,
        recovery_type: batchRecoveryType
      });
      setBatchResult(res);
      if (currentPath) loadDirectory(currentPath);
    } catch (e: any) {
      alert('Batch recovery failed: ' + e.message);
    } finally {
      setIsRecoveringBatch(false);
    }
  };

  const toggleSelectPath = (path: string) => {
    setSelectedPaths(prev => 
      prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]
    );
  };

  const toggleSelectAll = (filteredList: JpegAnalysis[]) => {
    const allFilteredPaths = filteredList.map(f => f.filepath);
    const allSelected = allFilteredPaths.every(p => selectedPaths.includes(p));
    if (allSelected) {
      setSelectedPaths(prev => prev.filter(p => !allFilteredPaths.includes(p)));
    } else {
      setSelectedPaths(prev => Array.from(new Set([...prev, ...allFilteredPaths])));
    }
  };

  const inspectSingleFromBatch = (item: JpegAnalysis) => {
    const fileObj = directoryContent?.files.find(f => f.path === item.filepath) || {
      name: item.filename,
      path: item.filepath,
      size: item.file_size,
      mtime: Date.now(),
      ext: item.filename.split('.').pop() || 'jpg',
      is_dir: false
    };
    setActiveFile(fileObj);
    setStudioMode('single');
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400 border-green-500/40 bg-green-950/40';
    if (score >= 60) return 'text-yellow-400 border-yellow-500/40 bg-yellow-950/40';
    return 'text-red-400 border-red-500/40 bg-red-950/40';
  };

  const displayedBatchItems = (batchScanData?.results || []).filter(item => {
    if (onlyCorruptedFilter) return item.is_corrupt || item.recoverable;
    return true;
  });

  return (
    <div className="flex-1 flex flex-col bg-xn-bg overflow-hidden select-none">
      {/* Studio Header & Mode Switcher */}
      <div className="h-10 bg-xn-panel border-b border-xn-border flex items-center justify-between px-3 text-xs z-10">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('browser')}
            className="flex items-center space-x-1 px-2.5 py-1 bg-xn-surface hover:bg-xn-hover border border-xn-border rounded text-xn-textBright transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Browser</span>
          </button>
          
          <div className="flex items-center bg-xn-bg p-0.5 rounded border border-xn-border ml-2">
            <button
              onClick={() => setStudioMode('batch')}
              className={`px-3 py-1 rounded text-xs font-medium flex items-center space-x-1.5 transition ${
                studioMode === 'batch'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-xn-text hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Multi-Photo Batch Recovery</span>
            </button>

            <button
              onClick={() => setStudioMode('single')}
              className={`px-3 py-1 rounded text-xs font-medium flex items-center space-x-1.5 transition ${
                studioMode === 'single'
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'text-xn-text hover:text-white'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Single Photo Deep Inspector</span>
            </button>
          </div>
        </div>

        {/* Header Right Action */}
        <div>
          {studioMode === 'batch' ? (
            <button
              onClick={handleBatchScan}
              disabled={isScanningBatch || !currentPath}
              className="flex items-center space-x-1.5 px-3 py-1 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded font-medium transition shadow"
            >
              <FolderSearch className="w-3.5 h-3.5" />
              <span>{isScanningBatch ? 'Scanning Folder...' : 'Scan Folder for Corrupted Photos'}</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <select
                onChange={(e) => handleExecuteSingleRecovery(e.target.value)}
                defaultValue="auto"
                disabled={isRecoveringSingle || isLoadingSingle || !activeFile}
                className="bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
              >
                <option value="auto">⚡ Smart Auto (Fusion + Crop + Donor + Bitstream)</option>
                <option value="thumbnail_fusion">🪄 Thumbnail-Guided Fusion (0% Grey)</option>
                <option value="pristine_crop">✂️ Pristine Native Crop (0% Grey Blocks)</option>
                <option value="inpainted_fill">🎨 Context-Aware Inpainted Fill</option>
                <option value="thumbnail_hd">✨ Enhanced HD Thumbnail (Upscaled)</option>
                <option value="donor_reference">📷 Donor Reference Photo Grafting</option>
                <option value="donor_header">🧩 Baseline Header Grafting (Annex K Tables)</option>
                <option value="byte_stuffing">🛠️ Repair Byte-Stuffing (Rogue 0xFF)</option>
                <option value="render_partial">📐 Scanline Salvage (EOI / IEND Termination)</option>
                <option value="extract_thumbnail">🖼️ Carve Embedded EXIF Previews</option>
                <option value="deep_carve">🔍 Forensic Deep Binary Stream Carving</option>
              </select>

              {suggestedDonors.length > 0 && (
                <div className="flex items-center space-x-1.5 bg-xn-surface border border-xn-border rounded px-2 py-1 text-xs">
                  <span className="text-[10px] text-xn-textMuted font-mono">Donor:</span>
                  <select
                    value={selectedDonor}
                    onChange={(e) => setSelectedDonor(e.target.value)}
                    className="bg-transparent text-[11px] text-amber-400 font-medium outline-none cursor-pointer max-w-[150px] truncate"
                    title="Intact reference donor photo for header grafting"
                  >
                    {suggestedDonors.map(d => (
                      <option key={d.path} value={d.path} className="bg-xn-bg text-xn-text">
                        {d.name} {d.is_same_session ? '★' : ''} ({d.width}×{d.height})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <button
                onClick={() => handleExecuteSingleRecovery('auto')}
                disabled={isRecoveringSingle || isLoadingSingle || !activeFile}
                className="flex items-center space-x-1.5 px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded font-medium transition shadow"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isRecoveringSingle ? 'Executing Recovery...' : 'Run Recovery'}</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ======================================================== */}
      {/* 1. MULTI-PHOTO BATCH RECOVERY MODE                       */}
      {/* ======================================================== */}
      {studioMode === 'batch' ? (
        <div className="flex-1 flex flex-col overflow-hidden p-4 space-y-4">
          {/* Top Banner & Scan Action if not scanned yet */}
          {!batchScanData && !isScanningBatch ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-xn-surface border border-xn-border rounded-lg space-y-3">
              <div className="w-14 h-14 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                <Layers className="w-7 h-7" />
              </div>
              <div className="space-y-1 max-w-md">
                <h3 className="font-semibold text-xn-textBright text-sm">
                  Batch Multi-Photo Corruption Scanner & Recovery
                </h3>
                <p className="text-xs text-xn-textMuted leading-relaxed">
                  Scan all photos in the current folder ({currentPath || 'selected folder'}) to detect damaged, cut-off, or truncated JPEGs, and extract all unharmed embedded preview copies in one pass.
                </p>
              </div>
              <button
                onClick={handleBatchScan}
                disabled={!currentPath}
                className="mt-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-md font-medium text-xs flex items-center space-x-2 shadow-lg transition"
              >
                <FolderSearch className="w-4 h-4" />
                <span>Start Batch Corruption Scan</span>
              </button>
            </div>
          ) : isScanningBatch ? (
            <div className="flex-1 flex flex-col items-center justify-center space-y-3 text-xs text-xn-text">
              <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              <span className="font-medium">Inspecting JPEG marker trees across all photos in folder...</span>
            </div>
          ) : batchScanData ? (
            <div className="flex-1 flex flex-col space-y-3 overflow-hidden">
              {/* Batch Summary Stats Cards */}
              <div className="grid grid-cols-4 gap-3 text-xs shrink-0">
                <div className="bg-xn-surface p-2.5 rounded-lg border border-xn-border space-y-0.5">
                  <span className="text-[10px] text-xn-textMuted uppercase font-semibold">Total Scanned</span>
                  <div className="text-base font-bold text-xn-textBright font-mono">{batchScanData.total_scanned} photos</div>
                </div>

                <div className="bg-xn-surface p-2.5 rounded-lg border border-amber-500/30 space-y-0.5">
                  <span className="text-[10px] text-amber-400 uppercase font-semibold">Corrupted Photos</span>
                  <div className="text-base font-bold text-amber-400 font-mono">{batchScanData.corrupt_count} damaged</div>
                </div>

                <div className="bg-xn-surface p-2.5 rounded-lg border border-green-500/30 space-y-0.5">
                  <span className="text-[10px] text-green-400 uppercase font-semibold">Recoverable Photos</span>
                  <div className="text-base font-bold text-green-400 font-mono">{batchScanData.recoverable_count} recoverable</div>
                </div>

                <div className="bg-xn-surface p-2.5 rounded-lg border border-xn-border space-y-0.5">
                  <span className="text-[10px] text-xn-textMuted uppercase font-semibold">Clean Intact Files</span>
                  <div className="text-base font-bold text-xn-textMuted font-mono">
                    {batchScanData.total_scanned - batchScanData.corrupt_count} clean
                  </div>
                </div>
              </div>

              {/* Action Toolbar for Batch Execution */}
              <div className="bg-xn-surface p-2.5 rounded-lg border border-xn-border flex items-center justify-between text-xs shrink-0">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => toggleSelectAll(displayedBatchItems)}
                    className="flex items-center space-x-1.5 px-2.5 py-1 bg-xn-panel hover:bg-xn-hover border border-xn-border rounded text-xn-textBright transition"
                  >
                    {displayedBatchItems.every(f => selectedPaths.includes(f.filepath)) ? (
                      <CheckSquare className="w-3.5 h-3.5 text-amber-400" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-xn-textMuted" />
                    )}
                    <span>Select All Filtered ({displayedBatchItems.length})</span>
                  </button>

                  <label className="flex items-center space-x-1.5 cursor-pointer text-xn-text">
                    <input
                      type="checkbox"
                      checked={onlyCorruptedFilter}
                      onChange={(e) => setOnlyCorruptedFilter(e.target.checked)}
                      className="accent-amber-500"
                    />
                    <span>Show Corrupted / Damaged Only</span>
                  </label>

                  <select
                    value={batchRecoveryType}
                    onChange={(e) => setBatchRecoveryType(e.target.value)}
                    className="bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
                  >
                    <option value="auto">⚡ Smart Auto (Multi-Pass: Fusion + Crop + Donor Graft + Bitstream)</option>
                    <option value="thumbnail_fusion">🪄 Thumbnail-Guided Fusion (0% Grey Blocks)</option>
                    <option value="pristine_crop">✂️ Pristine Native Crop (0% Grey Blocks)</option>
                    <option value="inpainted_fill">🎨 Context-Aware Inpainted Fill</option>
                    <option value="thumbnail_hd">✨ Enhanced HD Thumbnail (Upscaled)</option>
                    <option value="extract_thumbnail">🖼️ Carve Embedded EXIF Previews Only</option>
                    <option value="render_partial">📐 Render Partial Scanlines with EOI / IEND Repair</option>
                    <option value="donor_header">🧩 Baseline Header Grafting (Annex K Tables)</option>
                    <option value="deep_carve">🔍 Forensic Deep Binary Stream Carving</option>
                  </select>
                </div>

                {/* Big Recover Selected Button */}
                <button
                  onClick={handleBatchExecute}
                  disabled={isRecoveringBatch || selectedPaths.length === 0}
                  className="px-4 py-1.5 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 disabled:opacity-40 text-white rounded font-medium shadow flex items-center space-x-1.5 transition"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>
                    {isRecoveringBatch 
                      ? 'Recovering Selected Photos...' 
                      : `Recover All Selected (${selectedPaths.length}) Photos`}
                  </span>
                </button>
              </div>

              {/* Batch Execution Results Gallery Banner */}
              {batchResult && (
                <div className="bg-green-950/40 border border-green-600/70 p-3 rounded-lg text-xs space-y-3 shrink-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-green-300 flex items-center space-x-1.5">
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                      <span>
                        Multi-Photo Recovery Complete! {batchResult.total_recovered_artifacts} restored artifact(s) generated from {batchResult.total_files_processed} photo(s).
                      </span>
                    </span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          loadDirectory(batchResult.output_dir);
                          setViewMode('browser');
                        }}
                        className="px-2.5 py-1 bg-green-700 hover:bg-green-600 text-white rounded font-medium flex items-center space-x-1 transition shadow"
                        title="Browse recovered images in Photorecover"
                      >
                        <FolderOpen className="w-3.5 h-3.5" />
                        <span>View Recovered in Browser</span>
                      </button>

                      <button
                        onClick={() => api.revealInExplorer(batchResult.output_dir)}
                        className="px-2.5 py-1 bg-xn-surface hover:bg-xn-hover border border-green-500/50 text-green-200 rounded font-medium flex items-center space-x-1 transition"
                        title="Open output folder in Windows File Explorer"
                      >
                        <FolderSearch className="w-3.5 h-3.5" />
                        <span>Show in Explorer</span>
                      </button>
                    </div>
                  </div>

                  {/* Recovered Items Preview Row */}
                  <div className="flex items-center space-x-3 overflow-x-auto py-1">
                    {batchResult.results.flatMap(r => r.recovered_files || []).map((art, idx) => (
                      <div
                        key={idx}
                        className="flex items-center space-x-2 bg-xn-panel/80 border border-green-500/30 p-1.5 rounded-md shrink-0 cursor-pointer hover:border-green-400 transition"
                        onClick={() => {
                          const fileObj = {
                            name: art.filename || 'recovered.jpg',
                            path: art.filepath,
                            size: art.size || 0,
                            mtime: Date.now(),
                            ext: 'jpg',
                            is_dir: false
                          };
                          setActiveFile(fileObj);
                          setViewMode('viewer');
                        }}
                      >
                        <img
                          src={art.preview_base64 || api.getThumbnailUrl(art.filepath, 120)}
                          alt="preview"
                          className="w-12 h-12 object-cover rounded bg-black/50 border border-xn-border"
                        />
                        <div className="flex flex-col text-[11px] leading-tight">
                          <span className="font-semibold text-green-200 truncate max-w-[140px]">
                            {art.filename}
                          </span>
                          <span className="text-[10px] text-green-400 font-mono capitalize">
                            {art.method.replace(/_/g, ' ')}
                          </span>
                          <span className="text-[9px] text-xn-textMuted font-mono">
                            {art.width}x{art.height} • {art.size ? `${(art.size / 1024).toFixed(1)} KB` : ''}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Scanned Items Table & Grid */}
              <div className="flex-1 border border-xn-border rounded-lg bg-xn-surface overflow-hidden flex flex-col">
                <div className="p-2 border-b border-xn-border bg-xn-panel font-semibold text-[11px] text-xn-textMuted uppercase flex items-center justify-between">
                  <span>Detected Photo List ({displayedBatchItems.length})</span>
                  <span>Click any photo to Deep Inspect or Carve Previews</span>
                </div>

                <div className="flex-1 overflow-y-auto divide-y divide-xn-border/40">
                  {displayedBatchItems.map((item) => {
                    const isSelected = selectedPaths.includes(item.filepath);
                    return (
                      <div
                        key={item.filepath}
                        onClick={() => toggleSelectPath(item.filepath)}
                        className={`p-2.5 flex items-center justify-between hover:bg-xn-hover cursor-pointer transition ${
                          isSelected ? 'bg-amber-950/20' : ''
                        }`}
                      >
                        {/* Checkbox & File Info */}
                        <div className="flex items-center space-x-3 flex-1 min-w-0 pr-4">
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); toggleSelectPath(item.filepath); }}
                            className="text-xn-textMuted hover:text-white"
                          >
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-amber-400" />
                            ) : (
                              <Square className="w-4 h-4 text-xn-textMuted" />
                            )}
                          </button>

                          <div className="flex flex-col min-w-0">
                            <span className="font-medium text-xs text-xn-textBright truncate" title={item.filename}>
                              {item.filename}
                            </span>
                            <span className="text-[10px] text-xn-textMuted font-mono">
                              {(item.file_size / 1024).toFixed(1)} KB • {item.markers.length} markers parsed
                            </span>
                          </div>
                        </div>

                        {/* Damage & Diagnostics Badge */}
                        <div className="flex items-center space-x-3 shrink-0">
                          {item.is_corrupt ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-950/70 border border-red-800 text-red-300 flex items-center space-x-1">
                              <AlertTriangle className="w-3 h-3 text-red-400" />
                              <span>{typeof item.issues[0] === 'string' ? item.issues[0] : item.issues[0]?.message || 'Damaged / Truncated'}</span>
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-green-950/70 border border-green-800 text-green-300">
                              Intact (100%)
                            </span>
                          )}

                          {/* Embedded Previews Count */}
                          {item.embedded_thumbnail_count > 0 && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/70 border border-amber-800 text-amber-300">
                              {item.embedded_thumbnail_count} Embedded Preview(s)
                            </span>
                          )}

                          {/* Integrity Score */}
                          <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${getScoreColor(item.integrity_score)}`}>
                            {item.integrity_score}%
                          </span>

                          {/* Deep Inspect Button */}
                          <button
                            onClick={(e) => { e.stopPropagation(); inspectSingleFromBatch(item); }}
                            title="Open in Single Photo Deep Inspector"
                            className="p-1 rounded bg-xn-panel hover:bg-xn-hover border border-xn-border text-xn-text hover:text-white transition"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        /* ======================================================== */
        /* 2. SINGLE PHOTO DEEP INSPECTOR MODE                      */
        /* ======================================================== */
        activeFile ? (
          <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
            {/* Left 5 Cols: Diagnostics, Markers & Issues */}
            <div className="col-span-5 bg-xn-surface border-r border-xn-border flex flex-col h-full overflow-y-auto p-3.5 space-y-4 text-xs">
              {/* File & Integrity Score Header */}
              <div className="bg-xn-panel p-3 rounded-lg border border-xn-border space-y-2.5">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-xn-textBright truncate max-w-xs">{activeFile.name}</h3>
                      {analysis?.image_format && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-950/80 border border-blue-700 text-blue-300">
                          {analysis.image_format}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-xn-textMuted font-mono">{(activeFile.size / 1024).toFixed(1)} KB ({activeFile.size} bytes)</p>
                  </div>
                  {/* Score Badge */}
                  {analysis && (
                    <div className={`px-2.5 py-1 rounded-md border font-mono font-bold text-center ${getScoreColor(analysis.integrity_score)}`}>
                      <div className="text-sm">{analysis.integrity_score}%</div>
                      <div className="text-[9px] uppercase tracking-wider">Integrity</div>
                    </div>
                  )}
                </div>

                {/* Status Banner */}
                {analysis?.is_corrupt ? (
                  <div className="flex items-center space-x-2 bg-amber-950/40 border border-amber-700/60 p-2 rounded text-amber-200 text-[11px]">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>
                      Structural damage or truncation detected. 
                      {analysis.embedded_thumbnail_count > 0 && ` ${analysis.embedded_thumbnail_count} uncorrupted embedded preview(s) found in EXIF.`}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2 bg-green-950/40 border border-green-700/60 p-2 rounded text-green-200 text-[11px]">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-green-400" />
                    <span>File structure is intact. All mandatory markers and chunks are present.</span>
                  </div>
                )}
              </div>

              {/* Diagnostic Issues List */}
              {analysis && analysis.issues.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold text-red-400 uppercase tracking-wide">
                    Identified Corruption Issues ({analysis.issues.length})
                  </span>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {analysis.issues.map((iss, i) => {
                      const msg = typeof iss === 'string' ? iss : iss.message;
                      const sev = typeof iss === 'string' ? 'warning' : iss.severity;
                      const fix = typeof iss === 'object' ? iss.suggested_fix : null;
                      const code = typeof iss === 'object' ? iss.code : null;

                      return (
                        <div key={i} className="bg-red-950/30 border border-red-900/60 p-2 rounded text-[11px] text-red-300 flex flex-col space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-red-400 flex items-center space-x-1">
                              <span>•</span>
                              <span>{code || 'CORRUPTION'}</span>
                            </span>
                            <span className={`text-[9px] px-1.5 py-0.2 rounded uppercase font-bold ${
                              sev === 'critical' ? 'bg-red-800 text-white' : 'bg-yellow-800 text-yellow-200'
                            }`}>
                              {sev}
                            </span>
                          </div>
                          <p className="text-[11px] leading-tight text-red-200">{msg}</p>
                          {fix && (
                            <div className="text-[10px] text-green-300 bg-green-950/40 border border-green-800/40 px-1.5 py-0.5 rounded flex items-center space-x-1">
                              <span className="font-semibold text-green-400">Fix:</span>
                              <span>{fix}</span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Binary Marker Stream Inspection Table */}
              {analysis && (
                <div className="space-y-1.5 flex-1">
                  <span className="text-[11px] font-semibold text-xn-textMuted uppercase tracking-wide flex items-center justify-between">
                    <span>JPEG Marker Tree ({analysis.markers.length})</span>
                    <span className="font-mono text-[10px]">Offset (Hex)</span>
                  </span>
                  <div className="border border-xn-border rounded bg-xn-bg overflow-hidden max-h-56 overflow-y-auto">
                    <table className="w-full text-[11px] text-left">
                      <thead className="bg-xn-panel text-xn-textMuted text-[10px] uppercase font-mono">
                        <tr>
                          <th className="p-1.5">Marker</th>
                          <th className="p-1.5">Name</th>
                          <th className="p-1.5 text-right">Offset</th>
                          <th className="p-1.5 text-right">Size</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-xn-border/40 font-mono text-[10px]">
                        {analysis.markers.map((m, idx) => (
                          <tr key={idx} className="hover:bg-xn-hover">
                            <td className="p-1.5 font-bold text-blue-400">{m.marker}</td>
                            <td className="p-1.5 text-xn-textBright truncate max-w-[140px]">{m.name}</td>
                            <td className="p-1.5 text-right text-xn-textMuted">0x{m.offset.toString(16).toUpperCase()}</td>
                            <td className="p-1.5 text-right text-xn-textMuted">{m.length} B</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Recovery Methodology */}
              <div className="bg-blue-950/20 border border-blue-900/40 p-2.5 rounded text-[11px] text-blue-300/90 space-y-1">
                <div className="flex items-center space-x-1.5 font-semibold text-blue-400">
                  <Info className="w-3.5 h-3.5" />
                  <span>Recovery Methodology</span>
                </div>
                <p className="leading-relaxed">
                  When a JPEG file is truncated or damaged, missing scan data cannot be magically reconstructed. However, our engine carves uncorrupted embedded thumbnails from EXIF headers and re-terminates broken scanlines so images can be safely recovered and viewed without data loss.
                </p>
              </div>
            </div>

            {/* Right 7 Cols: Embedded Thumbnails & Side-by-Side Recovery View */}
            <div className="col-span-7 bg-xn-bg flex flex-col h-full overflow-y-auto p-4 space-y-4">
              {/* Embedded Thumbnail Carving Section */}
              {analysis && analysis.embedded_thumbnails.length > 0 && (
                <div className="bg-xn-surface border border-xn-border rounded-lg p-3 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                      <span className="font-semibold text-xn-textBright text-xs">
                        Extracted Embedded EXIF Previews ({analysis.embedded_thumbnails.length})
                      </span>
                    </div>
                    <span className="text-[10px] text-green-400 bg-green-950/60 border border-green-800/80 px-2 py-0.5 rounded font-medium">
                      100% Intact Previews
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    {analysis.embedded_thumbnails.map((thumb, idx) => (
                      <div key={idx} className="bg-xn-panel border border-xn-border rounded p-2 flex flex-col space-y-2">
                        <div className="h-36 bg-black/60 rounded overflow-hidden flex items-center justify-center checkerboard-pattern">
                          <img 
                            src={thumb.preview_base64} 
                            alt="Carved Thumbnail" 
                            className="max-h-full max-w-full object-contain"
                          />
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-xn-textMuted font-mono">
                          <span>{thumb.width} × {thumb.height} px</span>
                          <span>{(thumb.size / 1024).toFixed(1)} KB</span>
                        </div>
                        <button
                          onClick={() => handleExecuteSingleRecovery('extract_thumbnail')}
                          className="w-full py-1 bg-xn-surface hover:bg-xn-hover border border-xn-border text-xn-text rounded text-xs font-medium flex items-center justify-center space-x-1 transition"
                          title="Extract the low-resolution EXIF camera thumbnail only"
                        >
                          <Download className="w-3 h-3 text-xn-textMuted" />
                          <span>Extract Low-Res Thumbnail ({thumb.width}×{thumb.height})</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Side-by-Side Recovery Artifacts Preview */}
              {singleRecoveryResult && singleRecoveryResult.recovered_files.length > 0 ? (
                <div className="bg-xn-surface border border-green-700/60 rounded-lg p-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-green-400 text-xs flex items-center space-x-1.5">
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                      <span>Recovery Completed — {singleRecoveryResult.recovered_count} File(s) Generated (Sorted by Quality)</span>
                    </span>
                  </div>

                  <div className="space-y-3">
                    {singleRecoveryResult.recovered_files.map((art, idx) => (
                      <div key={idx} className="bg-xn-panel border border-xn-border rounded p-3 grid grid-cols-12 gap-3 items-center">
                        <div className="col-span-4 h-28 bg-black/60 rounded overflow-hidden flex items-center justify-center checkerboard-pattern">
                          {art.preview_base64 ? (
                            <img src={art.preview_base64} alt="Recovered" className="max-h-full max-w-full object-contain" />
                          ) : (
                            <div className="text-[10px] text-xn-textMuted">Preview Saved</div>
                          )}
                        </div>
                        <div className="col-span-8 space-y-1.5 text-xs">
                          <div className="flex items-center justify-between">
                            <div className="font-bold text-xn-textBright flex items-center space-x-2">
                              <span>{art.method}</span>
                              {art.width >= 600 && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-green-950 border border-green-600 text-green-300 uppercase">
                                  Full Resolution
                                </span>
                              )}
                            </div>
                            <a
                              href={api.getDownloadUrl(art.filepath)}
                              download={art.filename}
                              className="px-2.5 py-1 bg-green-700 hover:bg-green-600 text-white rounded text-[11px] font-medium flex items-center space-x-1 shadow transition"
                              title="Download full quality master file"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download High Quality</span>
                            </a>
                          </div>
                          <div className="text-[11px] text-xn-textMuted font-mono truncate">{art.filename}</div>
                          <div className="text-[11px] text-xn-accent font-mono font-semibold">{art.width} × {art.height} px ({(art.size / 1024).toFixed(1)} KB)</div>
                          <p className="text-[11px] text-xn-text">{art.description}</p>
                          <div className="text-[10px] text-green-400 font-mono truncate">Saved in: {art.filepath}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                /* Original File Display */
                <div className="bg-xn-surface border border-xn-border rounded-lg p-4 flex flex-col items-center justify-center space-y-3">
                  <div className="flex items-center justify-between w-full">
                    <span className="text-[11px] font-semibold text-xn-textMuted uppercase tracking-wide">
                      Damaged File Preview (Current State)
                    </span>
                    <span className="text-[10px] text-amber-400 font-mono">
                      {activeFile.name}
                    </span>
                  </div>
                  <div className="max-h-80 w-full bg-black/80 rounded overflow-hidden flex items-center justify-center p-2 checkerboard-pattern">
                    <img
                      src={api.getRawImageUrl(activeFile.path)}
                      alt={activeFile.name}
                      className="max-h-72 object-contain"
                    />
                  </div>
                  
                  <div className="flex flex-col items-center space-y-2 pt-1 w-full max-w-md text-center">
                    <button
                      onClick={() => handleExecuteSingleRecovery('auto')}
                      disabled={isRecoveringSingle}
                      className="w-full py-2.5 px-4 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded font-semibold text-xs flex items-center justify-center space-x-2 shadow-lg hover:shadow-green-500/20 transition cursor-pointer"
                    >
                      <Sparkles className="w-4 h-4 text-green-200" />
                      <span>{isRecoveringSingle ? 'Reconstructing Photo at 100% Quality...' : '⚡ Reconstruct Full-Resolution Photo (100% Quality)'}</span>
                    </button>
                    <p className="text-[11px] text-xn-textMuted">
                      Applies lossless bitstream repair, missing EOI termination, and Annex K quantization tables with zero downsampling (4:4:4 chroma, quality=100).
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-xs text-xn-textMuted">
            <p>Select a photo to deep inspect, or switch to Multi-Photo Batch Recovery mode.</p>
          </div>
        )
      )}
    </div>
  );
};
