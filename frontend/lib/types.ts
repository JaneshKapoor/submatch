export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_step: string;
  steps_completed: string[];
  error?: string | null;
  created_at: string;
  source: string;
}

export interface SegmentResult {
  index: number;
  start: number;
  end: number;
  timestamp_label: string;
  audio_text: string;
  subtitle_text: string;
  normalized_audio: string;
  normalized_subtitle: string;
  score: number;
  word_count_audio: number;
  word_count_subtitle: number;
  word_count_delta: number;
  status: "OK" | "MARGINAL" | "REVIEW" | "MISSING";
  has_subtitle: boolean;
}

export interface ReportStats {
  total: number;
  ok: number;
  marginal: number;
  review: number;
  missing: number;
  flagged: number;
  avg_score: number;
  match_rate: number;
}

export interface ReportData {
  stats: ReportStats;
  segments: SegmentResult[];
  video_url: string;
  generated_at: string;
  report_path: string;
}

export interface Language {
  code: string;
  name: string;
}

export type FilterStatus = "all" | "REVIEW" | "MARGINAL" | "OK" | "MISSING";
