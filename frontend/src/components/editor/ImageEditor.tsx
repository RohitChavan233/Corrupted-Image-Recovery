import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Save, 
  RotateCw, 
  FlipHorizontal, 
  FlipVertical, 
  Crop, 
  Sliders, 
  Wand2, 
  Type, 
  Undo, 
  Redo, 
  RefreshCcw,
  CheckCircle,
  FileImage
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';

export const ImageEditor: React.FC = () => {
  const { activeFile, setViewMode, loadDirectory, currentPath } = useAppStore();

  // Adjustment State
  const [brightness, setBrightness] = useState(1.0);
  const [contrast, setContrast] = useState(1.0);
  const [saturation, setSaturation] = useState(1.0);
  const [gamma, setGamma] = useState(1.0);
  const [filterName, setFilterName] = useState<string>('none');

  // Transform State
  const [rotation, setRotation] = useState(0);
  const [flipH, setFlipH] = useState(false);
  const [flipV, setFlipV] = useState(false);

  // Resize State
  const [resizeWidth, setResizeWidth] = useState<number>(activeFile?.width || 1920);
  const [resizeHeight, setResizeHeight] = useState<number>(activeFile?.height || 1080);
  const [maintainAspect, setMaintainAspect] = useState(true);

  // Watermark State
  const [watermarkText, setWatermarkText] = useState('');
  const [watermarkColor, setWatermarkColor] = useState('#ffffff');
  const [watermarkPosition, setWatermarkPosition] = useState('bottom-right');

  // Preview & Processing state
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Active Tab: 'adjust' | 'filters' | 'transform' | 'watermark'
  const [activeTab, setActiveTab] = useState<'adjust' | 'filters' | 'transform' | 'watermark'>('adjust');

  // Initialize preview
  useEffect(() => {
    if (activeFile) {
      setPreviewUrl(api.getRawImageUrl(activeFile.path));
      if (activeFile.width) setResizeWidth(activeFile.width);
      if (activeFile.height) setResizeHeight(activeFile.height);
    }
  }, [activeFile]);

  // Handle Resize input
  const handleWidthChange = (val: number) => {
    setResizeWidth(val);
    if (maintainAspect && activeFile?.width && activeFile?.height) {
      const ratio = activeFile.height / activeFile.width;
      setResizeHeight(Math.round(val * ratio));
    }
  };

  const handleHeightChange = (val: number) => {
    setResizeHeight(val);
    if (maintainAspect && activeFile?.width && activeFile?.height) {
      const ratio = activeFile.width / activeFile.height;
      setResizeWidth(Math.round(val * ratio));
    }
  };

  const handleResetAdjustments = () => {
    setBrightness(1.0);
    setContrast(1.0);
    setSaturation(1.0);
    setGamma(1.0);
    setFilterName('none');
    setRotation(0);
    setFlipH(false);
    setFlipV(false);
    setWatermarkText('');
    if (activeFile) {
      setPreviewUrl(api.getRawImageUrl(activeFile.path));
    }
  };

  // Generate Real Server-side Preview
  const handleApplyPreview = async () => {
    if (!activeFile) return;
    setIsProcessing(true);
    setSaveSuccessMsg(null);
    try {
      const resizeParams = (resizeWidth !== activeFile.width || resizeHeight !== activeFile.height)
        ? { width: resizeWidth, height: resizeHeight }
        : undefined;

      const res = await api.processImage({
        filepath: activeFile.path,
        brightness,
        contrast,
        saturation,
        gamma,
        filter_name: filterName === 'none' ? undefined : filterName,
        rotate: rotation,
        flip_h: flipH,
        flip_v: flipV,
        resize: resizeParams,
        watermark_text: watermarkText.trim() || undefined,
        watermark_color: watermarkColor,
        watermark_position: watermarkPosition,
        output_format: 'JPEG',
        output_quality: 92
      });

      if (res.blob) {
        const url = URL.createObjectURL(res.blob);
        setPreviewUrl(url);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  // Save to Disk
  const handleSaveCopy = async () => {
    if (!activeFile) return;
    setIsProcessing(true);
    try {
      const p = activeFile.path;
      const dotIdx = p.lastIndexOf('.');
      const savePath = `${p.substring(0, dotIdx)}_edited.jpg`;

      const resizeParams = (resizeWidth !== activeFile.width || resizeHeight !== activeFile.height)
        ? { width: resizeWidth, height: resizeHeight }
        : undefined;

      const res = await api.processImage({
        filepath: activeFile.path,
        brightness,
        contrast,
        saturation,
        gamma,
        filter_name: filterName === 'none' ? undefined : filterName,
        rotate: rotation,
        flip_h: flipH,
        flip_v: flipV,
        resize: resizeParams,
        watermark_text: watermarkText.trim() || undefined,
        watermark_color: watermarkColor,
        watermark_position: watermarkPosition,
        output_format: 'JPEG',
        output_quality: 95,
        save_as: savePath
      });

      if (res.success) {
        setSaveSuccessMsg(`Saved copy: ${savePath.split(/[/\\]/).pop()}`);
        if (currentPath) {
          loadDirectory(currentPath);
        }
      }
    } catch (e: any) {
      console.error(e);
      alert('Failed to save image: ' + e.message);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!activeFile) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-xn-bg text-xn-textMuted text-xs">
        <p>No image selected to edit.</p>
        <button onClick={() => setViewMode('browser')} className="mt-2 px-3 py-1 bg-xn-accent text-white rounded">
          Back to Browser
        </button>
      </div>
    );
  }

  const filtersList = [
    { id: 'none', label: 'Original' },
    { id: 'sharpen', label: 'Sharpen' },
    { id: 'blur', label: 'Gaussian Blur' },
    { id: 'grayscale', label: 'Grayscale' },
    { id: 'sepia', label: 'Vintage Sepia' },
    { id: 'invert', label: 'Invert Colors' },
    { id: 'edge', label: 'Find Edges' },
    { id: 'noise_reduction', label: 'Noise Reduction' }
  ];

  return (
    <div className="flex-1 flex flex-col bg-xn-bg overflow-hidden select-none">
      {/* Editor Top Navigation */}
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
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span className="truncate max-w-sm">{activeFile.name}</span>
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {saveSuccessMsg && (
            <span className="text-green-400 text-xs flex items-center space-x-1 bg-green-950/60 border border-green-800/80 px-2 py-0.5 rounded">
              <CheckCircle className="w-3 h-3" />
              <span>{saveSuccessMsg}</span>
            </span>
          )}

          <button
            onClick={handleResetAdjustments}
            title="Reset All Adjustments"
            className="flex items-center space-x-1 px-2.5 py-1 bg-xn-surface hover:bg-xn-hover border border-xn-border rounded text-xn-text hover:text-white transition"
          >
            <RefreshCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>

          <button
            onClick={handleApplyPreview}
            disabled={isProcessing}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium transition shadow"
          >
            <span>{isProcessing ? 'Rendering...' : 'Apply Live Preview'}</span>
          </button>

          <button
            onClick={handleSaveCopy}
            disabled={isProcessing}
            className="flex items-center space-x-1 px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded font-medium transition shadow"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Copy</span>
          </button>
        </div>
      </div>

      {/* Editor Body: Left Controls Panel + Right Canvas Preview */}
      <div className="flex-1 flex overflow-hidden">
        {/* Controls Sidebar */}
        <div className="w-72 bg-xn-surface border-r border-xn-border flex flex-col h-full text-xs overflow-y-auto">
          {/* Tool Tabs */}
          <div className="grid grid-cols-4 bg-xn-panel border-b border-xn-border text-[11px] font-medium">
            <button
              onClick={() => setActiveTab('adjust')}
              className={`py-2 border-b-2 transition ${
                activeTab === 'adjust' ? 'border-xn-accent text-xn-accent bg-xn-surface' : 'border-transparent text-xn-text hover:text-white'
              }`}
            >
              Adjust
            </button>
            <button
              onClick={() => setActiveTab('filters')}
              className={`py-2 border-b-2 transition ${
                activeTab === 'filters' ? 'border-xn-accent text-xn-accent bg-xn-surface' : 'border-transparent text-xn-text hover:text-white'
              }`}
            >
              Filters
            </button>
            <button
              onClick={() => setActiveTab('transform')}
              className={`py-2 border-b-2 transition ${
                activeTab === 'transform' ? 'border-xn-accent text-xn-accent bg-xn-surface' : 'border-transparent text-xn-text hover:text-white'
              }`}
            >
              Transform
            </button>
            <button
              onClick={() => setActiveTab('watermark')}
              className={`py-2 border-b-2 transition ${
                activeTab === 'watermark' ? 'border-xn-accent text-xn-accent bg-xn-surface' : 'border-transparent text-xn-text hover:text-white'
              }`}
            >
              Watermark
            </button>
          </div>

          <div className="p-3.5 space-y-4 flex-1">
            {/* Tab: Adjustments */}
            {activeTab === 'adjust' && (
              <div className="space-y-3.5">
                {/* Brightness */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xn-textMuted">
                    <span>Brightness</span>
                    <span className="font-mono text-xn-textBright">{brightness.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="2.5"
                    step="0.05"
                    value={brightness}
                    onChange={(e) => setBrightness(parseFloat(e.target.value))}
                    className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                  />
                </div>

                {/* Contrast */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xn-textMuted">
                    <span>Contrast</span>
                    <span className="font-mono text-xn-textBright">{contrast.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="2.5"
                    step="0.05"
                    value={contrast}
                    onChange={(e) => setContrast(parseFloat(e.target.value))}
                    className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                  />
                </div>

                {/* Saturation */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xn-textMuted">
                    <span>Saturation (Color)</span>
                    <span className="font-mono text-xn-textBright">{saturation.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="2.5"
                    step="0.05"
                    value={saturation}
                    onChange={(e) => setSaturation(parseFloat(e.target.value))}
                    className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                  />
                </div>

                {/* Gamma */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xn-textMuted">
                    <span>Gamma Correction</span>
                    <span className="font-mono text-xn-textBright">{gamma.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="2.5"
                    step="0.05"
                    value={gamma}
                    onChange={(e) => setGamma(parseFloat(e.target.value))}
                    className="w-full accent-xn-accent h-1.5 bg-xn-panel rounded cursor-pointer"
                  />
                </div>
              </div>
            )}

            {/* Tab: Filters */}
            {activeTab === 'filters' && (
              <div className="space-y-2">
                <span className="text-[11px] font-semibold text-xn-textMuted uppercase">Select Filter:</span>
                <div className="grid grid-cols-2 gap-2">
                  {filtersList.map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setFilterName(f.id)}
                      className={`p-2 rounded border text-left transition ${
                        filterName === f.id
                          ? 'border-xn-accent bg-xn-accent/20 text-white font-medium shadow-sm'
                          : 'border-xn-border bg-xn-panel text-xn-text hover:bg-xn-hover hover:text-white'
                      }`}
                    >
                      <div className="font-medium text-xs">{f.label}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Tab: Transform (Rotate, Flip, Resize) */}
            {activeTab === 'transform' && (
              <div className="space-y-4">
                {/* Rotations & Flips */}
                <div>
                  <span className="text-[11px] font-semibold text-xn-textMuted uppercase mb-1.5 block">Orientation:</span>
                  <div className="grid grid-cols-3 gap-1.5">
                    <button
                      onClick={() => setRotation(r => (r + 90) % 360)}
                      className="flex items-center justify-center space-x-1 p-2 bg-xn-panel hover:bg-xn-hover border border-xn-border rounded text-xn-textBright transition"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      <span>+90°</span>
                    </button>
                    <button
                      onClick={() => setFlipH(f => !f)}
                      className={`flex items-center justify-center space-x-1 p-2 border border-xn-border rounded transition ${
                        flipH ? 'bg-xn-accent text-white' : 'bg-xn-panel hover:bg-xn-hover text-xn-textBright'
                      }`}
                    >
                      <FlipHorizontal className="w-3.5 h-3.5" />
                      <span>Flip H</span>
                    </button>
                    <button
                      onClick={() => setFlipV(f => !f)}
                      className={`flex items-center justify-center space-x-1 p-2 border border-xn-border rounded transition ${
                        flipV ? 'bg-xn-accent text-white' : 'bg-xn-panel hover:bg-xn-hover text-xn-textBright'
                      }`}
                    >
                      <FlipVertical className="w-3.5 h-3.5" />
                      <span>Flip V</span>
                    </button>
                  </div>
                </div>

                {/* Resize */}
                <div className="space-y-2 pt-2 border-t border-xn-border">
                  <span className="text-[11px] font-semibold text-xn-textMuted uppercase block">Resize Dimensions (px):</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-xn-textMuted">Width</label>
                      <input
                        type="number"
                        value={resizeWidth}
                        onChange={(e) => handleWidthChange(parseInt(e.target.value) || 0)}
                        className="w-full bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-xn-textMuted">Height</label>
                      <input
                        type="number"
                        value={resizeHeight}
                        onChange={(e) => handleHeightChange(parseInt(e.target.value) || 0)}
                        className="w-full bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none"
                      />
                    </div>
                  </div>
                  <label className="flex items-center space-x-1.5 cursor-pointer text-[11px] text-xn-text">
                    <input
                      type="checkbox"
                      checked={maintainAspect}
                      onChange={(e) => setMaintainAspect(e.target.checked)}
                      className="accent-xn-accent"
                    />
                    <span>Maintain Aspect Ratio</span>
                  </label>
                </div>
              </div>
            )}

            {/* Tab: Watermark */}
            {activeTab === 'watermark' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-xn-textMuted uppercase block">Watermark Text:</label>
                  <input
                    type="text"
                    placeholder="e.g. © 2026 Copyright"
                    value={watermarkText}
                    onChange={(e) => setWatermarkText(e.target.value)}
                    className="w-full bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-xn-textMuted uppercase block">Position:</label>
                  <select
                    value={watermarkPosition}
                    onChange={(e) => setWatermarkPosition(e.target.value)}
                    className="w-full bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none cursor-pointer"
                  >
                    <option value="bottom-right">Bottom-Right</option>
                    <option value="bottom-left">Bottom-Left</option>
                    <option value="top-right">Top-Right</option>
                    <option value="top-left">Top-Left</option>
                    <option value="center">Center</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-xn-textMuted uppercase block">Text Color:</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="color"
                      value={watermarkColor}
                      onChange={(e) => setWatermarkColor(e.target.value)}
                      className="w-8 h-8 rounded border border-xn-border cursor-pointer bg-transparent"
                    />
                    <span className="font-mono text-xn-textBright">{watermarkColor}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Canvas: Live Image View */}
        <div className="flex-1 bg-black flex items-center justify-center p-4 relative checkerboard-pattern overflow-hidden">
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Editor Preview"
              className="max-w-full max-h-full object-contain rounded shadow-2xl transition-all"
            />
          )}

          {isProcessing && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center space-x-2 text-white text-xs">
              <div className="w-5 h-5 border-2 border-xn-accent border-t-transparent rounded-full animate-spin" />
              <span>Processing image with Pillow SIMD...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
