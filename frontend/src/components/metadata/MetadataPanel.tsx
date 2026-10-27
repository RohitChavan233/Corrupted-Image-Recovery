import React, { useState, useEffect } from 'react';
import { 
  Info, 
  MapPin, 
  Star, 
  Tag, 
  FileText, 
  ShieldCheck, 
  ExternalLink,
  Camera,
  Layers,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { ExifData } from '../../types';

export const MetadataPanel: React.FC = () => {
  const { activeFile, metadataVisible, loadDirectory, currentPath } = useAppStore();

  const [metadata, setMetadata] = useState<ExifData | null>(null);
  const [rating, setRating] = useState(0);
  const [colorLabel, setColorLabel] = useState('');
  const [tags, setTags] = useState('');
  const [comment, setComment] = useState('');
  const [showAllExif, setShowAllExif] = useState(false);
  const [isStripping, setIsStripping] = useState(false);
  const [strippedSuccess, setStrippedSuccess] = useState(false);

  useEffect(() => {
    if (activeFile) {
      setStrippedSuccess(false);
      api.getMetadata(activeFile.path).then((data) => {
        setMetadata(data);
        setRating(data.user_rating || 0);
        setColorLabel(data.color_label || '');
        setTags(data.user_tags || '');
        setComment(data.user_comment || '');
      }).catch(console.error);
    }
  }, [activeFile]);

  if (!metadataVisible || !activeFile) return null;

  const handleRatingChange = async (newRating: number) => {
    const val = rating === newRating ? 0 : newRating;
    setRating(val);
    await api.updateAnnotations({ filepath: activeFile.path, rating: val });
    activeFile.rating = val;
  };

  const handleColorChange = async (c: string) => {
    const val = colorLabel === c ? '' : c;
    setColorLabel(val);
    await api.updateAnnotations({ filepath: activeFile.path, color_label: val });
    activeFile.color_label = val;
  };

  const handleTagsBlur = async () => {
    await api.updateAnnotations({ filepath: activeFile.path, tags });
    activeFile.tags = tags;
  };

  const handleCommentBlur = async () => {
    await api.updateAnnotations({ filepath: activeFile.path, comment });
  };

  const handleStripMetadata = async () => {
    setIsStripping(true);
    try {
      await api.stripMetadata(activeFile.path);
      setStrippedSuccess(true);
      if (currentPath) loadDirectory(currentPath);
    } catch (e: any) {
      alert('Failed to strip metadata: ' + e.message);
    } finally {
      setIsStripping(false);
    }
  };

  const colorLabels = [
    { name: 'Red', hex: '#ef4444' },
    { name: 'Yellow', hex: '#eab308' },
    { name: 'Green', hex: '#22c55e' },
    { name: 'Blue', hex: '#3b82f6' },
    { name: 'Purple', hex: '#a855f7' }
  ];

  return (
    <aside className="w-72 bg-xn-surface border-l border-xn-border flex flex-col h-full overflow-hidden text-xs select-none">
      {/* Panel Header */}
      <div className="p-2.5 border-b border-xn-border font-semibold text-xn-textBright uppercase tracking-wider text-[10px] flex items-center justify-between">
        <span className="flex items-center space-x-1.5">
          <Info className="w-3.5 h-3.5 text-blue-400" />
          <span>Information & EXIF</span>
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Rating & Color Label Tagging */}
        <div className="bg-xn-panel p-2.5 rounded border border-xn-border space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase text-xn-textMuted">Rating:</span>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRatingChange(star)}
                  className="hover:scale-125 transition"
                >
                  <Star
                    className={`w-3.5 h-3.5 ${
                      rating >= star ? 'text-yellow-400 fill-yellow-400' : 'text-xn-textMuted hover:text-yellow-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-xn-border/60">
            <span className="text-[10px] font-semibold uppercase text-xn-textMuted">Color Label:</span>
            <div className="flex items-center space-x-1.5">
              {colorLabels.map((c) => (
                <button
                  key={c.name}
                  onClick={() => handleColorChange(c.hex)}
                  style={{ backgroundColor: c.hex }}
                  className={`w-3.5 h-3.5 rounded-full transition-transform ${
                    colorLabel === c.hex ? 'scale-125 ring-2 ring-white shadow' : 'opacity-70 hover:opacity-100'
                  }`}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Technical Camera & Shot Details */}
        <div className="space-y-2">
          <span className="text-[10px] font-semibold uppercase text-xn-textMuted flex items-center space-x-1">
            <Camera className="w-3.5 h-3.5 text-blue-400" />
            <span>Camera Data</span>
          </span>

          <div className="bg-xn-panel rounded border border-xn-border p-2 space-y-1.5 text-[11px]">
            <div className="flex justify-between">
              <span className="text-xn-textMuted">Camera:</span>
              <span className="text-xn-textBright font-medium truncate max-w-[140px]">
                {metadata?.camera_make !== 'Unknown' ? `${metadata?.camera_make} ${metadata?.camera_model}` : 'Not available'}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">Lens:</span>
              <span className="text-xn-textBright font-medium truncate max-w-[140px]">
                {metadata?.lens_model}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">Shutter:</span>
              <span className="text-xn-textBright font-medium">{metadata?.exposure_time}s</span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">Aperture:</span>
              <span className="text-xn-textBright font-medium">f/{metadata?.f_number}</span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">ISO:</span>
              <span className="text-xn-textBright font-medium">{metadata?.iso_speed}</span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">Focal Length:</span>
              <span className="text-xn-textBright font-medium">{metadata?.focal_length}mm</span>
            </div>

            <div className="flex justify-between">
              <span className="text-xn-textMuted">Date Taken:</span>
              <span className="text-xn-textBright font-medium truncate max-w-[140px]">{metadata?.date_taken}</span>
            </div>
          </div>
        </div>

        {/* GPS Coordinates & Map Link */}
        {metadata?.gps && metadata.gps.latitude_decimal && metadata.gps.longitude_decimal && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-semibold uppercase text-xn-textMuted flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5 text-red-400" />
              <span>GPS Location</span>
            </span>

            <div className="bg-xn-panel rounded border border-xn-border p-2 space-y-1 text-[11px]">
              <div className="font-mono text-xn-textBright">
                {metadata.gps.latitude_decimal}, {metadata.gps.longitude_decimal}
              </div>
              <a
                href={metadata.gps.maps_url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:text-blue-300 flex items-center space-x-1 text-[10px] mt-1"
              >
                <span>View on Google Maps</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        )}

        {/* Tags & Comments Editor */}
        <div className="space-y-2">
          <span className="text-[10px] font-semibold uppercase text-xn-textMuted flex items-center space-x-1">
            <Tag className="w-3.5 h-3.5 text-green-400" />
            <span>Tags & Notes</span>
          </span>

          <div className="space-y-2">
            <div>
              <label className="text-[10px] text-xn-textMuted mb-0.5 block">Keywords / Tags (comma separated):</label>
              <input
                type="text"
                placeholder="nature, travel, raw..."
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                onBlur={handleTagsBlur}
                className="w-full bg-xn-bg border border-xn-border rounded px-2 py-1 text-xs text-xn-textBright outline-none"
              />
            </div>

            <div>
              <label className="text-[10px] text-xn-textMuted mb-0.5 block">User Description & Comments:</label>
              <textarea
                rows={2}
                placeholder="Add notes..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                onBlur={handleCommentBlur}
                className="w-full bg-xn-bg border border-xn-border rounded p-1.5 text-xs text-xn-textBright outline-none resize-none"
              />
            </div>
          </div>
        </div>

        {/* Privacy: Strip Sensitive Metadata */}
        <div className="pt-2 border-t border-xn-border space-y-2">
          <button
            onClick={handleStripMetadata}
            disabled={isStripping}
            className="w-full py-1.5 px-2 bg-red-950/40 hover:bg-red-900/60 border border-red-800/80 rounded text-red-300 text-xs flex items-center justify-center space-x-1.5 transition"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-red-400" />
            <span>{isStripping ? 'Scrubbing...' : 'Strip Sensitive EXIF / GPS'}</span>
          </button>
          {strippedSuccess && (
            <p className="text-[10px] text-green-400 text-center">
              Clean copy created without metadata!
            </p>
          )}
        </div>

        {/* Collapsible Full EXIF Table */}
        {metadata?.all_exif && Object.keys(metadata.all_exif).length > 0 && (
          <div className="pt-2 border-t border-xn-border">
            <button
              onClick={() => setShowAllExif(!showAllExif)}
              className="w-full flex items-center justify-between text-[10px] uppercase font-semibold text-xn-textMuted hover:text-white"
            >
              <span>Raw EXIF Tags ({Object.keys(metadata.all_exif).length})</span>
              {showAllExif ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>

            {showAllExif && (
              <div className="mt-2 border border-xn-border rounded bg-xn-bg max-h-48 overflow-y-auto">
                <table className="w-full text-[10px] font-mono text-left">
                  <tbody className="divide-y divide-xn-border/40">
                    {Object.entries(metadata.all_exif).map(([k, v]) => (
                      <tr key={k} className="hover:bg-xn-hover">
                        <td className="p-1 text-xn-textMuted truncate max-w-[90px]">{k}</td>
                        <td className="p-1 text-xn-textBright truncate max-w-[130px]">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
