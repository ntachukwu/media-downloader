"""
Signals — Django-style decoupled event system.

Senders fire signals; receivers connect independently.
The domain never knows who is listening.

Usage:
    # connect a receiver
    from domain.signals import download_complete
    download_complete.connect(my_handler)

    # send (called by use cases)
    download_complete.send(file_path=path, request=request)

Receivers accept **kwargs so they can ignore fields they don't care about.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Signal:
    """Lightweight observer. Receivers connect; senders fire."""

    _receivers: list[Callable[..., Any]] = field(default_factory=list)

    def connect(self, receiver: Callable[..., Any]) -> None:
        self._receivers.append(receiver)

    def disconnect(self, receiver: Callable[..., Any]) -> None:
        """Remove a receiver. Useful in tests to reset state."""
        self._receivers = [r for r in self._receivers if r is not receiver]

    def send(self, **kwargs: Any) -> None:
        for receiver in self._receivers:
            receiver(**kwargs)


# Named signals — one per lifecycle event.
# kwargs documented below; receivers should accept **_ to be forward-compatible.

download_started = Signal()
"""Fired before the download begins.
kwargs: url (str)
"""

download_progress = Signal()
"""Fired periodically during download. Not yet wired to the yt-dlp progress hook.
kwargs: downloaded (int), total (int | None), speed (float | None)
"""

download_complete = Signal()
"""Fired when the download succeeds.
kwargs: file_path (Path), request (DownloadRequest)
"""

download_failed = Signal()
"""Fired when the download fails.
kwargs: error (str), request (DownloadRequest)
"""
