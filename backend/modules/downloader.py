"""
YouTube video + subtitle downloader.

Subtitle priority:
  1. youtube-transcript-api  (works from cloud IPs, no bot detection)
  2. yt-dlp manual CC subtitles
  3. yt-dlp auto-generated subtitles
  4. Nothing (fall back to OCR)

Video download uses yt-dlp with Android player client to bypass
YouTube's bot detection on cloud/datacenter IPs.
"""

from __future__ import annotations

import glob
import json
import logging
import re
from pathlib import Path
from typing import Callable

import yt_dlp

logger = logging.getLogger(__name__)


def _extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


class VideoDownloader:
    def __init__(self, job_dir: str, progress_hook: Callable | None = None):
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self._progress_hook = progress_hook

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(self, url: str, subtitle_language: str = "hi") -> tuple[str, list[str]]:
        """
        Download video + subtitles. Returns (video_path, subtitle_paths).
        Tries multiple strategies to avoid YouTube bot detection on cloud.
        """
        # 1. Try fetching subtitles via youtube-transcript-api (cloud-safe)
        subtitle_paths = self._fetch_subtitles_via_api(url, subtitle_language)

        # 2. Download the video (audio needed for Whisper)
        video_path = self._download_video(url)

        # 3. If transcript API failed, fall back to yt-dlp subtitles
        if not subtitle_paths:
            subtitle_paths = self._collect_subtitle_files(subtitle_language)

        if not subtitle_paths:
            logger.warning("No subtitles found for language '%s'", subtitle_language)

        return str(video_path), subtitle_paths

    # ------------------------------------------------------------------
    # Subtitle via youtube-transcript-api (bypasses bot detection)
    # ------------------------------------------------------------------

    def _fetch_subtitles_via_api(self, url: str, language: str) -> list[str]:
        """
        Use youtube-transcript-api to fetch subtitles directly.
        Works from cloud IPs where yt-dlp download is blocked.
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

            video_id = _extract_video_id(url)
            if not video_id:
                return []

            # Try requested language, then English, then any available
            lang_priority = [language]
            if language != "en":
                lang_priority.append("en")

            transcript = None
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_priority)
            except NoTranscriptFound:
                # Try auto-generated
                try:
                    listing = YouTubeTranscriptApi.list_transcripts(video_id)
                    for t in listing:
                        transcript = t.fetch()
                        break
                except Exception:
                    pass
            except TranscriptsDisabled:
                logger.info("Transcripts disabled for %s", video_id)
                return []

            if not transcript:
                return []

            # Convert to VTT and save
            vtt_path = self.job_dir / f"video.{language}.vtt"
            self._transcript_to_vtt(transcript, vtt_path)
            logger.info("Subtitles fetched via youtube-transcript-api → %s", vtt_path)
            return [str(vtt_path)]

        except ImportError:
            logger.warning("youtube-transcript-api not installed, skipping")
            return []
        except Exception as e:
            logger.warning("youtube-transcript-api failed: %s", e)
            return []

    def _transcript_to_vtt(self, transcript: list[dict], path: Path):
        """Convert youtube-transcript-api output to a VTT file."""
        lines = ["WEBVTT\n"]
        for entry in transcript:
            start = entry["start"]
            end = start + entry.get("duration", 2.0)
            text = entry.get("text", "").strip()
            if not text:
                continue
            lines.append(f"\n{self._seconds_to_vtt_ts(start)} --> {self._seconds_to_vtt_ts(end)}")
            lines.append(text)
        path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _seconds_to_vtt_ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    # ------------------------------------------------------------------
    # Video download via yt-dlp (Android client bypasses bot checks)
    # ------------------------------------------------------------------

    def _ydl_progress_hook(self, d: dict):
        if self._progress_hook and d.get("status") == "downloading":
            try:
                pct = float(d.get("_percent_str", "0%").strip().replace("%", ""))
                self._progress_hook(pct)
            except ValueError:
                pass

    def _download_video(self, url: str) -> Path:
        output_template = str(self.job_dir / "video.%(ext)s")

        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": output_template,
            # Use Android client — bypasses bot detection on cloud IPs
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios", "web_creator"],
                    "player_skip": ["webpage", "configs"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "com.google.android.youtube/17.36.4 "
                    "(Linux; U; Android 12; GB) gzip"
                ),
            },
            # Also try to get subtitles as fallback (in case transcript API failed)
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt/srt/best",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._ydl_progress_hook],
            "postprocessors": [],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            logger.warning("yt-dlp download failed: %s — trying fallback client", e)
            # Fallback: try with web client + no client hints
            ydl_opts["extractor_args"] = {"youtube": {"player_client": ["web"]}}
            ydl_opts.pop("http_headers", None)
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e2:
                raise RuntimeError(
                    f"YouTube download failed on both Android and web clients.\n"
                    f"Error: {e2}\n"
                    f"Try uploading the video file directly instead of using a YouTube URL."
                ) from e2

        # Find downloaded video file
        for ext in ("mp4", "mkv", "webm", "avi", "mov"):
            p = self.job_dir / f"video.{ext}"
            if p.exists():
                return p

        for f in self.job_dir.iterdir():
            if f.suffix in {".mp4", ".mkv", ".webm", ".avi", ".mov"}:
                return f

        raise FileNotFoundError(f"No video file found in {self.job_dir}")

    def _collect_subtitle_files(self, subtitle_language: str) -> list[str]:
        patterns = [
            str(self.job_dir / f"video.{subtitle_language}.vtt"),
            str(self.job_dir / f"video.{subtitle_language}.srt"),
            str(self.job_dir / f"video.{subtitle_language}.auto.vtt"),
            str(self.job_dir / f"video.{subtitle_language}.auto.srt"),
        ]
        found = []
        for pattern in patterns:
            found.extend(glob.glob(pattern))

        if not found:
            for ext in ("vtt", "srt"):
                found.extend(glob.glob(str(self.job_dir / f"*.{ext}")))

        seen, unique = set(), []
        for f in found:
            if f not in seen:
                seen.add(f)
                unique.append(f)
        return unique
