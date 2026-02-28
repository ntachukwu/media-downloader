"""
Split step — divides a video into sequential parts of a fixed maximum duration.

Each part uses stream copy (``-c copy``) for speed. Split points are
keyframe-aligned by ffmpeg, so actual part durations may be slightly shorter
than ``max_seconds``. The original file is never modified or deleted.

Output naming: ``<stem>_part1.mp4``, ``<stem>_part2.mp4``, etc., next to
the original file.
"""

import math
import subprocess
from pathlib import Path

from adapters.whatsapp._ffmpeg import probe_duration


def split_by_duration(path: Path, max_seconds: int) -> list[Path]:
    """Split the video into parts of at most ``max_seconds`` each.

    Returns ``[path]`` unchanged if the video is already within the limit
    or if the duration cannot be determined. Otherwise returns a list of
    part paths. The number of parts is ``ceil(duration / max_seconds)``.
    """
    duration = probe_duration(path)
    if duration is None or duration <= max_seconds:
        return [path]

    n_parts = math.ceil(duration / max_seconds)
    parts: list[Path] = []

    for i in range(n_parts):
        start = i * max_seconds
        part_path = path.with_stem(f"{path.stem}_part{i + 1}")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-i",
                str(path),
                "-t",
                str(max_seconds),
                "-c",
                "copy",
                str(part_path),
            ],
            check=True,
            capture_output=True,
        )
        parts.append(part_path)

    return parts
