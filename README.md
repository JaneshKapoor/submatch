# SubMatch — Audio-Subtitle Mismatch Detector

> **PlanetRead · DMP 2026 · Open Source · MIT License**

SubMatch automatically detects mismatches between spoken audio and on-screen subtitles in YouTube videos (or uploaded files). It compares what is *said* (Whisper ASR) against what is *shown* (subtitle file or OCR), scores every segment, and delivers an interactive HTML report — so reviewers only need to check flagged moments, not scrub through the entire video.

---

## Demo

| Timestamp | Audio (Whisper) | Subtitle | Words | Score | Status |
|-----------|-----------------|----------|-------|-------|--------|
| 00:10.20 | वो कहाँ गई थी | वो कहाँ गया था | 4 vs 4 | 0.61 | REVIEW |
| 00:45.70 | ठीक है भाई | ठीक है भाई | 3 vs 3 | 1.00 | OK |
| 01:00.00 | आज मौसम बहुत अच्छा है | आज मौसम बहुत बुरा है | 5 vs 5 | 0.72 | MARGINAL |

---

## Architecture

```
Input
├── YouTube URL  ──────────────────────────────────┐
└── Upload Video (.mp4 / .mkv / .webm) + optional  │
    Subtitle file (.vtt / .srt)                     │
                                                    ▼
                              ┌─────────────────────────────────┐
                              │      FastAPI Backend :8000       │
                              │                                  │
                              │  1. yt-dlp                       │
                              │     Download video + subtitles   │
                              │     (manual CC → auto-gen → OCR) │
                              │            │                     │
                              │  2. faster-whisper               │
                              │     Transcribe audio → segments  │
                              │     [int8 · VAD filter · local]  │
                              │            │                     │
                              │  3. Subtitle Parser              │
                              │     Parse VTT / SRT              │
                              │     OR Tesseract OCR fallback    │
                              │            │                     │
                              │  4. Mismatch Detector            │
                              │     rapidfuzz similarity score   │
                              │     + word-count delta per seg   │
                              │            │                     │
                              │  5. Report Generator             │
                              │     Standalone HTML + JSON       │
                              └──────────────┬──────────────────┘
                                             │  WebSocket (real-time progress)
                              ┌──────────────▼──────────────────┐
                              │     Next.js Frontend :3000       │
                              │                                  │
                              │  Landing page  (URL / Upload)    │
                              │  Progress page (live steps)      │
                              │  Report page   (filter / search) │
                              └─────────────────────────────────┘
```

---

## Features

- **Two input modes** — paste a YouTube URL or drag-and-drop a video file
- **faster-whisper ASR** — 4-8x faster than standard Whisper, runs 100% locally, no API key needed
- **Subtitle download** — `yt-dlp` fetches manual CC subtitles first, falls back to auto-generated
- **OCR fallback** — Tesseract reads burned-in subtitles when no subtitle file exists
- **Indic language support** — Hindi, Kannada, Tamil, Telugu, Marathi, Bengali, Gujarati, Malayalam, Punjabi
- **Word-count delta** — flags segments where word counts diverge significantly
- **rapidfuzz similarity** — Unicode-aware character-level + token-set scoring
- **Real-time progress** — WebSocket stream drives live pipeline step UI
- **Interactive HTML report** — filterable by status, searchable, downloadable, works offline

---

## Speed

All transcription runs locally — no API calls, no internet needed after first model download.

| Model | 10-min video (CPU) | Best for |
|-------|--------------------|---------|
| `tiny` | ~1 min | Quick checks |
| **`base`** | **~3-4 min** | **English, most Indic — default** |
| `small` | ~5-6 min | Better Indic accuracy |
| `medium` | ~10 min | High-accuracy Indic / mixed language |
| `large-v3` | ~20 min | Maximum accuracy |

> faster-whisper uses CTranslate2 (int8 quantization) + VAD filtering (skips silence) + greedy decoding. Same accuracy as standard Whisper at a fraction of the time.

---

## Setup

### Prerequisites

