"""
OCR-based subtitle extractor — fallback when no subtitle file is available.

Captures a frame at the midpoint of each Whisper audio segment,
crops the bottom 15% (where subtitles typically appear),
and runs Tesseract OCR with the appropriate Indic language pack.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

logger = logging.getLogger(__name__)

SUBTITLE_REGION_RATIO = 0.15  # bottom 15% of frame


class OCRExtractor:
    def __init__(
        self,
        language: str = "hi",
        progress_hook: Callable | None = None,
    ):
        """
        Parameters
        ----------
        language : str
            yt-dlp / BCP-47 language code (e.g. 'hi', 'kn', 'en').
            Mapped to Tesseract language pack internally.
        """
        from config.settings import SUPPORTED_LANGUAGES

        lang_info = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES["en"])
        self._tess_lang = lang_info["tesseract"]
        self._progress_hook = progress_hook

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_video(
        self,
        video_path: str,
        audio_segments: list[dict],
    ) -> list[dict]:
        """
        For each audio segment, OCR the frame at its midpoint.

        Returns
        -------
        list of { "start": float, "end": float, "text": str }
        """
        import pytesseract

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        results = []

        for i, seg in enumerate(audio_segments):
            midpoint = (seg["start"] + seg["end"]) / 2.0
            frame_no = int(midpoint * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ok, frame = cap.read()
            if not ok:
                logger.warning("Could not read frame %d (t=%.2fs)", frame_no, midpoint)
                results.append({"start": seg["start"], "end": seg["end"], "text": ""})
                continue

            cropped = self._crop_subtitle_region(frame)
            preprocessed = self._preprocess(cropped)
            text = self._run_ocr(pytesseract, preprocessed)

            results.append(
                {"start": seg["start"], "end": seg["end"], "text": text.strip()}
            )

            if self._progress_hook and i % 10 == 0:
                self._progress_hook(i / len(audio_segments))

        cap.release()
        logger.info("OCR extracted text for %d segments", len(results))
        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _crop_subtitle_region(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        crop_top = int(h * (1 - SUBTITLE_REGION_RATIO))
        return frame[crop_top:h, 0:w]

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """Improve OCR accuracy: grayscale → denoise → threshold."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Upscale for better OCR
        scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # Adaptive threshold works better than simple binary for varied backgrounds
        thresh = cv2.adaptiveThreshold(
            scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return thresh

    def _run_ocr(self, pytesseract, img: np.ndarray) -> str:
        config = (
            f"--oem 3 --psm 6 -l {self._tess_lang}"
            " -c tessedit_char_blacklist=|"
        )
        try:
            return pytesseract.image_to_string(img, config=config)
        except Exception as exc:
            logger.warning("Tesseract error: %s", exc)
            return ""
