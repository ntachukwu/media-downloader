"""
WhatsApp processor — runs the post-download pipeline for WhatsApp Status.

The pipeline is not connected automatically. Call ``connect()`` at startup
to wire it to the ``download_complete`` signal:

    from adapters.whatsapp import processor
    processor.connect()

The processing order is:
1. Trim to max duration (fast stream copy, reduces data for subsequent steps).
2. Ensure H.264/AAC codec (re-encodes if needed).
3. Enforce max file size (re-encodes at lower bitrate if the file is too large).

Constraint values are read from the ``whatsapp_status`` destination adapter
so they stay in sync with the registry.
"""

from functools import partial
from pathlib import Path

from adapters.destinations.registry import get as get_destination
from adapters.whatsapp import codec, resize, trim
from domain import signals
from domain.pipeline import ProcessorFn, build_pipeline

_c = get_destination("whatsapp_status").constraints

_steps: list[ProcessorFn] = []
if _c.max_duration_seconds is not None:
    _steps.append(partial(trim.trim_to_duration, max_seconds=_c.max_duration_seconds))
_steps.append(codec.ensure_h264_aac)
if _c.max_file_mb is not None:
    _steps.append(partial(resize.enforce_max_mb, max_mb=_c.max_file_mb))

_pipeline = build_pipeline(_steps)


def _prepare_for_whatsapp(file_path: Path, **_: object) -> None:
    try:
        _pipeline(file_path)
    except Exception:
        # Processing failure must not affect the download result.
        # A future logging adapter will record errors here.
        pass


def connect() -> None:
    """Connect the WhatsApp pipeline to the ``download_complete`` signal.

    Idempotent — calling this more than once connects the receiver multiple
    times. Guard against double-calls at the call site if that matters.
    """
    signals.download_complete.connect(_prepare_for_whatsapp)
