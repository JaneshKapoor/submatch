from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    WHISPER_MODEL: str = "base"
    MAX_CONCURRENT_JOBS: int = 2
    TEMP_DIR: str = "./temp"

    HIGH_THRESHOLD: float = 0.85
    LOW_THRESHOLD: float = 0.65

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

TEMP_PATH = Path(settings.TEMP_DIR)
TEMP_PATH.mkdir(parents=True, exist_ok=True)

SUPPORTED_LANGUAGES = {
    "hi": {"name": "Hindi", "tesseract": "hin", "whisper": "hi"},
    "kn": {"name": "Kannada", "tesseract": "kan", "whisper": "kn"},
    "en": {"name": "English", "tesseract": "eng", "whisper": "en"},
    "ta": {"name": "Tamil", "tesseract": "tam", "whisper": "ta"},
    "te": {"name": "Telugu", "tesseract": "tel", "whisper": "te"},
    "mr": {"name": "Marathi", "tesseract": "mar", "whisper": "mr"},
    "bn": {"name": "Bengali", "tesseract": "ben", "whisper": "bn"},
    "gu": {"name": "Gujarati", "tesseract": "guj", "whisper": "gu"},
    "ml": {"name": "Malayalam", "tesseract": "mal", "whisper": "ml"},
    "pa": {"name": "Punjabi", "tesseract": "pan", "whisper": "pa"},
    "auto": {"name": "Auto-detect", "tesseract": "eng", "whisper": None},
}
