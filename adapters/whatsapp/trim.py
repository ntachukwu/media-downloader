"""
Trim step — cuts the video to a maximum duration.

Uses ``-c copy`` (stream copy, no re-encode) for speed. Codec conversion
is a separate step handled by ``codec.ensure_h264_aac``.
"""

import subprocess
from pathlib import Path

from adapters.whatsapp._ffmpeg import probe_duration, tmp_path


def trim_to_duration(path: Path, max_seconds: int) -> Path:
    """Trim the video to ``max_seconds`` if it exceeds that duration.

    Returns ``path`` unchanged if the video is already within the limit
    or if the duration cannot be determined.
    """
    duration = probe_duration(path)
    if duration is None or duration <= max_seconds:
        return path

    tmp = tmp_path(path)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-t",
            str(max_seconds),
            "-c",
            "copy",
            str(tmp),
        ],
        check=True,
        capture_output=True,
    )
    tmp.replace(path)
    return path
