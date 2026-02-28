"""
Ports — the contracts this application depends on.

These are interfaces (Python Protocols). The application layer only
ever talks to these. Adapters implement them. Nothing in domain/ or
app/ imports from adapters/.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from domain.models import DownloadRequest, DownloadResult


@runtime_checkable
class Downloader(Protocol):
    """Knows how to fetch media from a URL."""

    def download(self, request: DownloadRequest) -> DownloadResult: ...


@runtime_checkable
class Storage(Protocol):
    """Knows how to prepare and resolve output paths."""

    def ensure(self, path: str) -> Path:
        """Create directory if needed, return resolved Path."""
        ...


@dataclass(frozen=True)
class DestinationConstraints:
    """Platform constraints for a download destination.

    Fields that are `None` carry no limit for that dimension.
    `last_verified` is an ISO-8601 date string (``YYYY-MM-DD``) that
    records when the values were last confirmed against the platform's
    published limits.
    """

    max_duration_seconds: int | None  # None = no limit
    max_file_mb: int | None  # None = no limit
    preferred_aspect: str | None  # "9:16", "1:1", "16:9", None = any
    required_codec: str  # "h264", "h265", "any"
    last_verified: str  # ISO-8601 date — staleness indicator


@runtime_checkable
class Destination(Protocol):
    """A platform that media can be shared to.

    Concrete adapters declare ``name`` and ``label`` as class attributes
    and implement ``constraints`` as a property.
    """

    name: str  # machine key, e.g. "whatsapp_status"
    label: str  # human-readable label, e.g. "WhatsApp Status"

    @property
    def constraints(self) -> DestinationConstraints: ...
