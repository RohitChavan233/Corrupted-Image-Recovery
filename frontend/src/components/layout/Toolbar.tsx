import React, { useState } from 'react';
import { 
  ArrowUp, 
  RotateCw, 
  Star, 
  Search, 
  SlidersHorizontal, 
  Sidebar as SidebarIcon, 
  PanelRight, 
  Film,
  ZoomIn,
  ZoomOut,
  Bookmark,
  BookmarkCheck,
  FolderOpen
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export const Toolbar: React.FC = () => {
  const { 
    currentPath, 
    directoryContent, 
    loadDirectory, 
    favorites, 
    toggleFavorite,
    thumbnailSize, 
    setThumbnailSize,
    sortField,
    sortOrder,
    setSort,
    filterRating,
    setFilterRating,
    filterColor,
    setFilterColor,
    filterQuery,
    setFilterQuery,
    sidebarVisible,
    toggleSidebar,
    metadataVisible,
    toggleMetadata,
    filmstripVisible,
    toggleFilmstrip,
    viewMode
  } = useAppStore();

  const [pathInput, setPathInput] = useState(currentPath);
  const [isEditingPath, setIsEditingPath] = useState(false);

  const isFav = favorites.includes(currentPath);

  const handleNavigateUp = () => {
    if (directoryContent?.parent_path) {
      loadDirectory(directoryContent.parent_path);
    }
  };

  const handleRefresh = () => {
    if (currentPath) {
      loadDirectory(currentPath);
    }
  };

  const handlePathSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pathInput.trim()) {
      loadDirectory(pathInput.trim());
      setIsEditingPath(false);
    }
  };

  const colorLabels = [
    { name: 'Red', color: '#ef4444' },
    { name: 'Yellow', color: '#eab308' },
    { name: 'Green', color: '#22c55e' },
    { name: 'Blue', color: '#3b82f6' },
    { name: 'Purple', color: '#a855f7' }
  ];

  return (
    <div className="h-9 bg-xn-panel border-b border-xn-border flex items-center justify-between px-3 text-xs z-20">
      {/* Left: Navigation & Path breadcrumb */}
      <div className="flex items-center space-x-1 flex-1 max-w-xl mr-4">
        <button
          onClick={handleNavigateUp}
          disabled={!directoryContent?.parent_path}
          title="Go to Parent Directory"
          className="p-1 rounded hover:bg-xn-hover disabled:opacity-30 disabled:hover:bg-transparent text-xn-textBright transition"
        >
          <ArrowUp className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={handleRefresh}
          title="Refresh Current Folder"
          className="p-1 rounded hover:bg-xn-hover text-xn-textBright transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => currentPath && toggleFavorite(currentPath)}
          disabled={!currentPath}
          title={isFav ? "Remove from Favorites" : "Add to Favorites"}
          className="p-1 rounded hover:bg-xn-hover text-xn-textBright transition"
        >
          {isFav ? (
            <BookmarkCheck className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
          ) : (
            <Bookmark className="w-3.5 h-3.5 text-xn-text" />
          )}
        </button>

        {/* Path Bar */}
        <div className="flex-1 min-w-0 ml-1">
          {isEditingPath ? (
            <form onSubmit={handlePathSubmit}>
              <input
                type="text"
                value={pathInput}
                onChange={(e) => setPathInput(e.target.value)}
                onBlur={() => setIsEditingPath(false)}
                autoFocus
                className="w-full bg-xn-bg border border-xn-accent rounded px-2 py-0.5 text-xs text-xn-textBright outline-none"
              />
            </form>
          ) : (
            <div 
              onClick={() => {
                setPathInput(currentPath);
                setIsEditingPath(true);
              }}
              className="bg-xn-bg/90 border border-xn-border hover:border-xn-accent/60 rounded px-2 py-0.5 text-xs text-xn-text truncate cursor-text flex items-center space-x-1.5 transition"
              title={currentPath}
            >
              <FolderOpen className="w-3 h-3 text-blue-400 shrink-0" />
              <span className="truncate">{currentPath || 'Select a folder...'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Center/Right: Browser Controls (Only shown in Browser & Viewer) */}
      {viewMode === 'browser' && (
        <div className="flex items-center space-x-3">
          {/* Thumbnail Size Slider */}
          <div className="flex items-center space-x-1.5 bg-xn-bg/70 px-2 py-0.5 rounded border border-xn-border">
            <ZoomOut className="w-3 h-3 text-xn-textMuted" />
            <input
              type="range"
              min="80"
              max="340"
              step="10"
              value={thumbnailSize}
              onChange={(e) => setThumbnailSize(Number(e.target.value))}
              className="w-20 accent-xn-accent cursor-pointer h-1.5 bg-xn-hover rounded-lg"
              title={`Thumbnail Size: ${thumbnailSize}px`}
            />
            <ZoomIn className="w-3 h-3 text-xn-textMuted" />
            <span className="text-[10px] text-xn-textMuted w-7 text-right">{thumbnailSize}p</span>
          </div>

          {/* Sort Controls */}
          <div className="flex items-center space-x-1 bg-xn-bg/70 px-2 py-0.5 rounded border border-xn-border">
            <SlidersHorizontal className="w-3 h-3 text-xn-textMuted" />
            <select
              value={sortField}
              onChange={(e) => setSort(e.target.value as any)}
              className="bg-transparent text-xs text-xn-textBright outline-none cursor-pointer"
            >
              <option value="name" className="bg-xn-surface">Name</option>
              <option value="mtime" className="bg-xn-surface">Date</option>
              <option value="size" className="bg-xn-surface">Size</option>
              <option value="ext" className="bg-xn-surface">Format</option>
              <option value="rating" className="bg-xn-surface">Rating</option>
            </select>
            <span className="text-[10px] text-xn-accent font-semibold">
              {sortOrder === 'asc' ? '↑' : '↓'}
            </span>
          </div>

          {/* Star Rating Filter */}
          <div className="flex items-center space-x-0.5 bg-xn-bg/70 px-1.5 py-0.5 rounded border border-xn-border">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setFilterRating(filterRating === star ? 0 : star)}
                title={`Filter >= ${star} stars`}
                className="p-0.5 hover:scale-110 transition"
              >
                <Star
                  className={`w-3 h-3 ${
                    filterRating >= star
                      ? 'text-yellow-400 fill-yellow-400'
                      : 'text-xn-textMuted hover:text-yellow-300'
                  }`}
                />
              </button>
            ))}
            {filterRating > 0 && (
              <button
                onClick={() => setFilterRating(0)}
                className="text-[9px] text-xn-textMuted hover:text-red-400 ml-1"
                title="Clear rating filter"
              >
                ✕
              </button>
            )}
          </div>

          {/* Color Label Filter */}
          <div className="flex items-center space-x-1 bg-xn-bg/70 px-1.5 py-0.5 rounded border border-xn-border">
            {colorLabels.map((c) => (
              <button
                key={c.name}
                onClick={() => setFilterColor(filterColor === c.name.toLowerCase() ? '' : c.name.toLowerCase())}
                style={{ backgroundColor: c.color }}
                title={`Filter by ${c.name} label`}
                className={`w-2.5 h-2.5 rounded-full transition-transform ${
                  filterColor === c.name.toLowerCase() ? 'scale-125 ring-2 ring-white' : 'opacity-60 hover:opacity-100'
                }`}
              />
            ))}
            {filterColor && (
              <button
                onClick={() => setFilterColor('')}
                className="text-[9px] text-xn-textMuted hover:text-red-400 ml-1"
                title="Clear color filter"
              >
                ✕
              </button>
            )}
          </div>

          {/* Search Query Input */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2 top-1.5 text-xn-textMuted" />
            <input
              type="text"
              placeholder="Filter filename..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="bg-xn-bg/90 border border-xn-border focus:border-xn-accent rounded pl-6 pr-2 py-0.5 text-xs text-xn-textBright outline-none w-32 focus:w-44 transition-all"
            />
            {filterQuery && (
              <button
                onClick={() => setFilterQuery('')}
                className="absolute right-1.5 top-1 text-[10px] text-xn-textMuted hover:text-xn-textBright"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      )}

      {/* Right: Panel Toggle Buttons */}
      <div className="flex items-center space-x-1 ml-3">
        <button
          onClick={toggleSidebar}
          title="Toggle Folder Tree Sidebar"
          className={`p-1 rounded border border-xn-border transition ${
            sidebarVisible ? 'bg-xn-hover text-xn-textBright' : 'text-xn-textMuted hover:bg-xn-hover'
          }`}
        >
          <SidebarIcon className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={toggleFilmstrip}
          title="Toggle Bottom Filmstrip"
          className={`p-1 rounded border border-xn-border transition ${
            filmstripVisible ? 'bg-xn-hover text-xn-textBright' : 'text-xn-textMuted hover:bg-xn-hover'
          }`}
        >
          <Film className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={toggleMetadata}
          title="Toggle Metadata Inspector"
          className={`p-1 rounded border border-xn-border transition ${
            metadataVisible ? 'bg-xn-hover text-xn-textBright' : 'text-xn-textMuted hover:bg-xn-hover'
          }`}
        >
          <PanelRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
