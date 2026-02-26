"""
Ports — the contracts this application depends on.

These are interfaces (Python Protocols). The application layer only
ever talks to these. Adapters implement them. Nothing in domain/ or
app/ imports from adapters/.
"""

from typing import Protocol
from pathlib import Path
from domain.models import DownloadRequest, DownloadResult


class Downloader(Protocol):
    """Knows how to fetch media from a URL."""

    def download(self, request: DownloadRequest) -> DownloadResult:
        ...


class Storage(Protocol):
    """Knows how to prepare and resolve output paths."""

    def ensure(self, path: str) -> Path:
        """Create directory if needed, return resolved Path."""
        ...
