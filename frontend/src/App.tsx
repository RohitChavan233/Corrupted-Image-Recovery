import React from 'react';
import { useAppStore } from './store/useAppStore';
import { Header } from './components/layout/Header';
import { Toolbar } from './components/layout/Toolbar';
import { StatusBar } from './components/layout/StatusBar';
import { FolderTree } from './components/browser/FolderTree';
import { ThumbnailGrid } from './components/browser/ThumbnailGrid';
import { Filmstrip } from './components/browser/Filmstrip';
import { ImageViewer } from './components/viewer/ImageViewer';
import { CompareViewer } from './components/viewer/CompareViewer';
import { ImageEditor } from './components/editor/ImageEditor';
import { RecoveryStudio } from './components/recovery/RecoveryStudio';
import { BatchStudio } from './components/batch/BatchStudio';
import { DuplicateFinder } from './components/duplicates/DuplicateFinder';
import { MetadataPanel } from './components/metadata/MetadataPanel';
import { Slideshow } from './components/viewer/Slideshow';

export const App: React.FC = () => {
  const { 
    viewMode, 
    sidebarVisible, 
    metadataVisible,
    filmstripVisible
  } = useAppStore();

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-xn-bg text-xn-text font-sans select-none">
      {/* 1. Header */}
      <Header />

      {/* 2. Toolbar */}
      <Toolbar />

      {/* 3. Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Folder Navigation */}
        {sidebarVisible && viewMode === 'browser' && <FolderTree />}

        {/* Center Canvas / Views */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {viewMode === 'browser' && (
            <>
              <ThumbnailGrid />
              {filmstripVisible && <Filmstrip />}
            </>
          )}

          {viewMode === 'viewer' && (
            <>
              <ImageViewer />
              {filmstripVisible && <Filmstrip />}
            </>
          )}

          {viewMode === 'compare' && <CompareViewer />}

          {viewMode === 'editor' && <ImageEditor />}

          {viewMode === 'recovery' && <RecoveryStudio />}

          {viewMode === 'batch' && <BatchStudio />}

          {viewMode === 'duplicates' && <DuplicateFinder />}
        </main>

        {/* Right Panel: Metadata & EXIF Inspector */}
        {metadataVisible && (viewMode === 'browser' || viewMode === 'viewer') && (
          <MetadataPanel />
        )}
      </div>

      {/* 4. Bottom Status Bar */}
      <StatusBar />

      {/* 5. Slideshow Overlay */}
      <Slideshow />
    </div>
  );
};
