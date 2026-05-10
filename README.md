# Audio-Subtitle Mismatch Detector

**Organisation:** PlanetRead  
**Domain:** Education  
**License:** MIT  

An open-source tool that automatically detects mismatches between spoken audio and on-screen subtitles in YouTube videos. It compares what is *said* (Whisper ASR) against what is *shown* (downloaded subtitle file or OCR), flags divergent timestamps, and delivers a beautiful interactive HTML report — so QA teams only review what actually needs checking.

---

## Features

- **YouTube integration** — paste any URL; `yt-dlp` downloads video + subtitles automatically
- **Whisper ASR** — OpenAI Whisper (local, no API key) transcribes audio in 100+ languages
- **Subtitle download** — manual CC and auto-generated subtitles fetched via `yt-dlp`
- **OCR fallback** — Tesseract OCR reads burned-in subtitles when no subtitle file exists
- **Indic language support** — Hindi (Devanagari), Kannada, Tamil, Telugu, Marathi, Bengali, and more
- **rapidfuzz similarity** — Unicode-aware character-level + token-set scoring
- **Interactive HTML report** — filterable, searchable, color-coded; works offline
- **Real-time progress** — WebSocket stream drives a live progress UI
- **REST API** — fully documented FastAPI backend

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│               Next.js Frontend (port 3000)       │
│  Landing page → Progress tracker → Report viewer │
└───────────────────┬─────────────────────────────┘
                    │ REST + WebSocket
┌───────────────────▼─────────────────────────────┐
│              FastAPI Backend (port 8000)          │
│                                                  │
│  POST /api/jobs          → start analysis job    │
│  GET  /api/jobs/:id      → poll job status       │
│  GET  /api/jobs/:id/report     → report JSON     │
│  GET  /api/jobs/:id/report.html → standalone HTML│
│  WS   /ws/:id            → real-time progress    │
│                                                  │
│  Pipeline (runs in background thread):           │
│  1. yt-dlp  → download video + subtitles         │
│  2. Whisper → transcribe audio → segments        │
│  3. SubtitleParser → parse VTT/SRT               │
│     (or OCRExtractor → Tesseract fallback)       │
│  4. MismatchDetector → align + score segments    │
│  5. ReportGenerator → write HTML + JSON          │
└──────────────────────────────────────────────────┘
```

---

## Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.10 | Backend |
| Node.js | ≥ 18 | Frontend |
| Tesseract OCR | ≥ 4.1 | OCR fallback |
| ffmpeg | any recent | Whisper audio extraction |

#### Install Tesseract with Indic language packs

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian:**
```bash
sudo apt-get install tesseract-ocr \
  tesseract-ocr-hin \   # Hindi
  tesseract-ocr-kan \   # Kannada
  tesseract-ocr-tam \   # Tamil
  tesseract-ocr-tel \   # Telugu
  tesseract-ocr-mar \   # Marathi
  tesseract-ocr-ben     # Bengali
```

**Windows:**  
Download the installer from https://github.com/UB-Mannheim/tesseract/wiki and select Indic language packs during install.

#### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

---

### Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start the backend
python main.py
# or: uvicorn main:app --reload --port 8000
```

The first run downloads the Whisper model (~1.5 GB for `medium`). Subsequent runs are instant.

---

### Frontend setup

```bash
cd frontend

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

All configuration lives in `backend/.env` (copy from `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | Optional — use cloud Whisper API instead of local |
| `YOUTUBE_API_KEY` | _(empty)_ | Optional — not needed, `yt-dlp` works without it |
| `BACKEND_HOST` | `0.0.0.0` | Backend bind host |
| `BACKEND_PORT` | `8000` | Backend port |
| `FRONTEND_URL` | `http://localhost:3000` | CORS allowed origin |
| `WHISPER_MODEL` | `medium` | `tiny` / `base` / `small` / `medium` / `large-v3` |
| `MAX_CONCURRENT_JOBS` | `2` | Concurrent pipeline threads |
| `HIGH_THRESHOLD` | `0.85` | Score ≥ this → OK (green) |
| `LOW_THRESHOLD` | `0.65` | Score ≥ this → MARGINAL (yellow); below → REVIEW (red) |

---

## Usage

