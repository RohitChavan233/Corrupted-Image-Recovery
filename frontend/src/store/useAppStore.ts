import { create } from 'zustand';
import { FileItem, DirectoryContent, ViewMode } from '../types';
import { api } from '../api/client';

interface AppState {
  // Navigation & Directory
  currentPath: string;
  directoryContent: DirectoryContent | null;
  isLoadingDirectory: boolean;
  directoryError: string | null;
  favorites: string[];

  // Selection & Active Item
  selectedFiles: FileItem[];
  activeFile: FileItem | null;

  // View Mode & Layout
  viewMode: ViewMode;
  previousViewMode: ViewMode;
  thumbnailSize: number;
  sidebarVisible: boolean;
  metadataVisible: boolean;
  filmstripVisible: boolean;

  // Sorting & Filtering
  sortField: 'name' | 'mtime' | 'size' | 'ext' | 'rating';
  sortOrder: 'asc' | 'desc';
  filterRating: number;
  filterColor: string;
  filterQuery: string;

  // Viewer Pan & Zoom State
  zoomLevel: number;
  panOffset: { x: number; y: number };
  fitMode: 'fit' | 'fill' | 'actual';
  rotation: number;
  flipH: boolean;
  flipV: boolean;

  // Slideshow
  isSlideshowActive: boolean;
  slideshowInterval: number; // seconds

  // Actions
  loadDirectory: (path: string) => Promise<void>;
  loadFavorites: () => Promise<void>;
  toggleFavorite: (path: string) => Promise<void>;
  setSelectedFiles: (files: FileItem[]) => void;
  toggleSelectFile: (file: FileItem, multiSelect?: boolean) => void;
  setActiveFile: (file: FileItem | null) => void;
  nextImage: () => void;
  prevImage: () => void;
  setViewMode: (mode: ViewMode) => void;
  setThumbnailSize: (size: number) => void;
  toggleSidebar: () => void;
  toggleMetadata: () => void;
  toggleFilmstrip: () => void;
  setSort: (field: 'name' | 'mtime' | 'size' | 'ext' | 'rating') => void;
  setFilterRating: (rating: number) => void;
  setFilterColor: (color: string) => void;
  setFilterQuery: (query: string) => void;
  setZoomLevel: (zoom: number) => void;
  setPanOffset: (offset: { x: number; y: number }) => void;
  resetTransform: () => void;
  rotateClockwise: () => void;
  toggleFlipH: () => void;
  toggleFlipV: () => void;
  startSlideshow: () => void;
  stopSlideshow: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  currentPath: '',
  directoryContent: null,
  isLoadingDirectory: false,
  directoryError: null,
  favorites: [],

  selectedFiles: [],
  activeFile: null,

  viewMode: 'browser',
  previousViewMode: 'browser',
  thumbnailSize: 160,
  sidebarVisible: true,
  metadataVisible: true,
  filmstripVisible: true,

  sortField: 'name',
  sortOrder: 'asc',
  filterRating: 0,
  filterColor: '',
  filterQuery: '',

  zoomLevel: 1.0,
  panOffset: { x: 0, y: 0 },
  fitMode: 'fit',
  rotation: 0,
  flipH: false,
  flipV: false,

  isSlideshowActive: false,
  slideshowInterval: 3,

  loadDirectory: async (path: string) => {
    set({ isLoadingDirectory: true, directoryError: null });
    try {
      const data = await api.browse(path);
      const prevActive = get().activeFile;
      // Keep active file if it exists in new directory, otherwise pick first
      const newActive = data.files.find(f => f.path === prevActive?.path) || data.files[0] || null;
      set({
        currentPath: data.current_path,
        directoryContent: data,
        isLoadingDirectory: false,
        activeFile: newActive,
        selectedFiles: newActive ? [newActive] : []
      });
    } catch (err: any) {
      set({
        isLoadingDirectory: false,
        directoryError: err.message || 'Failed to open folder'
      });
    }
  },

