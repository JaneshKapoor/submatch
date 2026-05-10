import { Job, Language, ReportData } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = BASE_URL.replace(/^http/, "ws");

export interface AnalyzePayload {
  url: string;
  source_language: string;
  subtitle_language: string;
  whisper_model: string;
  similarity_threshold: number;
  use_ocr_fallback: boolean;
}

export interface UploadPayload {
  video: File;
  subtitle?: File;
  source_language: string;
  subtitle_language: string;
  whisper_model: string;
  similarity_threshold: number;
  use_ocr_fallback: boolean;
}

export async function startAnalysis(payload: AnalyzePayload): Promise<{ job_id: string }> {
  const res = await fetch(`${BASE_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || `Server error: ${res.status}`);
  }
  return res.json();
}

export async function uploadVideo(payload: UploadPayload): Promise<{ job_id: string }> {
  const form = new FormData();
  form.append("video", payload.video);
  if (payload.subtitle) form.append("subtitle_file", payload.subtitle);
  form.append("source_language", payload.source_language);
  form.append("subtitle_language", payload.subtitle_language);
  form.append("whisper_model", payload.whisper_model);
  form.append("similarity_threshold", String(payload.similarity_threshold));
  form.append("use_ocr_fallback", String(payload.use_ocr_fallback));

  const res = await fetch(`${BASE_URL}/api/jobs/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || `Upload error: ${res.status}`);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`${BASE_URL}/api/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job not found: ${jobId}`);
  return res.json();
}

export async function getReport(jobId: string): Promise<ReportData> {
  const res = await fetch(`${BASE_URL}/api/jobs/${jobId}/report`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || "Failed to fetch report");
  }
  return res.json();
}

export function getReportHtmlUrl(jobId: string): string {
  return `${BASE_URL}/api/jobs/${jobId}/report.html`;
}

export async function getLanguages(): Promise<Language[]> {
  const res = await fetch(`${BASE_URL}/api/languages`).catch(() => null);
  if (!res?.ok) return [];
  return res.json();
}

export function createJobWebSocket(
  jobId: string,
  onMessage: (job: Partial<Job>) => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/${jobId}`);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch { /* ignore */ }
  };
  ws.onclose = () => onClose?.();
  ws.onerror = () => ws.close();
  return ws;
}
