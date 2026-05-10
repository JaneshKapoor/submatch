"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Youtube, Upload, Wand2, Globe, Zap, FileText,
  ChevronRight, AlertTriangle, ArrowRight, Github,
  AudioLines, FileVideo, Subtitles, BarChart3,
} from "lucide-react";
import { AuroraBackground } from "@/components/ui/aurora-background";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { startAnalysis, uploadVideo } from "@/lib/api";

const WHISPER_MODELS = [
  { value: "tiny",     label: "Tiny",    desc: "~1min" },
  { value: "base",     label: "Base",    desc: "~2min" },
  { value: "small",    label: "Small",   desc: "~5min" },
  { value: "medium",   label: "Medium",  desc: "~10min", recommended: true },
  { value: "large-v3", label: "Large",   desc: "~20min" },
];

const LANGUAGES = [
  { code: "auto", label: "Auto-detect" },
  { code: "hi",   label: "Hindi (हिन्दी)" },
  { code: "kn",   label: "Kannada (ಕನ್ನಡ)" },
  { code: "en",   label: "English" },
  { code: "ta",   label: "Tamil (தமிழ்)" },
  { code: "te",   label: "Telugu (తెలుగు)" },
  { code: "mr",   label: "Marathi (मराठी)" },
  { code: "bn",   label: "Bengali (বাংলা)" },
  { code: "gu",   label: "Gujarati (ગુજરાતી)" },
  { code: "ml",   label: "Malayalam (മലയാളം)" },
  { code: "pa",   label: "Punjabi (ਪੰਜਾਬੀ)" },
];

const PIPELINE_STEPS = [
  { icon: <FileVideo className="w-4 h-4" />,  label: "Video Input",          desc: "YouTube URL or direct upload" },
  { icon: <AudioLines className="w-4 h-4" />, label: "Whisper Transcription", desc: "OpenAI Whisper ASR" },
  { icon: <Subtitles className="w-4 h-4" />,  label: "Subtitle Extraction",   desc: "VTT/SRT parse or OCR" },
  { icon: <BarChart3 className="w-4 h-4" />,  label: "Mismatch Detection",    desc: "rapidfuzz + word-count scoring" },
  { icon: <FileText className="w-4 h-4" />,   label: "Report Generation",     desc: "Interactive HTML report" },
];

type TabId = "youtube" | "upload";

