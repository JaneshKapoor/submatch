import unicodedata
import re


def normalize(text: str) -> str:
    """Normalize text for comparison: NFC, collapse whitespace, strip punctuation."""
    if not text:
        return ""

    # Unicode canonical composition (important for Indic scripts)
    text = unicodedata.normalize("NFC", text)

    # Remove HTML tags that sometimes appear in subtitle files
    text = re.sub(r"<[^>]+>", "", text)

    # Strip common subtitle formatting markers
    text = re.sub(r"\{[^}]*\}", "", text)  # {i}, {b}, etc.
    text = re.sub(r"\\[nN]", " ", text)    # \n, \N line breaks

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Keep letters (L*), combining marks/diacritics (M*), digits (N*),
    # whitespace, and the Devanagari danda (।).
    # We must NOT use \w here — it misses Indic vowel signs (category Mc/Mn).
    kept = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] in ("L", "M", "N") or ch in (" ", "।", "_"):
            kept.append(ch)
    text = "".join(kept)

    # Lower-case Latin characters (Indic scripts are case-insensitive by nature)
    text = text.lower()

    return text.strip()


def format_timestamp(seconds: float) -> str:
    """Convert float seconds → human-readable 'MM:SS.s' string."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


def seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds → SRT timestamp HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
