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
        """Return True for audio-only formats, False for video containers.

        Returns:
            True if the format carries audio only (mp3, m4a, wav);
            False for video containers (mp4, mkv, webm).
        """
        return self in (MediaFormat.MP3, MediaFormat.M4A, MediaFormat.WAV)


@dataclass(frozen=True)
class DownloadRequest:
    """Everything needed to describe a download — nothing more.

    Attributes:
        url: The media URL to download. Must not be blank.
        format: Target container or codec format.
        out_dir: Directory where the output file will be written.

    Raises:
        ValueError: If *url* is blank or contains only whitespace.
    """

    url: str
    format: MediaFormat
    out_dir: str

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("URL cannot be empty")


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a completed download.

    Attributes:
        request: The original request that produced this result.
        file_path: Path to the downloaded file on disk.
        success: True if the download completed without error.
        error: Human-readable error message; None on success.
    """

    request: DownloadRequest
    file_path: Path
    success: bool
    error: str | None = None
