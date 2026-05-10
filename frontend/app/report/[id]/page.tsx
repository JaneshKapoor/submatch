"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Download, ExternalLink, Search, ChevronLeft,
  CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  Filter, TrendingUp, Clock, Hash,
} from "lucide-react";
import { AuroraBackground } from "@/components/ui/aurora-background";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getReport, getReportHtmlUrl } from "@/lib/api";
import { ReportData, SegmentResult, FilterStatus } from "@/lib/types";

const STATUS_META = {
  OK:       { variant: "ok"       as const, icon: <CheckCircle2 className="w-3 h-3" />, bar: "bg-emerald-500", row: "" },
  MARGINAL: { variant: "marginal" as const, icon: <AlertTriangle className="w-3 h-3" />, bar: "bg-amber-500",  row: "bg-amber-900/5" },
  REVIEW:   { variant: "review"   as const, icon: <XCircle className="w-3 h-3" />,       bar: "bg-red-500",    row: "bg-red-900/5" },
  MISSING:  { variant: "missing"  as const, icon: <HelpCircle className="w-3 h-3" />,    bar: "bg-slate-500",  row: "bg-slate-800/20" },
};

const FILTERS: { label: string; value: FilterStatus }[] = [
  { label: "All",      value: "all" },
  { label: "Review",   value: "REVIEW" },
  { label: "Marginal", value: "MARGINAL" },
  { label: "OK",       value: "OK" },
  { label: "Missing",  value: "MISSING" },
];

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<FilterStatus>("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!jobId) return;
    getReport(jobId).then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [jobId]);

  const filtered = useMemo(() => {
    if (!data) return [];
    let s: SegmentResult[] = data.segments;
    if (filter !== "all") s = s.filter((r) => r.status === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      s = s.filter((r) => r.audio_text.toLowerCase().includes(q) || r.subtitle_text.toLowerCase().includes(q));
    }
    return s;
  }, [data, filter, search]);

  if (loading) return (
    <AuroraBackground className="flex items-center justify-center">
      <div className="text-center animate-fade-up">
        <div className="w-12 h-12 border-2 border-white/10 border-t-violet-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Loading report…</p>
      </div>
    </AuroraBackground>
  );

  if (error || !data) return (
    <AuroraBackground className="flex items-center justify-center px-6">
      <div className="text-center max-w-md animate-fade-up">
        <XCircle className="w-14 h-14 text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Report Not Found</h2>
        <p className="text-slate-400 text-sm mb-6">{error || "Could not load the report."}</p>
        <Button onClick={() => router.push("/")}>Back to Home</Button>
      </div>
    </AuroraBackground>
  );

  const { stats } = data;
  const statCards = [
    { label: "Total Segments",    value: stats.total,              icon: <Hash className="w-4 h-4" />,       color: "text-violet-300",  glow: "shadow-violet-500/10" },
    { label: "Match Rate",        value: `${stats.match_rate}%`,   icon: <TrendingUp className="w-4 h-4" />, color: "text-emerald-300", glow: "shadow-emerald-500/10" },
    { label: "Flagged for Review", value: stats.flagged,           icon: <AlertTriangle className="w-4 h-4" />, color: "text-red-300",  glow: "shadow-red-500/10" },
    { label: "Avg. Score",        value: stats.avg_score.toFixed(2), icon: <Clock className="w-4 h-4" />,    color: "text-amber-300",   glow: "shadow-amber-500/10" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-slate-100">
      {/* Subtle noise + gradient header */}
      <div className="relative border-b border-white/5 bg-gradient-to-r from-gray-950 via-gray-900/80 to-gray-950">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-violet-900/5 via-transparent to-indigo-900/5" />

        {/* Sticky nav */}
        <div className="sticky top-0 z-50 border-b border-white/5 bg-gray-950/90 backdrop-blur-xl">
          <div className="max-w-screen-xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <button onClick={() => router.push("/")} className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm">
                <ChevronLeft className="w-4 h-4" />
                Home
              </button>
              <span className="text-white/10">|</span>
              <div className="w-6 h-6 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-md flex items-center justify-center">
                <span className="text-white font-black text-xs">S</span>
              </div>
              <span className="text-sm font-bold text-white">SubMatch</span>
              <span className="text-slate-600 text-xs hidden md:block">·</span>
              <span className="text-slate-500 text-xs hidden md:block">Mismatch Report</span>
            </div>
            <div className="flex items-center gap-2">
              <a href={getReportHtmlUrl(jobId)} target="_blank" rel="noreferrer">
                <Button variant="secondary" size="sm">
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open HTML
                </Button>
              </a>
              <a href={getReportHtmlUrl(jobId)} download="submatch-report.html">
                <Button size="sm">
                  <Download className="w-3.5 h-3.5" />
                  Download
                </Button>
              </a>
            </div>
          </div>
        </div>

        {/* Report header */}
        <div className="max-w-screen-xl mx-auto px-6 py-8">
          <div className="mb-2 flex items-center gap-2 text-xs text-slate-500 font-mono">
            <svg className="w-3.5 h-3.5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V9.35a8.16 8.16 0 004.77 1.52V7.42a4.85 4.85 0 01-1-.73z" />
            </svg>
            <span className="truncate max-w-lg">{data.video_url}</span>
          </div>
          <h1 className="text-2xl font-black text-white">Mismatch Analysis Report</h1>
          <p className="text-slate-500 text-sm mt-1">{new Date(data.generated_at).toLocaleString()}</p>
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-6 py-8">

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((c) => (
            <div key={c.label} className={cn("glass rounded-2xl p-5 border border-white/6 hover:border-white/10 transition-all hover:shadow-xl", c.glow)}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-500 text-xs font-medium">{c.label}</span>
                <span className={cn("opacity-60", c.color)}>{c.icon}</span>
              </div>
              <div className={cn("text-3xl font-black tabular-nums", c.color)}>{c.value}</div>
            </div>
          ))}
        </div>

        {/* Breakdown bar */}
        <div className="glass rounded-2xl border border-white/6 p-5 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h3 className="text-sm font-semibold text-slate-300">Segment Breakdown</h3>
            <div className="flex flex-wrap gap-4 text-xs text-slate-500">
              {[
                { label: "OK",       count: stats.ok,       dot: "bg-emerald-500" },
                { label: "Marginal", count: stats.marginal, dot: "bg-amber-500" },
                { label: "Review",   count: stats.review,   dot: "bg-red-500" },
                { label: "Missing",  count: stats.missing,  dot: "bg-slate-500" },
              ].map((s) => (
                <span key={s.label} className="flex items-center gap-1.5">
                  <span className={cn("w-1.5 h-1.5 rounded-full", s.dot)} />
                  {s.label} ({s.count})
                </span>
              ))}
            </div>
          </div>
          <div className="h-2.5 bg-white/5 rounded-full overflow-hidden flex gap-px">
            {stats.total > 0 && (
              <>
                <div className="bg-emerald-500 h-full rounded-l-full score-bar" style={{ width: `${(stats.ok / stats.total) * 100}%` }} />
                <div className="bg-amber-500 h-full score-bar"                  style={{ width: `${(stats.marginal / stats.total) * 100}%` }} />
                <div className="bg-red-500 h-full score-bar"                    style={{ width: `${(stats.review / stats.total) * 100}%` }} />
                <div className="bg-slate-600 h-full rounded-r-full score-bar"   style={{ width: `${(stats.missing / stats.total) * 100}%` }} />
              </>
            )}
          </div>
        </div>

        {/* Filters + search */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <Filter className="w-3.5 h-3.5 text-slate-600" />
          {FILTERS.map((f) => {
            const count = f.value === "all" ? stats.total : f.value === "REVIEW" ? stats.review : f.value === "MARGINAL" ? stats.marginal : f.value === "OK" ? stats.ok : stats.missing;
            return (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={cn(
                  "px-3 py-1 rounded-xl text-xs font-semibold border transition-all",
                  filter === f.value
                    ? "border-violet-500/60 bg-violet-500/15 text-violet-300"
                    : "border-white/8 text-slate-500 hover:border-white/15 hover:text-slate-300"
                )}
              >
                {f.label} <span className="opacity-60">({count})</span>
              </button>
            );
          })}
          <div className="ml-auto relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600" />
            <input
              type="text"
              placeholder="Search segments…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-white/5 border border-white/8 rounded-xl text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-violet-500/50 w-52 transition-all"
            />
          </div>
        </div>

        {/* Table */}
        <div className="rounded-2xl border border-white/6 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/3 border-b border-white/6">
                  {["Timestamp", "Audio (Whisper)", "Subtitle", "Words", "Score", "Status"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-widest whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/4">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-16 text-slate-600">
                      <Search className="w-8 h-8 mx-auto mb-3 text-slate-700" />
                      <p className="text-sm">No segments match this filter.</p>
                    </td>
                  </tr>
                ) : (
                  filtered.map((seg) => {
                    const meta = STATUS_META[seg.status];
                    const scorePct = Math.round(seg.score * 100);
                    return (
                      <tr key={seg.index} className={cn("hover:bg-white/3 transition-colors", meta.row)}>
                        {/* Timestamp */}
                        <td className="px-4 py-3 font-mono text-xs text-slate-500 whitespace-nowrap">
                          {seg.timestamp_label}
                        </td>
                        {/* Audio text */}
                        <td className="px-4 py-3 indic-text text-slate-200 max-w-xs">
                          {seg.audio_text || <span className="text-slate-600 italic text-xs">empty</span>}
                        </td>
                        {/* Subtitle text */}
                        <td className="px-4 py-3 indic-text text-slate-300 max-w-xs">
                          {seg.subtitle_text || <span className="text-slate-600 italic text-xs">not found</span>}
                        </td>
                        {/* Word count */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-1.5 text-xs font-mono">
                            <span className="text-slate-400">{seg.word_count_audio}</span>
                            <span className="text-slate-700">vs</span>
                            <span className="text-slate-400">{seg.word_count_subtitle}</span>
                            {seg.word_count_delta > 0 && (
                              <span className={cn(
                                "px-1.5 py-0.5 rounded-md text-[10px] font-bold",
                                seg.word_count_delta > 3 ? "bg-red-500/15 text-red-400" :
                                seg.word_count_delta > 1 ? "bg-amber-500/15 text-amber-400" :
                                "bg-slate-500/15 text-slate-500"
                              )}>
                                Δ{seg.word_count_delta}
                              </span>
                            )}
                          </div>
                        </td>
                        {/* Score bar */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-white/8 rounded-full overflow-hidden">
                              <div
                                className={cn("h-full rounded-full score-bar", meta.bar)}
                                style={{ width: `${scorePct}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono text-slate-400 tabular-nums w-8">
                              {seg.score.toFixed(2)}
                            </span>
                          </div>
                        </td>
                        {/* Status badge */}
                        <td className="px-4 py-3">
                          <Badge variant={meta.variant}>
                            {meta.icon}
                            {seg.status}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-5 border-t border-white/5 flex items-center justify-between text-xs text-slate-600">
          <span>
            Generated by <strong className="text-slate-500">SubMatch</strong> · PlanetRead Open Source
          </span>
          <span className="font-mono">{filtered.length} / {stats.total} segments shown</span>
        </div>
      </div>
    </div>
  );
}
