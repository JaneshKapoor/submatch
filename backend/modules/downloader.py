"""
YouTube video + subtitle downloader using yt-dlp.

Priority order for subtitles:
  1. Manual / human-generated subtitles (most accurate)
  2. Auto-generated subtitles by YouTube
  3. Nothing (fall back to OCR)
"""

from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
from typing import Callable

import yt_dlp

logger = logging.getLogger(__name__)


class VideoDownloader:
    def __init__(self, job_dir: str, progress_hook: Callable | None = None):
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._progress_hook = progress_hook

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(
        self,
        url: str,
        subtitle_language: str = "hi",
    ) -> tuple[str, list[str]]:
        """
        Download video + subtitles for `url`.

        Returns
        -------
        video_path : str   Absolute path to the downloaded video file.
        subtitle_paths : list[str]
            Paths to subtitle files found (may be empty if none available).
        """
        video_path = self._download_video_and_subtitles(url, subtitle_language)
        subtitle_paths = self._collect_subtitle_files(subtitle_language)

        if not subtitle_paths:
            logger.warning("No subtitles found for language '%s'", subtitle_language)

        return str(video_path), subtitle_paths

    def get_video_info(self, url: str) -> dict:
        """Fetch video metadata without downloading."""
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ydl_progress_hook(self, d: dict):
        if self._progress_hook and d.get("status") == "downloading":
            pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(pct_str)
                self._progress_hook(pct)
            except ValueError:
                pass

    def _download_video_and_subtitles(self, url: str, subtitle_language: str) -> Path:
        output_template = str(self.job_dir / "video.%(ext)s")

        # Build language list: requested lang + English fallback
        lang_list = [subtitle_language]
        if subtitle_language != "en":
            lang_list.append("en")

        ydl_opts = {
            # Video format: best quality mp4 (or best available)
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": output_template,
            # Subtitle download options
            "writesubtitles": True,           # manual subs
            "writeautomaticsub": True,         # auto-generated subs
            "subtitleslangs": lang_list,
            "subtitlesformat": "vtt/srt/best",
            # Misc
            "quiet": True,
            "no_warnings": False,
            "progress_hooks": [self._ydl_progress_hook],
            "postprocessors": [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded video file
        for ext in ("mp4", "mkv", "webm", "avi", "mov"):
            p = self.job_dir / f"video.{ext}"
            if p.exists():
                return p

        # Fallback: first video file found
        for f in self.job_dir.iterdir():
            if f.suffix in {".mp4", ".mkv", ".webm", ".avi", ".mov"}:
                return f

        raise FileNotFoundError(f"Video download failed — no video file in {self.job_dir}")

    def _collect_subtitle_files(self, subtitle_language: str) -> list[str]:
        """Collect subtitle files, preferring manual > auto-generated."""
        patterns = [
            # Manual subtitles (no 'auto' in filename)
            str(self.job_dir / f"video.{subtitle_language}.vtt"),
            str(self.job_dir / f"video.{subtitle_language}.srt"),
            # Auto-generated
            str(self.job_dir / f"video.{subtitle_language}.auto.vtt"),
            str(self.job_dir / f"video.{subtitle_language}.auto.srt"),
        ]

        found = []
        for pattern in patterns:
            matches = glob.glob(pattern)
            found.extend(matches)

        if not found:
            # Broader search: any subtitle file in the job dir
            for ext in ("vtt", "srt"):
                found.extend(glob.glob(str(self.job_dir / f"*.{ext}")))

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for f in found:
            if f not in seen:
                seen.add(f)
                unique.append(f)

        return unique
