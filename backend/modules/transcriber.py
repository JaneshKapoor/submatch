"""
Audio transcription using faster-whisper (CTranslate2 backend).

faster-whisper is 4-8x faster than openai-whisper on CPU and produces
identical output. It also supports int8 quantization which halves memory
usage with negligible accuracy loss.

No API key required — model runs 100% locally on your machine.
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

# Map our model size names to faster-whisper equivalents
_MODEL_MAP = {
    "tiny":     "tiny",
    "base":     "base",
    "small":    "small",
    "medium":   "medium",
    "large":    "large-v3",
    "large-v2": "large-v2",
    "large-v3": "large-v3",
}


class AudioTranscriber:
    def __init__(
        self,
        model_size: str = "base",
        progress_hook: Callable | None = None,
    ):
        self.model_size = _MODEL_MAP.get(model_size, model_size)
        self._progress_hook = progress_hook
        self._model = None  # lazy-loaded on first use

    def transcribe(
        self,
        video_path: str,
        language: str | None = None,
    ) -> list[dict]:
        """
        Transcribe the audio track of `video_path`.

        Parameters
        ----------
        video_path : str
            Path to any video or audio file (ffmpeg handles extraction).
        language : str | None
            ISO 639-1 code ('hi', 'kn', 'en', …). None = auto-detect.

        Returns
        -------
        list[dict]  — [{ "start": float, "end": float, "text": str }, ...]
        """
        from faster_whisper import WhisperModel

        if self._model is None:
            logger.info("Loading faster-whisper model: %s (int8, cpu)", self.model_size)
            # int8 compute type: 2x less memory, ~2x faster, negligible accuracy loss
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )

        logger.info("Transcribing: %s  language=%s", video_path, language or "auto")

        segments_iter, info = self._model.transcribe(
            video_path,
            language=language,
            task="transcribe",
            beam_size=1,              # greedy decoding — 3x faster, near-identical accuracy
            vad_filter=True,          # skip silent parts — skips music/silence automatically
            vad_parameters={"min_silence_duration_ms": 500},
            word_timestamps=False,
            condition_on_previous_text=False,  # prevents hallucination loops
        )

        logger.info(
            "Detected language: %s (prob=%.2f)",
            info.language, info.language_probability,
        )

        segments: list[dict] = []
        for seg in segments_iter:
            text = seg.text.strip()
            if text:
                segments.append({
                    "start": round(seg.start, 3),
                    "end":   round(seg.end,   3),
                    "text":  text,
                })

        logger.info("Transcription complete: %d segments", len(segments))
        return segments
