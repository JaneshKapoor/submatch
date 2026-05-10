"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  CheckCircle2, XCircle, Download, ExternalLink,
  Loader2, ChevronLeft, FileVideo, AudioLines,
  Subtitles, BarChart3, FileText,
} from "lucide-react";
import { AuroraBackground } from "@/components/ui/aurora-background";
import { Button } from "@/components/ui/button";
import { createJobWebSocket, getReportHtmlUrl } from "@/lib/api";
import { Job } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS = [
  { key: "Download / Upload",       icon: <FileVideo className="w-4 h-4" />,   label: "Download / Upload" },
  { key: "Audio Transcription",     icon: <AudioLines className="w-4 h-4" />,  label: "Audio Transcription" },
  { key: "Subtitle Extraction",     icon: <Subtitles className="w-4 h-4" />,   label: "Subtitle Extraction" },
  { key: "Mismatch Detection",      icon: <BarChart3 className="w-4 h-4" />,   label: "Mismatch Detection" },
  { key: "Report Generation",       icon: <FileText className="w-4 h-4" />,    label: "Report Generation" },
];

export default function AnalyzePage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<Partial<Job>>({
    status: "pending", progress: 0,
    current_step: "Connecting to backend…", steps_completed: [],
  });
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) return;

    wsRef.current = createJobWebSocket(jobId, (data) => {
      setJob((p) => ({ ...p, ...data }));
      if (data.status === "completed") setTimeout(() => router.push(`/report/${jobId}`), 1500);
    }, startPolling);

    return () => {
      wsRef.current?.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId]);

  function startPolling() {
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`http://localhost:8000/api/jobs/${jobId}`);
        if (!r.ok) return;
        const data: Partial<Job> = await r.json();
        setJob((p) => ({ ...p, ...data }));
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(pollRef.current!);
          if (data.status === "completed") setTimeout(() => router.push(`/report/${jobId}`), 1500);
        }
      } catch { clearInterval(pollRef.current!); }
    }, 2500);
  }

  const progress = job.progress ?? 0;
  const isFailed = job.status === "failed";
  const isCompleted = job.status === "completed";

  // Circumference for the circle
  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const dash = circ - (progress / 100) * circ;

  return (
    <AuroraBackground>
      {/* Nav */}
      <nav className="border-b border-white/5 bg-black/10 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3">
          <button onClick={() => router.push("/")} className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm">
            <ChevronLeft className="w-4 h-4" />
            Home
          </button>
          <span className="text-white/20">|</span>
          <div className="w-6 h-6 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-md flex items-center justify-center">
            <span className="text-white font-black text-xs">S</span>
          </div>
          <span className="text-sm font-semibold text-white">SubMatch</span>
          <span className="text-white/20">·</span>
          <span className="text-sm text-slate-400">Analyzing…</span>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-16 flex flex-col items-center gap-8 animate-fade-up">

        {/* Circular progress */}
        <div className="relative w-36 h-36">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            {/* Track */}
            <circle cx="60" cy="60" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            {/* Progress arc */}
            <circle
              cx="60" cy="60" r={radius} fill="none"
              stroke={isFailed ? "#ef4444" : isCompleted ? "#10b981" : "url(#grad)"}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={dash}
              style={{ transition: "stroke-dashoffset 0.6s ease" }}
            />
            <defs>
              <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#7c3aed" />
                <stop offset="100%" stopColor="#4f46e5" />
              </linearGradient>
            </defs>
          </svg>
          {/* Center content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {isFailed ? (
              <XCircle className="w-8 h-8 text-red-400" />
            ) : isCompleted ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            ) : (
              <>
                <span className="text-2xl font-black text-white tabular-nums">{progress}%</span>
                <span className="text-[10px] text-slate-500 mt-0.5">processing</span>
              </>
            )}
          </div>
        </div>

        {/* Status text */}
        <div className="text-center">
          {isFailed ? (
            <>
              <h2 className="text-2xl font-bold text-white mb-2">Analysis Failed</h2>
              <p className="text-red-300 text-sm max-w-sm">{job.error || "An unexpected error occurred."}</p>
            </>
          ) : isCompleted ? (
            <>
              <h2 className="text-2xl font-bold text-white mb-2">Analysis Complete!</h2>
              <p className="text-slate-400 text-sm">Redirecting to your report…</p>
            </>
          ) : (
            <>
              <h2 className="text-xl font-bold text-white mb-2">Analyzing Video</h2>
              <p className="text-slate-400 text-sm animate-pulse">{job.current_step}</p>
            </>
          )}
        </div>

        {/* Pipeline steps */}
        <div className="w-full glass-bright rounded-2xl border border-white/8 p-5 space-y-1">
          {STEPS.map((step, i) => {
            const completed = job.steps_completed?.includes(step.key);
            const isActive = !completed && !isFailed && !isCompleted &&
              job.current_step?.toLowerCase().includes(step.key.split(" ")[0].toLowerCase());

            return (
              <div key={step.key} className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300",
                completed && "bg-emerald-500/5",
                isActive && "bg-violet-500/8",
              )}>
                {/* Status indicator */}
                <div className={cn(
                  "w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300",
                  completed ? "bg-emerald-500/20 text-emerald-400" :
                  isActive   ? "bg-violet-500/20 text-violet-400" :
                               "bg-white/5 text-slate-600"
                )}>
                  {completed ? <CheckCircle2 className="w-4 h-4" /> :
                   isActive  ? <Loader2 className="w-4 h-4 animate-spin" /> :
                               step.icon}
                </div>

                <span className={cn(
                  "text-sm font-medium transition-colors",
                  completed ? "text-emerald-300" :
                  isActive   ? "text-violet-300" :
                               "text-slate-600"
                )}>
                  {step.label}
                </span>

                {completed && <span className="ml-auto text-xs text-emerald-500/70">✓ Done</span>}
                {isActive  && <span className="ml-auto text-xs text-violet-400 animate-pulse">Running…</span>}
              </div>
            );
          })}
        </div>

        {/* Action buttons */}
        {(isCompleted || isFailed) && (
          <div className="flex gap-3 w-full animate-fade-in">
            {isCompleted && (
              <>
                <Button
                  className="flex-1"
                  onClick={() => router.push(`/report/${jobId}`)}
                >
                  <ExternalLink className="w-4 h-4" />
                  View Report
                </Button>
                <a
                  href={getReportHtmlUrl(jobId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Button variant="secondary" size="md">
                    <Download className="w-4 h-4" />
                    HTML
                  </Button>
                </a>
              </>
            )}
            {isFailed && (
              <Button variant="secondary" className="flex-1" onClick={() => router.push("/")}>
                Try Again
              </Button>
            )}
          </div>
        )}

        <p className="text-xs text-slate-700 font-mono">job/{jobId}</p>
      </div>
    </AuroraBackground>
  );
}
