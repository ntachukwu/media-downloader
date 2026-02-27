"""
CLI progress receiver — connects to domain signals and prints to stdout.

Connect at startup in cli.py:
    from adapters import cli_progress  # noqa: F401  (side-effect import)
"""

from pathlib import Path
from typing import Any

from domain import signals


def _on_start(url: str, **_: Any) -> None:
    print(f"Downloading: {url}")


def _on_complete(file_path: Path, **_: Any) -> None:
    print(f"\nSaved to {file_path}")


def _on_failed(error: str, **_: Any) -> None:
    print(f"\nFailed: {error}")


signals.download_started.connect(_on_start)
signals.download_complete.connect(_on_complete)
signals.download_failed.connect(_on_failed)
