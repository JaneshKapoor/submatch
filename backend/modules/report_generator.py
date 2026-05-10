"""
Generates a standalone, beautiful HTML report of the mismatch analysis.
The HTML embeds Tailwind CSS via CDN and requires no server to view.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

from utils.text_utils import format_timestamp


_STATUS_CONFIG = {
    "OK":       {"badge": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30", "row": "hover:bg-slate-700/30", "dot": "#10b981"},
    "MARGINAL": {"badge": "bg-amber-500/20 text-amber-300 border-amber-500/30",      "row": "hover:bg-amber-900/10 bg-amber-900/5", "dot": "#f59e0b"},
    "REVIEW":   {"badge": "bg-red-500/20 text-red-300 border-red-500/30",            "row": "hover:bg-red-900/10 bg-red-900/5",    "dot": "#ef4444"},
    "MISSING":  {"badge": "bg-slate-500/20 text-slate-400 border-slate-500/30",      "row": "hover:bg-slate-700/30 bg-slate-800/50", "dot": "#6b7280"},
}


class ReportGenerator:
    def generate(
        self,
        results: list[dict],
        video_url: str,
        output_path: str,
    ) -> dict:
        """
        Generate an HTML report and write it to `output_path`.
        Also returns structured data (for JSON API response).
        """
        stats = self._compute_stats(results)
        html = self._render_html(results, stats, video_url)

        Path(output_path).write_text(html, encoding="utf-8")

        return {
            "stats": stats,
            "segments": results,
            "video_url": video_url,
            "generated_at": datetime.now().isoformat(),
            "report_path": output_path,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def _compute_stats(self, results: list[dict]) -> dict:
        total = len(results)
        ok = sum(1 for r in results if r["status"] == "OK")
        marginal = sum(1 for r in results if r["status"] == "MARGINAL")
        review = sum(1 for r in results if r["status"] == "REVIEW")
        missing = sum(1 for r in results if r["status"] == "MISSING")
        flagged = marginal + review + missing

        avg_score = (
            sum(r["score"] for r in results if r["has_subtitle"]) /
            max(1, sum(1 for r in results if r["has_subtitle"]))
        )

        return {
            "total": total,
            "ok": ok,
            "marginal": marginal,
            "review": review,
            "missing": missing,
            "flagged": flagged,
            "avg_score": round(avg_score, 4),
            "match_rate": round(ok / max(1, total) * 100, 1),
        }

    # ------------------------------------------------------------------
    # HTML rendering
    # ------------------------------------------------------------------

    def _render_html(self, results: list[dict], stats: dict, video_url: str) -> str:
        rows_html = "".join(self._render_row(r) for r in results)
        results_json = json.dumps(results, ensure_ascii=False)

        return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Subtitle Mismatch Report — PlanetRead</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Inter', 'system-ui', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
          }},
        }},
      }},
    }};
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    body {{ font-family: 'Inter', sans-serif; }}
    .score-bar {{ transition: width 0.6s cubic-bezier(0.4,0,0.2,1); }}
    .fade-in {{ animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .hindi-text {{ font-size: 1rem; line-height: 1.6; }}
    tr {{ transition: background 0.15s ease; }}
    ::-webkit-scrollbar {{ width:6px; height:6px; }}
    ::-webkit-scrollbar-track {{ background:#1e293b; }}
    ::-webkit-scrollbar-thumb {{ background:#475569; border-radius:3px; }}
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">

  <!-- Header -->
  <header class="border-b border-slate-700/60 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">P</div>
        <div>
          <div class="font-semibold text-slate-100">PlanetRead</div>
          <div class="text-xs text-slate-400">Audio-Subtitle Mismatch Report</div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-slate-500">{datetime.now().strftime("%B %d, %Y %H:%M")}</span>
        <button onclick="downloadReport()" class="flex items-center gap-2 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium rounded-lg transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          Download
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-6 py-8">

    <!-- Video URL badge -->
    <div class="mb-6 flex items-center gap-2 text-sm text-slate-400">
      <svg class="w-4 h-4 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V9.35a8.16 8.16 0 004.77 1.52V7.42a4.85 4.85 0 01-1-.73z"/></svg>
      <span class="truncate max-w-xl font-mono text-xs">{video_url}</span>
    </div>

    <!-- Stats cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {self._stat_card("Total Segments", str(stats['total']), "#6366f1", "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z")}
      {self._stat_card("Match Rate", f"{stats['match_rate']}%", "#10b981", "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z")}
      {self._stat_card("Flagged for Review", str(stats['flagged']), "#ef4444", "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z")}
      {self._stat_card("Avg Score", f"{stats['avg_score']:.2f}", "#f59e0b", "M13 10V3L4 14h7v7l9-11h-7z")}
    </div>

    <!-- Score breakdown bar -->
    <div class="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5 mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-slate-300">Segment Breakdown</h3>
        <div class="flex items-center gap-4 text-xs text-slate-400">
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>OK ({stats['ok']})</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500 inline-block"></span>Marginal ({stats['marginal']})</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>Review ({stats['review']})</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-slate-500 inline-block"></span>Missing ({stats['missing']})</span>
        </div>
      </div>
      <div class="h-3 bg-slate-700 rounded-full overflow-hidden flex">
        <div class="bg-emerald-500 h-full score-bar" style="width:{stats['ok']/max(1,stats['total'])*100:.1f}%"></div>
        <div class="bg-amber-500 h-full score-bar" style="width:{stats['marginal']/max(1,stats['total'])*100:.1f}%"></div>
        <div class="bg-red-500 h-full score-bar" style="width:{stats['review']/max(1,stats['total'])*100:.1f}%"></div>
        <div class="bg-slate-500 h-full score-bar" style="width:{stats['missing']/max(1,stats['total'])*100:.1f}%"></div>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <span class="text-sm text-slate-400 font-medium">Filter:</span>
      <button onclick="filterTable('all')" id="btn-all" class="filter-btn active px-3 py-1 rounded-lg text-xs font-medium border border-violet-500 bg-violet-500/20 text-violet-300 transition-all">All ({stats['total']})</button>
      <button onclick="filterTable('REVIEW')" id="btn-REVIEW" class="filter-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-600 text-slate-400 hover:border-red-500/50 hover:text-red-300 transition-all">Review Only ({stats['review']})</button>
      <button onclick="filterTable('MARGINAL')" id="btn-MARGINAL" class="filter-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-600 text-slate-400 hover:border-amber-500/50 hover:text-amber-300 transition-all">Marginal ({stats['marginal']})</button>
      <button onclick="filterTable('OK')" id="btn-OK" class="filter-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-600 text-slate-400 hover:border-emerald-500/50 hover:text-emerald-300 transition-all">OK ({stats['ok']})</button>
      <button onclick="filterTable('MISSING')" id="btn-MISSING" class="filter-btn px-3 py-1 rounded-lg text-xs font-medium border border-slate-600 text-slate-400 hover:border-slate-400/50 transition-all">Missing ({stats['missing']})</button>

      <div class="ml-auto">
        <input id="search-input" oninput="searchTable(this.value)" type="text" placeholder="Search text..." class="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded-lg text-xs text-slate-300 placeholder-slate-500 focus:outline-none focus:border-violet-500 w-48" />
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-xl border border-slate-700/50 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm" id="results-table">
          <thead>
            <tr class="bg-slate-800/80 border-b border-slate-700/50">
              <th class="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider w-24">Time</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Audio (Whisper)</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Subtitle</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider w-40">Score</th>
              <th class="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider w-28">Status</th>
            </tr>
          </thead>
          <tbody id="table-body" class="divide-y divide-slate-700/30">
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty state (hidden by default) -->
    <div id="empty-state" class="hidden text-center py-16 text-slate-500">
      <svg class="w-12 h-12 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
      <p class="font-medium">No segments match this filter</p>
    </div>

    <!-- Footer -->
    <div class="mt-8 pt-6 border-t border-slate-700/40 flex items-center justify-between text-xs text-slate-500">
      <span>Generated by <strong class="text-slate-400">PlanetRead Audio-Subtitle Mismatch Detector</strong></span>
      <span>Open Source — MIT License</span>
    </div>
  </main>

  <script>
    const allData = {results_json};
    let currentFilter = 'all';
    let currentSearch = '';

    function filterTable(status) {{
      currentFilter = status;
      document.querySelectorAll('.filter-btn').forEach(b => {{
        b.classList.remove('active', 'border-violet-500', 'bg-violet-500/20', 'text-violet-300');
        b.classList.add('border-slate-600', 'text-slate-400');
      }});
      const activeBtn = document.getElementById('btn-' + status);
      if (activeBtn) {{
        activeBtn.classList.add('active', 'border-violet-500', 'bg-violet-500/20', 'text-violet-300');
        activeBtn.classList.remove('border-slate-600', 'text-slate-400');
      }}
      renderTable();
    }}

    function searchTable(val) {{
      currentSearch = val.toLowerCase();
      renderTable();
    }}

    function renderTable() {{
      const tbody = document.getElementById('table-body');
      const emptyState = document.getElementById('empty-state');
      let filtered = allData;
      if (currentFilter !== 'all') {{
        filtered = filtered.filter(r => r.status === currentFilter);
      }}
      if (currentSearch) {{
        filtered = filtered.filter(r =>
          (r.audio_text || '').toLowerCase().includes(currentSearch) ||
          (r.subtitle_text || '').toLowerCase().includes(currentSearch)
        );
      }}

      if (filtered.length === 0) {{
        tbody.innerHTML = '';
        emptyState.classList.remove('hidden');
      }} else {{
        emptyState.classList.add('hidden');
        tbody.innerHTML = filtered.map(r => buildRow(r)).join('');
      }}
    }}

    function buildRow(r) {{
      const statusColors = {{
        'OK':       'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        'MARGINAL': 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        'REVIEW':   'bg-red-500/20 text-red-300 border-red-500/30',
        'MISSING':  'bg-slate-500/20 text-slate-400 border-slate-500/30',
      }};
      const rowColors = {{
        'OK':       '',
        'MARGINAL': 'bg-amber-900/5',
        'REVIEW':   'bg-red-900/5',
        'MISSING':  'bg-slate-800/50',
      }};
      const barColors = {{
        'OK': '#10b981', 'MARGINAL': '#f59e0b', 'REVIEW': '#ef4444', 'MISSING': '#6b7280'
      }};
      const sc = (r.score * 100).toFixed(0);
      return `
        <tr class="border-b border-slate-700/20 ${{rowColors[r.status] || ''}} hover:bg-slate-700/20 transition-colors fade-in">
          <td class="px-4 py-3 font-mono text-xs text-slate-400 whitespace-nowrap">${{r.timestamp_label}}</td>
          <td class="px-4 py-3 hindi-text text-slate-200 max-w-xs">${{r.audio_text || '<span class="text-slate-500 italic text-xs">empty</span>'}}</td>
          <td class="px-4 py-3 hindi-text text-slate-300 max-w-xs">${{r.subtitle_text || '<span class="text-slate-500 italic text-xs">not found</span>'}}</td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden w-16">
                <div class="h-full rounded-full" style="width:${{sc}}%;background:${{barColors[r.status]}}"></div>
              </div>
              <span class="text-xs font-mono text-slate-300 w-8">${{r.score.toFixed(2)}}</span>
            </div>
          </td>
          <td class="px-4 py-3">
            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${{statusColors[r.status] || ''}}">${{r.status}}</span>
          </td>
        </tr>`;
    }}

    function downloadReport() {{
      const blob = new Blob([document.documentElement.outerHTML], {{type: 'text/html'}});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'mismatch-report.html';
      a.click();
    }}
  </script>
</body>
</html>"""

    def _stat_card(self, label: str, value: str, color: str, icon_path: str) -> str:
        return f"""
      <div class="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5 flex items-start gap-4">
        <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style="background:{color}22">
          <svg class="w-5 h-5" style="color:{color}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{icon_path}" />
          </svg>
        </div>
        <div>
          <div class="text-2xl font-bold text-slate-100">{value}</div>
          <div class="text-xs text-slate-400 mt-0.5">{label}</div>
        </div>
      </div>"""

    def _render_row(self, r: dict) -> str:
        cfg = _STATUS_CONFIG.get(r["status"], _STATUS_CONFIG["MISSING"])
        score_pct = int(r["score"] * 100)
        bar_color = cfg["dot"]

        audio_display = r["audio_text"] or '<span class="text-slate-500 italic text-xs">empty</span>'
        sub_display = r["subtitle_text"] or '<span class="text-slate-500 italic text-xs">not found</span>'

        return f"""
            <tr class="border-b border-slate-700/20 {cfg['row']} transition-colors">
              <td class="px-4 py-3 font-mono text-xs text-slate-400 whitespace-nowrap">{r['timestamp_label']}</td>
              <td class="px-4 py-3 hindi-text text-slate-200 max-w-xs">{audio_display}</td>
              <td class="px-4 py-3 hindi-text text-slate-300 max-w-xs">{sub_display}</td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden w-16">
                    <div class="h-full rounded-full score-bar" style="width:{score_pct}%;background:{bar_color}"></div>
                  </div>
                  <span class="text-xs font-mono text-slate-300 w-8">{r['score']:.2f}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border {cfg['badge']}">{r['status']}</span>
              </td>
            </tr>"""