  loadFavorites: async () => {
    try {
      const favs = await api.getFavorites();
      set({ favorites: favs });
    } catch (e) {
      console.error(e);
    }
  },

  toggleFavorite: async (path: string) => {
    const { favorites } = get();
    if (favorites.includes(path)) {
      const updated = await api.removeFavorite(path);
      set({ favorites: updated });
    } else {
      const updated = await api.addFavorite(path);
      set({ favorites: updated });
    }
  },

  setSelectedFiles: (files) => set({ selectedFiles: files }),

  toggleSelectFile: (file, multiSelect = false) => {
    const { selectedFiles } = get();
    if (!multiSelect) {
      set({ selectedFiles: [file], activeFile: file });
      return;
    }
    const exists = selectedFiles.some(f => f.path === file.path);
    if (exists) {
      const updated = selectedFiles.filter(f => f.path !== file.path);
      set({ selectedFiles: updated, activeFile: updated[0] || null });
    } else {
      set({ selectedFiles: [...selectedFiles, file], activeFile: file });
    }
  },

  setActiveFile: (file) => {
    set({ activeFile: file });
    get().resetTransform();
  },

  nextImage: () => {
    const { directoryContent, activeFile } = get();
    if (!directoryContent || !activeFile || directoryContent.files.length === 0) return;
    const idx = directoryContent.files.findIndex(f => f.path === activeFile.path);
    const nextIdx = (idx + 1) % directoryContent.files.length;
    const nextFile = directoryContent.files[nextIdx];
    set({ activeFile: nextFile, selectedFiles: [nextFile] });
    get().resetTransform();
  },

  prevImage: () => {
    const { directoryContent, activeFile } = get();
    if (!directoryContent || !activeFile || directoryContent.files.length === 0) return;
    const idx = directoryContent.files.findIndex(f => f.path === activeFile.path);
    const prevIdx = (idx - 1 + directoryContent.files.length) % directoryContent.files.length;
    const prevFile = directoryContent.files[prevIdx];
    set({ activeFile: prevFile, selectedFiles: [prevFile] });
    get().resetTransform();
  },

  setViewMode: (mode) => {
    set((state) => ({
      previousViewMode: state.viewMode,
      viewMode: mode
    }));
    get().resetTransform();
  },

  setThumbnailSize: (size) => set({ thumbnailSize: size }),
  toggleSidebar: () => set(s => ({ sidebarVisible: !s.sidebarVisible })),
  toggleMetadata: () => set(s => ({ metadataVisible: !s.metadataVisible })),
  toggleFilmstrip: () => set(s => ({ filmstripVisible: !s.filmstripVisible })),

  setSort: (field) => {
    set(state => ({
      sortField: field,
      sortOrder: state.sortField === field && state.sortOrder === 'asc' ? 'desc' : 'asc'
    }));
  },

  setFilterRating: (rating) => set({ filterRating: rating }),
  setFilterColor: (color) => set({ filterColor: color }),
  setFilterQuery: (query) => set({ filterQuery: query }),

  setZoomLevel: (zoom) => set({ zoomLevel: Math.max(0.05, Math.min(15, zoom)) }),
  setPanOffset: (offset) => set({ panOffset: offset }),

  resetTransform: () => set({
    zoomLevel: 1.0,
    panOffset: { x: 0, y: 0 },
    fitMode: 'fit',
    rotation: 0,
    flipH: false,
    flipV: false
  }),

  rotateClockwise: () => set(s => ({ rotation: (s.rotation + 90) % 360 })),
  toggleFlipH: () => set(s => ({ flipH: !s.flipH })),
  toggleFlipV: () => set(s => ({ flipV: !s.flipV })),

  startSlideshow: () => set({ isSlideshowActive: true, viewMode: 'viewer' }),
  stopSlideshow: () => set({ isSlideshowActive: false })
}));
