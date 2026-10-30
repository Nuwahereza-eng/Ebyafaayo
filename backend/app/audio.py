import json
import subprocess
from pathlib import Path


def to_wav16k(src: Path, dst: Path) -> None:
    """Convert any recording (webm, m4a, mp3, ...) to 16 kHz mono WAV for the speech model."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(dst)],
        check=True,
        capture_output=True,
    )


def duration_seconds(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])