export default function HomePage() {
  const router = useRouter();

  // Shared settings
  const [tab, setTab] = useState<TabId>("youtube");
  const [audioLang, setAudioLang] = useState("auto");
  const [subtitleLang, setSubtitleLang] = useState("hi");
  const [whisperModel, setWhisperModel] = useState("medium");
  const [threshold, setThreshold] = useState(0.75);
  const [useOcr, setUseOcr] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // YouTube tab
  const [url, setUrl] = useState("");

  // Upload tab
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const subInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) setVideoFile(file);
    else setError("Please drop a valid video file.");
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (tab === "youtube" && !url.trim()) { setError("Please enter a YouTube URL."); return; }
    if (tab === "upload" && !videoFile) { setError("Please select a video file."); return; }

    setLoading(true);
    try {
      let job_id: string;
      const common = { source_language: audioLang, subtitle_language: subtitleLang, whisper_model: whisperModel, similarity_threshold: threshold, use_ocr_fallback: useOcr };

      if (tab === "youtube") {
        ({ job_id } = await startAnalysis({ url: url.trim(), ...common }));
      } else {
        ({ job_id } = await uploadVideo({ video: videoFile!, subtitle: subtitleFile || undefined, ...common }));
      }
      router.push(`/analyze/${job_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start. Is the backend running on port 8000?");
      setLoading(false);
    }
  }

  return (
    <AuroraBackground>
      {/* Nav */}
      <nav className="border-b border-white/5 backdrop-blur-sm bg-black/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo mark */}
            <div className="relative w-8 h-8">
              <div className="absolute inset-0 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg blur-[6px] opacity-60" />
              <div className="relative w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-black text-sm tracking-tight">S</span>
              </div>
            </div>
            <span className="font-bold text-lg text-white tracking-tight">
              Sub<span className="gradient-text">Match</span>
            </span>
            <span className="hidden sm:block text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/20 font-medium">
              v2.0
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden md:flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              PlanetRead Open Source
            </span>
            <a
              href="https://github.com/JaneshKapoor/submatch"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors"
            >
              <Github className="w-4 h-4" />
              <span className="hidden sm:block">GitHub</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Hero section */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-10">
        <div className="text-center max-w-4xl mx-auto mb-16 animate-fade-up">
          {/* Eyebrow pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-300 text-xs font-semibold mb-6 tracking-wide uppercase">
            <Zap className="w-3 h-3" />
            Whisper · Indic Languages · OCR · rapidfuzz
          </div>

          <h1 className="text-5xl sm:text-6xl font-black text-white leading-[1.1] mb-6 tracking-tight">
            Find subtitle
            <br />
            <span className="shimmer-text">mismatches</span> instantly
          </h1>

          <p className="text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
            SubMatch compares what is <em className="text-slate-300 not-italic">spoken</em> against what is{" "}
            <em className="text-slate-300 not-italic">shown</em> — frame-accurate, language-aware,
            with full support for Hindi, Kannada, and 8 other Indic scripts.
          </p>
        </div>

        {/* Main form card */}
        <div className="max-w-2xl mx-auto animate-fade-up" style={{ animationDelay: "0.1s" }}>
          <div className="glass-bright rounded-2xl shadow-2xl shadow-black/50 overflow-hidden border border-white/8">
            {/* Tab bar */}
            <div className="flex border-b border-white/6 bg-black/20">
              {[
                { id: "youtube" as TabId, icon: <Youtube className="w-4 h-4" />, label: "YouTube URL" },
                { id: "upload"  as TabId, icon: <Upload   className="w-4 h-4" />, label: "Upload Video" },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => { setTab(t.id); setError(""); }}
                  className={cn(
                    "flex-1 flex items-center justify-center gap-2 py-3.5 text-sm font-semibold transition-all duration-200",
                    tab === t.id
                      ? "text-violet-300 border-b-2 border-violet-500 bg-violet-500/5"
                      : "text-slate-500 hover:text-slate-300"
                  )}
                >
                  {t.icon}
                  {t.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* YouTube tab */}
              {tab === "youtube" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
                    Video URL
                  </label>
                  <div className="relative">
                    <Youtube className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-red-400/80" />
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://www.youtube.com/watch?v=..."
                      className="w-full pl-10 pr-4 py-3 bg-black/30 border border-white/10 rounded-xl text-slate-200 placeholder-slate-600 text-sm font-mono focus:outline-none focus:border-violet-500/60 focus:ring-1 focus:ring-violet-500/30 transition-all"
                    />
                  </div>
                  <p className="text-xs text-slate-600 mt-1.5">Supports any YouTube video with subtitles (auto-generated or CC)</p>
                </div>
              )}

              {/* Upload tab */}
              {tab === "upload" && (
                <div className="space-y-3">
                  {/* Video drop zone */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
                      Video File
                    </label>
                    <div
                      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={cn(
                        "drop-zone rounded-xl p-6 cursor-pointer text-center transition-all",
                        dragOver && "drag-over",
                        videoFile && "border-emerald-500/40 bg-emerald-500/5"
                      )}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="video/*"
                        className="hidden"
                        onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                      />
                      {videoFile ? (
                        <div className="flex items-center justify-center gap-3 text-emerald-300">
                          <FileVideo className="w-5 h-5" />
                          <div className="text-left">
                            <div className="text-sm font-semibold">{videoFile.name}</div>
                            <div className="text-xs text-slate-500">{(videoFile.size / 1024 / 1024).toFixed(1)} MB</div>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <Upload className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                          <p className="text-sm text-slate-400">Drop video here or <span className="text-violet-400">click to browse</span></p>
                          <p className="text-xs text-slate-600 mt-1">MP4, MKV, WebM, AVI — max 500 MB</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Optional subtitle file */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">
                      Subtitle File <span className="text-slate-600 normal-case font-normal">(optional — .vtt or .srt)</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => subInputRef.current?.click()}
                      className="w-full flex items-center gap-3 px-4 py-2.5 bg-black/20 border border-white/8 rounded-xl text-sm text-slate-400 hover:border-white/15 hover:text-slate-300 transition-all text-left"
                    >
                      <input
                        ref={subInputRef}
                        type="file"
                        accept=".vtt,.srt"
                        className="hidden"
                        onChange={(e) => setSubtitleFile(e.target.files?.[0] || null)}
                      />
                      <FileText className="w-4 h-4 text-slate-500" />
                      {subtitleFile ? (
                        <span className="text-emerald-300">{subtitleFile.name}</span>
                      ) : (
                        <span>Upload .vtt or .srt (falls back to OCR if omitted)</span>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Language row */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Audio Language", value: audioLang, set: setAudioLang, langs: LANGUAGES },
                  { label: "Subtitle Language", value: subtitleLang, set: setSubtitleLang, langs: LANGUAGES.filter((l) => l.code !== "auto") },
                ].map(({ label, value, set, langs }) => (
                  <div key={label}>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">{label}</label>
                    <select
                      value={value}
                      onChange={(e) => set(e.target.value)}
                      className="w-full px-3 py-2.5 bg-black/30 border border-white/10 rounded-xl text-slate-200 text-sm focus:outline-none focus:border-violet-500/60 transition-all appearance-none"
                    >
                      {langs.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
                    </select>
                  </div>
                ))}
              </div>

              {/* Advanced toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                <ChevronRight className={cn("w-3.5 h-3.5 transition-transform duration-200", showAdvanced && "rotate-90")} />
                Advanced settings
              </button>

              {showAdvanced && (
                <div className="space-y-5 pt-4 border-t border-white/6 animate-fade-in">
                  {/* Whisper model */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">
                      Whisper Model
                    </label>
                    <div className="grid grid-cols-5 gap-1.5">
                      {WHISPER_MODELS.map((m) => (
                        <button
                          key={m.value}
                          type="button"
                          onClick={() => setWhisperModel(m.value)}
                          className={cn(
                            "relative flex flex-col items-center py-2.5 px-1 rounded-xl border text-xs transition-all duration-200",
                            whisperModel === m.value
                              ? "border-violet-500/60 bg-violet-500/10 text-violet-300"
                              : "border-white/8 text-slate-500 hover:border-white/15 hover:text-slate-300"
                          )}
                        >
                          {m.recommended && (
                            <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-[9px] bg-violet-500 text-white px-1.5 py-0.5 rounded-full font-bold">
                              REC
                            </span>
                          )}
                          <span className="font-bold">{m.label}</span>
                          <span className="text-[10px] opacity-60 mt-0.5">{m.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Threshold slider */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                        Match Threshold
                      </label>
                      <span className="text-xs font-mono bg-violet-500/15 text-violet-300 px-2 py-0.5 rounded-lg border border-violet-500/20">
                        {threshold.toFixed(2)}
                      </span>
                    </div>
                    <input
                      type="range" min="0.5" max="0.99" step="0.01"
                      value={threshold}
                      onChange={(e) => setThreshold(parseFloat(e.target.value))}
                      className="w-full accent-violet-500 h-1.5"
                    />
                    <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                      <span>Lenient (0.50)</span>
                      <span className="text-slate-500">0.75 = recommended for Indic</span>
                      <span>Strict (0.99)</span>
                    </div>
                  </div>

                  {/* OCR toggle */}
                  <label className="flex items-center justify-between gap-3 cursor-pointer group">
                    <div>
                      <p className="text-sm text-slate-300 font-medium group-hover:text-slate-200 transition-colors">OCR Fallback</p>
                      <p className="text-xs text-slate-600 mt-0.5">Use Tesseract OCR when no subtitle file exists</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setUseOcr(!useOcr)}
                      className={cn(
                        "relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0",
                        useOcr ? "bg-violet-600" : "bg-white/10"
                      )}
                    >
                      <span className={cn(
                        "absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200",
                        useOcr ? "translate-x-6" : "translate-x-1"
                      )} />
                    </button>
                  </label>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="flex items-start gap-2.5 p-3.5 bg-red-500/8 border border-red-500/20 rounded-xl text-sm text-red-300 animate-fade-in">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit */}
              <Button
                type="submit"
                size="lg"
                loading={loading}
                disabled={loading || (tab === "youtube" ? !url.trim() : !videoFile)}
                className="w-full btn-glow text-base"
              >
                {!loading && <Wand2 className="w-4 h-4" />}
                {loading ? "Starting analysis…" : "Analyze Now"}
                {!loading && <ArrowRight className="w-4 h-4 ml-auto" />}
              </Button>
            </form>
          </div>
        </div>
      </section>

      {/* Pipeline visualization */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-white mb-2">How it works</h2>
          <p className="text-slate-500 text-sm">Five-step automated pipeline, no manual scrubbing</p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-center gap-4 sm:gap-0">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={i} className="flex sm:flex-col items-center gap-3 sm:gap-2 sm:flex-1">
              {/* Step circle */}
              <div className="relative flex-shrink-0">
                <div className="w-12 h-12 rounded-2xl glass-bright border border-white/8 flex items-center justify-center text-violet-400 transition-all hover:border-violet-500/40 hover:text-violet-300 hover:scale-110 duration-200">
                  {step.icon}
                </div>
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-violet-600 text-white text-[10px] font-bold flex items-center justify-center">
                  {i + 1}
                </span>
              </div>
              {/* Connector */}
              {i < PIPELINE_STEPS.length - 1 && (
                <div className="hidden sm:flex flex-1 items-center justify-center">
                  <div className="w-full h-px bg-gradient-to-r from-violet-500/30 to-transparent" />
                  <ArrowRight className="w-3 h-3 text-slate-700 -ml-2 flex-shrink-0" />
                </div>
              )}
              <div className="sm:text-center">
                <p className="text-xs font-semibold text-slate-300">{step.label}</p>
                <p className="text-[11px] text-slate-600 mt-0.5 hidden sm:block">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Language badges */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <div className="glass rounded-2xl p-6 flex flex-wrap gap-2 justify-center border border-white/6">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest self-center mr-2">Supported Scripts</span>
          {[
            { lang: "Hindi", script: "हिन्दी" },
            { lang: "Kannada", script: "ಕನ್ನಡ" },
            { lang: "Tamil", script: "தமிழ்" },
            { lang: "Telugu", script: "తెలుగు" },
            { lang: "Marathi", script: "मराठी" },
            { lang: "Bengali", script: "বাংলা" },
            { lang: "Gujarati", script: "ગુજરાતી" },
            { lang: "Malayalam", script: "മലയാളം" },
            { lang: "Punjabi", script: "ਪੰਜਾਬੀ" },
            { lang: "English", script: "English" },
          ].map(({ lang, script }) => (
            <span key={lang} className="px-3 py-1.5 rounded-xl bg-white/4 border border-white/8 text-xs text-slate-300 hover:bg-white/8 hover:border-white/15 transition-all cursor-default">
              <span className="text-slate-500 font-medium">{lang} · </span>
              <span className="indic-text">{script}</span>
            </span>
          ))}
        </div>
      </section>
    </AuroraBackground>
  );
}
