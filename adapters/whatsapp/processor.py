"""
WhatsApp processor — runs the post-download pipeline for WhatsApp Status.

The pipeline is not connected automatically. Call ``connect()`` at startup
to wire it to the ``download_complete`` signal:

    from adapters.whatsapp import processor
    processor.connect()

Processing steps, in order:

1. Reject if total duration exceeds the maximum splittable length (4m30s).
   A message is printed and preparation is skipped.
2. Split into sequential parts of at most 90 seconds each.
   The original file is kept; parts are written alongside it as
   ``<stem>_part1.mp4``, ``<stem>_part2.mp4``, etc.
3. For each part: ensure H.264/AAC codec, then enforce the 16 MB size limit.

Constraint values are read from the ``whatsapp_status`` destination adapter
so they stay in sync with the registry.
"""

from functools import partial
from pathlib import Path

from adapters.destinations.registry import get as get_destination
from adapters.whatsapp import codec, resize, split
from adapters.whatsapp._ffmpeg import probe_duration
from domain import signals
from domain.pipeline import ProcessorFn, build_pipeline

_c = get_destination("whatsapp_status").constraints

# Videos longer than this are rejected: 3 x max_duration_seconds = 4m30s.
MAX_TOTAL_SECONDS: int = 3 * (_c.max_duration_seconds or 90)

# Post-split pipeline: codec + resize (no trim — each part is already ≤ 90s).
_post_split_steps: list[ProcessorFn] = [codec.ensure_h264_aac]
if _c.max_file_mb is not None:
    _post_split_steps.append(partial(resize.enforce_max_mb, max_mb=_c.max_file_mb))

_post_split_pipeline = build_pipeline(_post_split_steps)


def _warn_too_long(duration: float) -> None:
    mins = int(duration) // 60
    secs = int(duration) % 60
    max_mins = MAX_TOTAL_SECONDS // 60
    max_secs = MAX_TOTAL_SECONDS % 60
    print(
        f"\nVideo too long for WhatsApp ({mins}m{secs:02d}s). "
        f"Maximum is {max_mins}m{max_secs:02d}s. "
        "Skipping WhatsApp preparation."
    )


def _prepare_for_whatsapp(file_path: Path, **_: object) -> None:
    try:
        duration = probe_duration(file_path)
        if duration is not None and duration > MAX_TOTAL_SECONDS:
            _warn_too_long(duration)
            return

        part_duration = _c.max_duration_seconds or 90
        parts = split.split_by_duration(file_path, max_seconds=part_duration)
        for part in parts:
            _post_split_pipeline(part)
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
