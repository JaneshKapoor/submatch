"""
Mismatch detector: aligns audio-transcription segments with subtitle segments
by timestamp overlap and computes a fuzzy similarity score for each pair.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Literal

from rapidfuzz import fuzz
from utils.text_utils import normalize, format_timestamp

logger = logging.getLogger(__name__)

Status = Literal["OK", "MARGINAL", "REVIEW", "MISSING"]


@dataclass
class SegmentResult:
    index: int
    start: float
    end: float
    timestamp_label: str       # "MM:SS.ss"
    audio_text: str
    subtitle_text: str
    normalized_audio: str
    normalized_subtitle: str
    score: float               # 0.0 – 1.0
    word_count_audio: int
    word_count_subtitle: int
    word_count_delta: int      # abs difference in word count
    status: Status
    has_subtitle: bool


class MismatchDetector:
    def __init__(
        self,
        high_threshold: float = 0.85,
        low_threshold: float = 0.65,
    ):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare(
        self,
        audio_segments: list[dict],
        subtitle_segments: list[dict],
    ) -> list[dict]:
        """
        Align audio and subtitle segments, score each, return result list.

        Both inputs are lists of { "start": float, "end": float, "text": str }.
        """
        results = []

        for i, audio_seg in enumerate(audio_segments):
            best_sub = self._find_best_matching_subtitle(audio_seg, subtitle_segments)

            audio_norm = normalize(audio_seg["text"])
            sub_text = best_sub["text"] if best_sub else ""
            sub_norm = normalize(sub_text)

            wc_audio = len(audio_seg["text"].split())
            wc_sub = len(sub_text.split()) if sub_text else 0

            if not best_sub or not sub_norm:
                score = 0.0
                status: Status = "MISSING"
                has_subtitle = False
            else:
                score = self._similarity(audio_norm, sub_norm)
                status = self._classify(score)
                has_subtitle = True

            result = SegmentResult(
                index=i,
                start=audio_seg["start"],
                end=audio_seg["end"],
                timestamp_label=format_timestamp(audio_seg["start"]),
                audio_text=audio_seg["text"],
                subtitle_text=sub_text,
                normalized_audio=audio_norm,
                normalized_subtitle=sub_norm,
                score=round(score, 4),
                word_count_audio=wc_audio,
                word_count_subtitle=wc_sub,
                word_count_delta=abs(wc_audio - wc_sub),
                status=status,
                has_subtitle=has_subtitle,
            )
            results.append(asdict(result))

        flagged = sum(1 for r in results if r["status"] in ("REVIEW", "MISSING"))
        logger.info(
            "Comparison complete: %d segments, %d flagged", len(results), flagged
        )
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find_best_matching_subtitle(
        self,
        audio_seg: dict,
        subtitle_segments: list[dict],
    ) -> dict | None:
        """
        Find the subtitle segment with the greatest temporal overlap with `audio_seg`.
        Falls back to nearest by distance if no overlap found.
        """
        best: dict | None = None
        best_overlap = -1.0
        best_distance = float("inf")

        a_start, a_end = audio_seg["start"], audio_seg["end"]

        for sub in subtitle_segments:
            s_start, s_end = sub["start"], sub["end"]

            # Temporal overlap (in seconds)
            overlap = max(0.0, min(a_end, s_end) - max(a_start, s_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best = sub

            # Distance between midpoints (fallback metric)
            a_mid = (a_start + a_end) / 2
            s_mid = (s_start + s_end) / 2
            dist = abs(a_mid - s_mid)
            if overlap == 0 and dist < best_distance:
                best_distance = dist
                if best_overlap == 0:
                    best = sub

        return best

    def _similarity(self, a: str, b: str) -> float:
        """
        Combine character-level and token-set similarity.
        Both handle Indic scripts well (Unicode-aware).
        """
        if not a or not b:
            return 0.0

        ratio = fuzz.ratio(a, b) / 100.0
        token_set = fuzz.token_set_ratio(a, b) / 100.0

        # Weighted average: char-level slightly favoured for Indic
        return 0.6 * ratio + 0.4 * token_set

    def _classify(self, score: float) -> Status:
        if score >= self.high_threshold:
            return "OK"
        if score >= self.low_threshold:
            return "MARGINAL"
        return "REVIEW"
