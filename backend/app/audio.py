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


def to_rgb_jpeg(src: Path, dst: Path, max_side: int = 1024) -> None:
    """A colour JPEG of at most `max_side` pixels, for Gemma to look at.

    Old photos are often scanned as one-channel greyscale JPEGs; Gemma described an empty room
    in one of those as "at least four people". The same photo as a normal colour JPEG reads fine.
    """
    scale = f"scale='min({max_side},iw)':'min({max_side},ih)':force_original_aspect_ratio=decrease"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"{scale},format=rgb24", "-frames:v", "1", "-q:v", "3", str(dst)],
        check=True,
        capture_output=True,
    )
