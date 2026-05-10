"""
Parse VTT and SRT subtitle files into timed segments.

Supports:
  - WebVTT (.vtt)  — primary format from YouTube via yt-dlp
  - SubRip  (.srt) — fallback format
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SRT_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
_VTT_TIMESTAMP_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})\.(\d{3})"
)
_VTT_SHORTTS_RE = re.compile(
    r"(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2})\.(\d{3})"
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CUE_META_RE = re.compile(r"^(align|line|position|size):", re.IGNORECASE)


def _ts_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


class SubtitleParser:
    def parse(self, path: str) -> list[dict]:
        """
        Auto-detect format and parse subtitle file.

        Returns
        -------
        list of { "start": float, "end": float, "text": str }
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {path}")

        content = path.read_text(encoding="utf-8", errors="replace")

        if path.suffix.lower() == ".vtt" or content.strip().startswith("WEBVTT"):
            return self._parse_vtt(content)
        return self._parse_srt(content)

    # ------------------------------------------------------------------
    # VTT
    # ------------------------------------------------------------------

    def _parse_vtt(self, content: str) -> list[dict]:
        segments = []
        lines = content.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Try full HH:MM:SS.mmm --> HH:MM:SS.mmm
            m = _VTT_TIMESTAMP_RE.search(line)
            if m:
                start = _ts_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
                end = _ts_to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    raw = lines[i].strip()
                    if not _CUE_META_RE.match(raw):
                        cleaned = _HTML_TAG_RE.sub("", raw).strip()
                        if cleaned:
                            text_lines.append(cleaned)
                    i += 1
                text = " ".join(text_lines).strip()
                if text:
                    segments.append({"start": start, "end": end, "text": text})
                continue

            # Try short MM:SS.mmm --> MM:SS.mmm
            m2 = _VTT_SHORTTS_RE.search(line)
            if m2:
                start = _ts_to_seconds("0", m2.group(1), m2.group(2), m2.group(3))
                end = _ts_to_seconds("0", m2.group(4), m2.group(5), m2.group(6))
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    raw = lines[i].strip()
                    if not _CUE_META_RE.match(raw):
                        cleaned = _HTML_TAG_RE.sub("", raw).strip()
                        if cleaned:
                            text_lines.append(cleaned)
                    i += 1
                text = " ".join(text_lines).strip()
                if text:
                    segments.append({"start": start, "end": end, "text": text})
                continue

            i += 1

        logger.info("VTT parsed: %d segments", len(segments))
        return self._merge_overlapping(segments)

    # ------------------------------------------------------------------
    # SRT
    # ------------------------------------------------------------------

    def _parse_srt(self, content: str) -> list[dict]:
        segments = []
        blocks = re.split(r"\n\n+", content.strip())

        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 2:
                continue

            # Find timestamp line
            ts_line = None
            text_start = 0
            for idx, l in enumerate(lines):
                m = _SRT_TIMESTAMP_RE.search(l)
                if m:
                    ts_line = m
                    text_start = idx + 1
                    break

            if ts_line is None:
                continue

            start = _ts_to_seconds(
                ts_line.group(1), ts_line.group(2), ts_line.group(3), ts_line.group(4)
            )
            end = _ts_to_seconds(
                ts_line.group(5), ts_line.group(6), ts_line.group(7), ts_line.group(8)
            )

            text = " ".join(
                _HTML_TAG_RE.sub("", l).strip()
                for l in lines[text_start:]
                if l.strip()
            ).strip()

            if text:
                segments.append({"start": start, "end": end, "text": text})

        logger.info("SRT parsed: %d segments", len(segments))
        return self._merge_overlapping(segments)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _merge_overlapping(self, segments: list[dict]) -> list[dict]:
        """Merge consecutive segments with identical text (YouTube often duplicates cues)."""
        if not segments:
            return []
        merged = [segments[0].copy()]
        for seg in segments[1:]:
            prev = merged[-1]
            if seg["text"] == prev["text"] and seg["start"] <= prev["end"] + 0.1:
                prev["end"] = max(prev["end"], seg["end"])
            else:
                merged.append(seg.copy())
        return merged
