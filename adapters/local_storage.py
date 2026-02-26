"""
Adapter: LocalStorage

Implements the Storage port using the local filesystem.
Swap for S3Storage, GCSStorage, etc. without touching anything else.
"""

from pathlib import Path


class LocalStorage:
    """Concrete Storage backed by the local filesystem."""

    def ensure(self, path: str) -> Path:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p
