"""
Domain models.

Pure data — no I/O, no dependencies, no framework.
These are the nouns of the application.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class MediaFormat(StrEnum):
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"
    MP3 = "mp3"
    M4A = "m4a"
    WAV = "wav"

    @property
    def is_audio_only(self) -> bool:
        return self in (MediaFormat.MP3, MediaFormat.M4A, MediaFormat.WAV)


@dataclass(frozen=True)
class DownloadRequest:
    """Everything needed to describe a download — nothing more."""

    url: str
    format: MediaFormat
    out_dir: str

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("URL cannot be empty")


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a completed download."""

    request: DownloadRequest
    file_path: Path
    success: bool
    error: str | None = None
