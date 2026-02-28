"""
Internal ffprobe utilities shared across whatsapp adapter modules.

Not part of the public API — import only from within adapters/whatsapp/.
"""

import subprocess
from pathlib import Path


def probe_duration(path: Path) -> float | None:
    """Return the video duration in seconds, or ``None`` if the probe fails."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def probe_video_codec(path: Path) -> str:
    """Return the video stream codec name, or an empty string if not found."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def probe_audio_codec(path: Path) -> str:
    """Return the audio stream codec name, or an empty string if not found."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def tmp_path(path: Path) -> Path:
    """Return a temporary path next to ``path`` for in-place processing."""
    return path.with_stem(path.stem + ".tmp")
