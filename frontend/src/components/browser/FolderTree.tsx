import React, { useEffect, useState } from 'react';
import { 
  Folder, 
  FolderGit2, 
  HardDrive, 
  Bookmark, 
  ChevronRight, 
  ChevronDown, 
  Image as ImageIcon, 
  Download, 
  Monitor, 
  Home, 
  FileText,
  FolderOpen
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { api } from '../../api/client';
import { PlaceItem } from '../../types';

export const FolderTree: React.FC = () => {
  const { 
    currentPath, 
    loadDirectory, 
    directoryContent, 
    favorites, 
    loadFavorites 
  } = useAppStore();

  const [places, setPlaces] = useState<PlaceItem[]>([]);
  const [drives, setDrives] = useState<PlaceItem[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadFavorites();
    api.getPlaces().then((res) => {
      setPlaces(res.places || []);
      setDrives(res.drives || []);
      // If currentPath is empty, initialize with Pictures or user Home
      if (!currentPath && res.places.length > 0) {
        loadDirectory(res.places[0].path);
      }
    }).catch(console.error);
  }, []);

  const getPlaceIcon = (iconName?: string) => {
    switch (iconName) {
      case 'image': return <ImageIcon className="w-3.5 h-3.5 text-blue-400" />;
      case 'download': return <Download className="w-3.5 h-3.5 text-green-400" />;
      case 'monitor': return <Monitor className="w-3.5 h-3.5 text-purple-400" />;
      case 'folder': return <FileText className="w-3.5 h-3.5 text-yellow-400" />;
      default: return <Home className="w-3.5 h-3.5 text-indigo-400" />;
    }
  };

  const toggleSubdirExpand = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedFolders(prev => ({ ...prev, [path]: !prev[path] }));
  };

  return (
    <aside className="w-60 bg-xn-surface border-r border-xn-border flex flex-col h-full overflow-hidden select-none text-xs">
      {/* Sidebar Header */}
      <div className="p-2 border-b border-xn-border/60 font-semibold text-xn-textBright uppercase tracking-wider text-[10px] flex items-center justify-between">
        <span>Folders & Navigation</span>
      </div>

      <div className="flex-1 overflow-y-auto p-1.5 space-y-3">
        {/* Quick Places Section */}
        <div>
          <div className="text-[10px] font-semibold text-xn-textMuted uppercase px-2 py-1">
            Places
          </div>
          <div className="space-y-0.5">
            {places.map((place) => {
              const isActive = currentPath.toLowerCase() === place.path.toLowerCase();
              return (
                <button
                  key={place.path}
                  onClick={() => loadDirectory(place.path)}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded transition text-left ${
                    isActive 
                      ? 'bg-xn-accent text-white font-medium' 
                      : 'text-xn-text hover:bg-xn-hover hover:text-xn-textBright'
                  }`}
                >
                  {getPlaceIcon(place.icon)}
                  <span className="truncate">{place.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Drives Section */}
        <div>
          <div className="text-[10px] font-semibold text-xn-textMuted uppercase px-2 py-1">
            Drives
          </div>
          <div className="space-y-0.5">
            {drives.map((drive) => {
              const isActive = currentPath.toLowerCase().startsWith(drive.path.toLowerCase());
              return (
                <button
                  key={drive.path}
                  onClick={() => loadDirectory(drive.path)}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded transition text-left ${
                    isActive 
                      ? 'bg-xn-hover text-xn-textBright font-medium' 
                      : 'text-xn-text hover:bg-xn-hover hover:text-xn-textBright'
                  }`}
                >
                  <HardDrive className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="truncate">{drive.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Favorites Section */}
        {favorites.length > 0 && (
          <div>
            <div className="text-[10px] font-semibold text-xn-textMuted uppercase px-2 py-1">
              Favorites
            </div>
            <div className="space-y-0.5">
              {favorites.map((fav) => {
                const isActive = currentPath.toLowerCase() === fav.toLowerCase();
                const folderName = fav.split(/[/\\]/).filter(Boolean).pop() || fav;
                return (
                  <button
                    key={fav}
                    onClick={() => loadDirectory(fav)}
                    className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded transition text-left ${
                      isActive 
                        ? 'bg-xn-accent text-white font-medium' 
                        : 'text-xn-text hover:bg-xn-hover hover:text-xn-textBright'
                    }`}
                  >
                    <Bookmark className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400 shrink-0" />
                    <span className="truncate" title={fav}>{folderName}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Current Subdirectories Tree */}
        {directoryContent && directoryContent.subdirectories.length > 0 && (
          <div>
            <div className="text-[10px] font-semibold text-xn-textMuted uppercase px-2 py-1 flex items-center justify-between">
              <span>Subfolders ({directoryContent.subdirectories.length})</span>
            </div>
            <div className="space-y-0.5 max-h-60 overflow-y-auto pl-1">
              {directoryContent.subdirectories.map((subdir) => {
                const isExpanded = !!expandedFolders[subdir.path];
                return (
                  <div key={subdir.path} className="flex flex-col">
                    <button
                      onClick={() => loadDirectory(subdir.path)}
                      className="w-full flex items-center space-x-1.5 px-2 py-1 rounded hover:bg-xn-hover text-xn-text hover:text-xn-textBright text-left transition group"
                    >
                      <Folder className="w-3.5 h-3.5 text-blue-400 shrink-0 group-hover:text-blue-300" />
                      <span className="truncate flex-1">{subdir.name}</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
