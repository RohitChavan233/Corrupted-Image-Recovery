export interface FileItem {
  name: string;
  path: string;
  size: number;
  mtime: number;
  ext: string;
  is_dir: boolean;
  width?: number | null;
  height?: number | null;
  format?: string | null;
  rating?: number;
  color_label?: string;
  tags?: string;
  is_corrupt?: number;
}

export interface DirectoryContent {
  current_path: string;
  parent_path: string | null;
  subdirectories: { name: string; path: string; is_dir: boolean }[];
  files: FileItem[];
  total_files: number;
  total_subdirs: number;
}

export interface PlaceItem {
  name: string;
  path: string;
  icon?: string;
  type?: string;
}

export interface PlacesResponse {
  places: PlaceItem[];
  drives: PlaceItem[];
}

export interface ExifData {
  filename: string;
  filepath: string;
  filesize: number;
  mtime: number;
  camera_make: string;
  camera_model: string;
  lens_model: string;
  date_taken: string;
  exposure_time: string;
  f_number: string;
  iso_speed: string;
  focal_length: string;
  software: string;
  artist_copyright: string;
  gps: {
    latitude_decimal?: number;
    longitude_decimal?: number;
    maps_url?: string;
    [key: string]: any;
  };
  all_exif: Record<string, string>;
  user_rating: number;
  color_label: string;
  user_tags: string;
  user_comment: string;
}

export interface JpegMarker {
  marker: string;
  name: string;
  offset: number;
  length: number;
}

export interface EmbeddedThumbnail {
  offset: number;
  size: number;
  width: number;
  height: number;
  format: string;
  preview_base64: string;
}

export interface DiagnosticIssueItem {
  code: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  offset?: number;
  length?: number;
  suggested_fix?: string;
}

export interface JpegAnalysis {
  filepath: string;
  filename: string;
  file_size: number;
  image_format?: string;
  is_corrupt: boolean;
  integrity_score: number;
  has_soi: boolean;
  has_eoi: boolean;
  has_dqt: boolean;
  has_sof: boolean;
  has_sos: boolean;
  has_app1: boolean;
  sos_offset: number;
  markers: JpegMarker[];
  issues: (string | DiagnosticIssueItem)[];
  decode_success: boolean;
  decode_partial: boolean;
  decoded_width: number;
  decoded_height: number;
  decode_error: string | null;
  embedded_thumbnail_count: number;
  embedded_thumbnails: EmbeddedThumbnail[];
  recoverable: boolean;
  available_repairs?: string[];
}

export interface RecoveredArtifact {
  method: string;
  filename: string;
  filepath: string;
  width: number;
  height: number;
  size: number;
  preview_base64: string | null;
  description: string;
}

export interface RecoveryExecutionResult {
  original_file: string;
  analysis: JpegAnalysis;
  recovered_count: number;
  recovered_files: RecoveredArtifact[];
  message: string;
}

export interface BatchItemResult {
  original: string;
  output?: string;
  status: 'success' | 'error';
  width?: number;
  height?: number;
  size?: number;
  error?: string;
}

export interface BatchStatus {
  job_id: string;
  total: number;
  completed: number;
  failed: number;
  is_cancelled: boolean;
  status: 'in_progress' | 'completed' | 'cancelled' | 'cancelling';
  results: BatchItemResult[];
}

export interface DuplicateCluster {
  cluster_id: number;
  count: number;
  items: {
    filepath: string;
    filename: string;
    size: number;
    dhash: string;
    sha256: string;
    similarity?: number;
  }[];
}

export interface BatchRecoveryScanResponse {
  total_scanned: number;
  corrupt_count: number;
  recoverable_count: number;
  results: JpegAnalysis[];
}

export interface BatchRecoveryExecuteResponse {
  total_files_processed: number;
  total_recovered_artifacts: number;
  output_dir: string;
  results: RecoveryExecutionResult[];
}

export type ViewMode = 
  | 'browser'      // Thumbnail grid + filmstrip + folder tree
  | 'viewer'       // Advanced single image viewer with deep pan/zoom
  | 'compare'      // Side-by-side synchronized comparison
  | 'editor'       // Non-destructive photo editor
  | 'recovery'     // Corrupted JPEG inspection & thumbnail carving
  | 'batch'        // Batch conversion, resizing, renaming
  | 'duplicates';  // Visual and binary duplicate finder
