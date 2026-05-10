---
title: SubMatch Backend
emoji: 🎙️
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# SubMatch — Backend API

FastAPI backend for [SubMatch](https://github.com/JaneshKapoor/submatch), the audio-subtitle mismatch detector by PlanetRead.

## Endpoints

- `POST /api/jobs` — analyze a YouTube URL
- `POST /api/jobs/upload` — analyze an uploaded video file
- `GET /api/jobs/:id` — poll job status
- `GET /api/jobs/:id/report` — get report JSON
- `GET /api/jobs/:id/report.html` — download HTML report
- `WS /ws/:id` — real-time progress stream
- `GET /health` — health check

## Stack

faster-whisper · Tesseract OCR (Hindi, Kannada, Tamil, Telugu, Marathi, Bengali) · yt-dlp · OpenCV · rapidfuzz · FastAPI
