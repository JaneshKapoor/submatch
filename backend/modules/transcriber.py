"""
Audio transcription using OpenAI Whisper (local model, no API key needed).

Produces a list of timed segments compatible with the rest of the pipeline.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(
        self,
        model_size: str = "medium",
        progress_hook: Callable | None = None,
    ):
        self.model_size = model_size
        self._progress_hook = progress_hook
        self._model = None  # Lazy-loaded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(
        self,
        video_path: str,
        language: str | None = None,
    ) -> list[dict]:
        """
        Transcribe the audio track of `video_path`.

        Parameters
        ----------
        video_path : str  Path to the video file.
        language   : str | None  ISO 639-1 code ('hi', 'kn', 'en', …).
                     Pass None to let Whisper auto-detect.

        Returns
        -------
        List of segment dicts:
            { "start": float, "end": float, "text": str }
        """
        import whisper  # imported here so the app starts even if torch isn't installed

        logger.info("Loading Whisper model: %s", self.model_size)
        if self._model is None:
            self._model = whisper.load_model(self.model_size)

        logger.info("Transcribing: %s (language=%s)", video_path, language or "auto")

        result = self._model.transcribe(
            video_path,
            language=language,
            task="transcribe",
            verbose=False,
            fp16=False,  # safer default; GPU users can enable
        )

        segments = []
        for seg in result.get("segments", []):
            text = seg.get("text", "").strip()
            if text:
                segments.append(
                    {
                        "start": round(seg["start"], 3),
                        "end": round(seg["end"], 3),
                        "text": text,
                    }
                )

        logger.info("Transcription produced %d segments", len(segments))
        return segments
