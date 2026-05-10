"""
SubMatch — Audio-Subtitle Mismatch Detector
FastAPI backend with REST + WebSocket + file upload support.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    BackgroundTasks, FastAPI, File, Form, HTTPException,
    UploadFile, WebSocket, WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config.settings import settings, TEMP_PATH, SUPPORTED_LANGUAGES
from modules.downloader import VideoDownloader
from modules.transcriber import AudioTranscriber
from modules.subtitle_parser import SubtitleParser
from modules.ocr_extractor import OCRExtractor
from modules.mismatch_detector import MismatchDetector
from modules.report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SubMatch", description="Audio-Subtitle Mismatch Detector", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store ───────────────────────────────────────────────────────
jobs: dict[str, dict] = {}
job_ws_clients: dict[str, list[WebSocket]] = {}

MAX_UPLOAD_SIZE_MB = 500


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _broadcast(job_id: str):
    if job_id not in job_ws_clients:
        return
    payload = {k: v for k, v in jobs[job_id].items() if k != "report_data"}
    dead = []
    for ws in job_ws_clients[job_id]:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        job_ws_clients[job_id].remove(ws)


def _push(job_id: str, updates: dict, loop: asyncio.AbstractEventLoop):
    jobs[job_id].update(updates)
    asyncio.run_coroutine_threadsafe(_broadcast(job_id), loop).result(timeout=5)


def _new_job(job_id: str, source_label: str) -> dict:
    return {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "current_step": "Initializing…",
        "steps_completed": [],
        "error": None,
        "created_at": datetime.now().isoformat(),
        "source": source_label,
        "report_data": None,
    }


# ── Core pipeline (shared by URL and file-upload paths) ─────────────────────

def _run_pipeline(
    job_id: str,
    video_path: str,
    subtitle_paths: list[str],
    source_language: str,
    subtitle_language: str,
    whisper_model: str,
    similarity_threshold: float,
    use_ocr_fallback: bool,
    loop: asyncio.AbstractEventLoop,
):
    job_dir = TEMP_PATH / job_id
    steps_completed: list[str] = []

    def push(step: str, progress: int, done: str | None = None):
        if done and done not in steps_completed:
            steps_completed.append(done)
        _push(job_id, {
            "status": "processing",
            "progress": progress,
            "current_step": step,
            "steps_completed": list(steps_completed),
        }, loop)

    try:
        # ── Transcribe ───────────────────────────────────────────────────────
        push("Transcribing audio with Whisper…", 30)
        transcriber = AudioTranscriber(model_size=whisper_model)
        whisper_lang = None if source_language == "auto" else source_language
        audio_segments = transcriber.transcribe(video_path, language=whisper_lang)
        push("Transcription complete", 55, "Audio Transcription")

        # ── Extract subtitles ─────────────────────────────────────────────────
        subtitle_segments: list[dict] = []

        if subtitle_paths:
            push("Parsing subtitle file…", 60)
            parser = SubtitleParser()
            subtitle_segments = parser.parse(subtitle_paths[0])
            push("Subtitle parsing complete", 72, "Subtitle Extraction")
        elif use_ocr_fallback:
            push("No subtitle file — running OCR on frames…", 62)
            ocr = OCRExtractor(language=subtitle_language)
            subtitle_segments = ocr.extract_from_video(video_path, audio_segments)
            push("OCR extraction complete", 72, "Subtitle Extraction (OCR)")
        else:
            push("No subtitles available", 72, "Subtitle Extraction")

        # ── Detect mismatches ─────────────────────────────────────────────────
        push("Detecting mismatches…", 78)
        low_threshold = max(0.0, similarity_threshold - 0.20)
        detector = MismatchDetector(high_threshold=similarity_threshold, low_threshold=low_threshold)
        results = detector.compare(audio_segments, subtitle_segments)
        push("Mismatch detection complete", 88, "Mismatch Detection")

        # ── Generate report ───────────────────────────────────────────────────
        push("Generating report…", 93)
        report_path = str(job_dir / "report.html")
        source_label = jobs[job_id].get("source", "")
        generator = ReportGenerator()
        report_data = generator.generate(results=results, video_url=source_label, output_path=report_path)
        (job_dir / "report.json").write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

        _push(job_id, {
            "status": "completed",
            "progress": 100,
            "current_step": "Analysis complete!",
            "steps_completed": ["Download / Upload", "Audio Transcription", "Subtitle Extraction", "Mismatch Detection", "Report Generation"],
            "report_data": report_data,
        }, loop)

    except Exception as exc:
        logger.exception("Pipeline failed for job %s", job_id)
        _push(job_id, {
            "status": "failed",
            "progress": jobs[job_id].get("progress", 0),
            "current_step": "Error occurred",
            "error": str(exc),
        }, loop)


# ── URL-based job ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: str
    source_language: str = "auto"
    subtitle_language: str = "hi"
    whisper_model: str = "medium"
    similarity_threshold: float = 0.75
    use_ocr_fallback: bool = True


@app.post("/api/jobs")
async def create_job_from_url(req: AnalyzeRequest):
    job_id = str(uuid.uuid4())
    job_dir = TEMP_PATH / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    jobs[job_id] = _new_job(job_id, req.url)

    loop = asyncio.get_event_loop()

    def _download_then_run():
        try:
            _push(job_id, {"status": "processing", "progress": 5, "current_step": "Downloading video and subtitles…"}, loop)
            downloader = VideoDownloader(str(job_dir))
            video_path, subtitle_paths = downloader.download(req.url, subtitle_language=req.subtitle_language)
            _push(job_id, {"progress": 25, "current_step": "Download complete", "steps_completed": ["Download / Upload"]}, loop)
            _run_pipeline(
                job_id, video_path, subtitle_paths,
                req.source_language, req.subtitle_language,
                req.whisper_model, req.similarity_threshold, req.use_ocr_fallback, loop,
            )
        except Exception as exc:
            logger.exception("Download failed for job %s", job_id)
            _push(job_id, {"status": "failed", "progress": 0, "current_step": "Download failed", "error": str(exc)}, loop)

    threading.Thread(target=_download_then_run, daemon=True).start()
    return {"job_id": job_id}


# ── File-upload job ───────────────────────────────────────────────────────────

@app.post("/api/jobs/upload")
async def create_job_from_upload(
    video: UploadFile = File(...),
    subtitle_file: Optional[UploadFile] = File(None),
    source_language: str = Form("auto"),
    subtitle_language: str = Form("hi"),
    whisper_model: str = Form("medium"),
    similarity_threshold: float = Form(0.75),
    use_ocr_fallback: bool = Form(True),
):
    job_id = str(uuid.uuid4())
    job_dir = TEMP_PATH / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded video
    video_suffix = Path(video.filename or "video.mp4").suffix or ".mp4"
    video_path = job_dir / f"video{video_suffix}"
    with video_path.open("wb") as f:
        shutil.copyfileobj(video.file, f)

    # Save optional subtitle file
    subtitle_paths: list[str] = []
    if subtitle_file and subtitle_file.filename:
        sub_suffix = Path(subtitle_file.filename).suffix or ".vtt"
        sub_path = job_dir / f"subtitle{sub_suffix}"
        with sub_path.open("wb") as f:
            shutil.copyfileobj(subtitle_file.file, f)
        subtitle_paths = [str(sub_path)]

    source_label = video.filename or "uploaded_video"
    jobs[job_id] = _new_job(job_id, source_label)

    loop = asyncio.get_event_loop()

    def _run():
        _push(job_id, {
            "status": "processing", "progress": 25,
            "current_step": "File uploaded, starting transcription…",
            "steps_completed": ["Download / Upload"],
        }, loop)
        _run_pipeline(
            job_id, str(video_path), subtitle_paths,
            source_language, subtitle_language,
            whisper_model, similarity_threshold, use_ocr_fallback, loop,
        )

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id}


# ── Read endpoints ────────────────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {k: v for k, v in jobs[job_id].items() if k != "report_data"}


@app.get("/api/jobs/{job_id}/report")
async def get_report_json(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed (status: {job['status']})")
    return job.get("report_data") or {}


@app.get("/api/jobs/{job_id}/report.html")
async def get_report_html(job_id: str):
    report_path = TEMP_PATH / job_id / "report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not generated yet")
    return FileResponse(str(report_path), media_type="text/html")


@app.get("/api/languages")
async def get_languages():
    return [{"code": c, "name": i["name"]} for c, i in SUPPORTED_LANGUAGES.items()]


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/{job_id}")
async def ws_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in job_ws_clients:
        job_ws_clients[job_id] = []
    job_ws_clients[job_id].append(websocket)
    if job_id in jobs:
        await websocket.send_json({k: v for k, v in jobs[job_id].items() if k != "report_data"})
    try:
        while True:
            await asyncio.wait_for(websocket.receive_text(), timeout=30)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        if job_id in job_ws_clients and websocket in job_ws_clients[job_id]:
            job_ws_clients[job_id].remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