| Tool | Install |
|------|---------|
| Python >= 3.10 | [python.org](https://python.org) |
| Node.js >= 18 | [nodejs.org](https://nodejs.org) |
| ffmpeg | `brew install ffmpeg` / `apt install ffmpeg` |
| Tesseract + Indic packs | see below |

**Tesseract (macOS):**
```bash
brew install tesseract tesseract-lang
```

**Tesseract (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr \
  tesseract-ocr-hin tesseract-ocr-kan tesseract-ocr-tam \
  tesseract-ocr-tel tesseract-ocr-mar tesseract-ocr-ben
```

**Tesseract (Windows):**
Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and select Indic language packs during install.

---

### Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # defaults work out of the box

python main.py
# or: uvicorn main:app --reload --port 8000
```

The first run downloads the Whisper model weights (~150 MB for `base`). Subsequent runs load from cache instantly.

---

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

All config lives in `backend/.env` (copied from `.env.example`).

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | _(empty)_ | Optional — Whisper runs locally, not needed |
| `YOUTUBE_API_KEY` | _(empty)_ | Optional — yt-dlp works without it |
| `BACKEND_HOST` | `0.0.0.0` | Bind host |
| `BACKEND_PORT` | `8000` | Bind port |
| `FRONTEND_URL` | `http://localhost:3000` | CORS allowed origin |
| `WHISPER_MODEL` | `base` | `tiny` / `base` / `small` / `medium` / `large-v3` |
| `HIGH_THRESHOLD` | `0.85` | Score >= this → OK |
| `LOW_THRESHOLD` | `0.65` | Score >= this → MARGINAL; below → REVIEW |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/jobs` | Start analysis from YouTube URL |
| `POST` | `/api/jobs/upload` | Start analysis from uploaded video file |
| `GET` | `/api/jobs/:id` | Poll job status and progress |
| `GET` | `/api/jobs/:id/report` | Full report as JSON |
| `GET` | `/api/jobs/:id/report.html` | Standalone HTML report |
| `GET` | `/api/languages` | List supported languages |
| `WS` | `/ws/:id` | Real-time progress stream |
| `GET` | `/health` | Health check |

---

## Report Statuses

| Status | Score | Meaning |
|--------|-------|---------|
| **OK** | >= 0.85 | Audio and subtitle match well |
| **MARGINAL** | 0.65 – 0.84 | Differences exist — worth a quick look |
| **REVIEW** | < 0.65 | Significant mismatch — flag for editor |
| **MISSING** | — | No subtitle segment found for this audio segment |

---

## Project Structure

```
submatch/
├── backend/
│   ├── main.py                  # FastAPI app, pipeline orchestration, WebSocket
│   ├── requirements.txt
│   ├── .env.example             # copy to .env before running
│   ├── config/
│   │   └── settings.py          # Pydantic settings + language map
│   ├── modules/
│   │   ├── downloader.py        # yt-dlp: download video + subtitles
│   │   ├── transcriber.py       # faster-whisper ASR (local, int8)
│   │   ├── subtitle_parser.py   # VTT + SRT parser
│   │   ├── ocr_extractor.py     # Tesseract OCR fallback
│   │   ├── mismatch_detector.py # rapidfuzz scoring + word-count delta
│   │   └── report_generator.py  # Standalone HTML report
│   └── utils/
│       └── text_utils.py        # Unicode NFC normalization for Indic scripts
└── frontend/
    ├── app/
    │   ├── page.tsx             # Landing page — YouTube URL + file upload tabs
    │   ├── analyze/[id]/        # Real-time progress page
    │   └── report/[id]/         # Interactive report viewer
    ├── components/ui/
    │   ├── aurora-background.tsx
    │   ├── button.tsx
    │   ├── badge.tsx
    │   └── card.tsx
    └── lib/
        ├── api.ts               # API client (REST + WebSocket)
        ├── types.ts             # TypeScript types
        └── utils.ts             # Tailwind utility
```

---

## Supported Languages

| Code | Language | Script |
|------|----------|--------|
| `hi` | Hindi | हिन्दी |
| `kn` | Kannada | ಕನ್ನಡ |
| `en` | English | Latin |
| `ta` | Tamil | தமிழ் |
| `te` | Telugu | తెలుగు |
| `mr` | Marathi | मराठी |
| `bn` | Bengali | বাংলা |
| `gu` | Gujarati | ગુજરાતી |
| `ml` | Malayalam | മലയാളം |
| `pa` | Punjabi | ਪੰਜਾਬੀ |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, TypeScript, Radix UI |
| Backend | Python 3.10+, FastAPI, uvicorn |
| ASR | faster-whisper (CTranslate2, int8, runs locally) |
| Download | yt-dlp |
| Subtitle parsing | webvtt-py + custom SRT parser |
| OCR | Tesseract 5 + pytesseract + OpenCV |
| Text similarity | rapidfuzz |
| Report | Standalone HTML with Tailwind CDN |
| Real-time | WebSocket |

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss what you'd like to change.

---

## License

MIT
