import { 
  PlacesResponse, 
  DirectoryContent, 
  ExifData, 
  JpegAnalysis, 
  RecoveryExecutionResult,
  BatchStatus,
  DuplicateCluster,
  BatchRecoveryScanResponse,
  BatchRecoveryExecuteResponse
} from '../types';

const API_BASE = '/api';

export const api = {
  // Places & Drives
  getPlaces: async (): Promise<PlacesResponse> => {
    const res = await fetch(`${API_BASE}/filesystem/places`);
    if (!res.ok) throw new Error('Failed to fetch places');
    return res.json();
  },

  // Directory Browse
  browse: async (folderPath: string): Promise<DirectoryContent> => {
    const res = await fetch(`${API_BASE}/filesystem/browse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to browse folder' }));
      throw new Error(err.detail || 'Failed to browse folder');
    }
    return res.json();
  },

  // Favorites
  getFavorites: async (): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/filesystem/favorites`);
    if (!res.ok) throw new Error('Failed to fetch favorites');
    const data = await res.json();
    return data.favorites;
  },

  addFavorite: async (folderPath: string): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/filesystem/favorites/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath }),
    });
    const data = await res.json();
    return data.favorites;
  },

  removeFavorite: async (folderPath: string): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/filesystem/favorites/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath }),
    });
    const data = await res.json();
    return data.favorites;
  },

  revealInExplorer: async (path: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/filesystem/reveal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: path }),
      });
      const data = await res.json();
      return !!data.success;
    } catch {
      return false;
    }
  },

  // Image URLs
  getThumbnailUrl: (path: string, size: number = 256): string => {
    return `${API_BASE}/images/thumbnail?path=${encodeURIComponent(path)}&size=${size}`;
  },

  getRawImageUrl: (path: string): string => {
    return `${API_BASE}/images/raw?path=${encodeURIComponent(path)}`;
  },

  // Metadata
  getMetadata: async (path: string): Promise<ExifData> => {
    const res = await fetch(`${API_BASE}/metadata?path=${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error('Failed to fetch metadata');
    return res.json();
  },

  updateAnnotations: async (params: {
    filepath: string;
    rating?: number;
    color_label?: string;
    tags?: string;
    comment?: string;
  }): Promise<ExifData> => {
    const res = await fetch(`${API_BASE}/metadata/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Failed to update annotations');
    return res.json();
  },

  stripMetadata: async (filepath: string, outputPath?: string): Promise<{ success: boolean; saved_path: string }> => {
    const res = await fetch(`${API_BASE}/metadata/strip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath, output_path: outputPath }),
    });
    if (!res.ok) throw new Error('Failed to strip metadata');
    return res.json();
  },

  // JPEG Recovery & Inspection
  inspectJpeg: async (filepath: string): Promise<JpegAnalysis> => {
    const res = await fetch(`${API_BASE}/recovery/inspect?path=${encodeURIComponent(filepath)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to inspect JPEG' }));
      throw new Error(err.detail || 'Failed to inspect JPEG');
    }
    return res.json();
  },

  executeRecovery: async (filepath: string, recoveryType: string = 'auto'): Promise<RecoveryExecutionResult> => {
    const res = await fetch(`${API_BASE}/recovery/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filepath, recovery_type: recoveryType }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to execute recovery' }));
      throw new Error(err.detail || 'Failed to execute recovery');
    }
    return res.json();
  },

  batchScanCorrupted: async (params: { folder_path?: string; file_list?: string[] }): Promise<BatchRecoveryScanResponse> => {
    const res = await fetch(`${API_BASE}/recovery/batch-scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Batch scan failed');
    return res.json();
  },

  batchExecuteRecovery: async (params: { file_list: string[]; recovery_type?: string; output_dir?: string }): Promise<BatchRecoveryExecuteResponse> => {
    const res = await fetch(`${API_BASE}/recovery/batch-execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Batch recovery failed');
    return res.json();
  },

  // Process & Edit Image
  processImage: async (params: any): Promise<{ success: boolean; saved_to?: string; blob?: Blob }> => {
    const res = await fetch(`${API_BASE}/images/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Processing failed' }));
      throw new Error(err.detail || 'Processing failed');
    }
    if (params.save_as) {
      return res.json();
    }
    const blob = await res.blob();
    return { success: true, blob };
  },

  // Batch Processing
  startBatch: async (params: any): Promise<{ job_id: string; status: string }> => {
    const res = await fetch(`${API_BASE}/batch/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Failed to start batch job');
    return res.json();
  },

  getBatchStatus: async (jobId: string): Promise<BatchStatus> => {
    const res = await fetch(`${API_BASE}/batch/status/${jobId}`);
    if (!res.ok) throw new Error('Failed to get batch status');
    return res.json();
  },

  cancelBatch: async (jobId: string): Promise<{ success: boolean }> => {
    const res = await fetch(`${API_BASE}/batch/cancel/${jobId}`, { method: 'POST' });
    return res.json();
  },

  // Duplicates
  scanDuplicates: async (folderPath: string, threshold: number = 0.90): Promise<{ clusters: DuplicateCluster[]; total_clusters: number }> => {
    const res = await fetch(`${API_BASE}/duplicates/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath, similarity_threshold: threshold }),
    });
    if (!res.ok) throw new Error('Failed to scan duplicates');
    return res.json();
  },

  // Screenshot
  captureScreenshot: async (targetFolder?: string): Promise<{ success: boolean; screenshot: any }> => {
    const res = await fetch(`${API_BASE}/screenshot/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_folder: targetFolder || '' }),
    });
    if (!res.ok) throw new Error('Failed to capture screenshot');
    return res.json();
  }
};
