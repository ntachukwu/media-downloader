"""
Resize step — re-encodes the video to stay within a file-size limit.

Computes a target bitrate from the file size limit and video duration,
then re-encodes with a 5 % headroom to account for container overhead.
"""

import subprocess
from pathlib import Path

from adapters.whatsapp._ffmpeg import probe_duration, tmp_path


def enforce_max_mb(path: Path, max_mb: int) -> Path:
    """Re-encode the video so that its file size stays within ``max_mb``.

    Returns ``path`` unchanged if the file is already within the limit, or
    if the duration cannot be determined (bitrate calculation requires it).
    """
    limit_bytes = max_mb * 1024 * 1024
    if path.stat().st_size <= limit_bytes:
        return path

    duration = probe_duration(path)
    if duration is None:
        return path  # cannot calculate target bitrate without duration

    # 5 % headroom for container and audio overhead
    target_bps = int((limit_bytes * 8) / duration * 0.95)

    tmp = tmp_path(path)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-b:v",
            str(target_bps),
            "-maxrate",
            str(target_bps),
            "-bufsize",
            str(target_bps * 2),
            str(tmp),
        ],
        check=True,
        capture_output=True,
    )
    tmp.replace(path)
    return path
