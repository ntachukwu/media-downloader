"""
Codec step — ensures the video uses H.264 video and AAC audio.

Probes the file first; skips re-encoding if both streams already use
the required codecs.
"""

import subprocess
from pathlib import Path

from adapters.whatsapp._ffmpeg import probe_audio_codec, probe_video_codec, tmp_path


def ensure_h264_aac(path: Path) -> Path:
    """Re-encode the video to H.264/AAC if it uses other codecs.

    Returns ``path`` unchanged if both the video and audio streams already
    use the required codecs.
    """
    if probe_video_codec(path) == "h264" and probe_audio_codec(path) == "aac":
        return path

    tmp = tmp_path(path)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(tmp),
        ],
        check=True,
        capture_output=True,
    )
    tmp.replace(path)
    return path