1. Open [http://localhost:3000](http://localhost:3000)
2. Paste a YouTube URL (any video with subtitles — auto-generated or manual CC)
3. Select the audio language and subtitle language
4. Click **Analyze Video**
5. Watch real-time progress as the pipeline runs
6. View the interactive report, or download the standalone HTML

### CLI usage (no frontend)

```bash
cd backend
python -c "
from modules.downloader import VideoDownloader
from modules.transcriber import AudioTranscriber
from modules.subtitle_parser import SubtitleParser
from modules.mismatch_detector import MismatchDetector
from modules.report_generator import ReportGenerator
import json, os

URL = 'https://www.youtube.com/watch?v=YOUR_VIDEO_ID'
JOB = './output'
os.makedirs(JOB, exist_ok=True)

video, subs = VideoDownloader(JOB).download(URL, subtitle_language='hi')
audio_segs = AudioTranscriber('medium').transcribe(video, language='hi')
sub_segs   = SubtitleParser().parse(subs[0]) if subs else []
results    = MismatchDetector(0.85, 0.65).compare(audio_segs, sub_segs)
ReportGenerator().generate(results, URL, JOB + '/report.html')
print('Report saved to', JOB + '/report.html')
"
```

---

## Report Format

| Column | Description |
|--------|-------------|
| Time | Segment start time (MM:SS.ss) |
| Audio (Whisper) | Text transcribed from the audio track |
| Subtitle | Text from the subtitle file or OCR |
| Score | Similarity score 0.00 – 1.00 |
| Status | OK / MARGINAL / REVIEW / MISSING |

**Example:**

| Time | Audio | Subtitle | Score | Status |
|------|-------|----------|-------|--------|
| 00:10.20 | वो कहाँ गई थी | वो कहाँ गया था | 0.61 | REVIEW |
| 00:45.70 | ठीक है भाई | ठीक है भाई | 0.97 | OK |

---

## Project Structure

```
dmp_2026/
├── backend/
│   ├── main.py                    # FastAPI app + pipeline orchestration
│   ├── requirements.txt
│   ├── .env.example               # ← copy to .env and add your keys
│   ├── config/
│   │   └── settings.py            # Pydantic settings + language map
│   ├── modules/
│   │   ├── downloader.py          # yt-dlp YouTube downloader
│   │   ├── transcriber.py         # Whisper ASR
│   │   ├── subtitle_parser.py     # VTT / SRT parser
│   │   ├── ocr_extractor.py       # Tesseract OCR fallback
│   │   ├── mismatch_detector.py   # rapidfuzz similarity + flagging
│   │   └── report_generator.py    # Standalone HTML report
│   └── utils/
│       └── text_utils.py          # Unicode normalization for Indic scripts
└── frontend/
    ├── app/
    │   ├── page.tsx               # Landing + URL input form
    │   ├── analyze/[id]/page.tsx  # Real-time progress page
    │   └── report/[id]/page.tsx   # Interactive report viewer
    ├── lib/
    │   ├── api.ts                 # Backend API client
    │   └── types.ts               # TypeScript types
    └── ...config files
```

---

## Supported Languages

| Code | Language | Whisper | Tesseract OCR |
|------|----------|---------|---------------|
| `hi` | Hindi (हिन्दी) | ✅ | `hin` |
| `kn` | Kannada (ಕನ್ನಡ) | ✅ | `kan` |
| `en` | English | ✅ | `eng` |
| `ta` | Tamil (தமிழ்) | ✅ | `tam` |
| `te` | Telugu (తెలుగు) | ✅ | `tel` |
| `mr` | Marathi (मराठी) | ✅ | `mar` |
| `bn` | Bengali (বাংলা) | ✅ | `ben` |
| `gu` | Gujarati (ગુજરાતી) | ✅ | `guj` |
| `ml` | Malayalam (മലയാളം) | ✅ | `mal` |
| `pa` | Punjabi (ਪੰਜਾਬੀ) | ✅ | `pan` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS, TypeScript |
| Backend | Python 3.10+, FastAPI, uvicorn |
| ASR | OpenAI Whisper (local) |
| Video/subtitle download | yt-dlp |
| Subtitle parsing | webvtt-py + custom SRT parser |
| OCR | Tesseract + pytesseract + OpenCV |
| Text similarity | rapidfuzz |
| Report | Standalone HTML + Tailwind CDN |
| Real-time | WebSocket (FastAPI + browser native) |

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss what you'd like to change.

---

## License

MIT — free for personal and commercial use.
