"""
Shared fixtures for adapter tests that require real media files.

Session-scoped fixtures create files once; tests that modify a file
use the function-scoped ``*_copy`` variants to get a fresh copy.
"""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def tiny_h264_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """3-second 64x64 H.264/AAC MP4 — the happy-path file."""
    path = tmp_path_factory.mktemp("video") / "h264.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:size=64x64:rate=25:duration=3",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-t",
            "3",
            str(path),
        ],
        check=True,
        capture_output=True,
    )
    return path


@pytest.fixture(scope="session")
def tiny_mpeg4_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """2-second 64x64 MPEG-4 Part 2 / AAC MP4 — triggers codec re-encode."""
    path = tmp_path_factory.mktemp("video") / "mpeg4.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:size=64x64:rate=25:duration=2",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            "-t",
            "2",
            str(path),
        ],
        check=True,
        capture_output=True,
    )
    return path


@pytest.fixture()
def h264_video(tiny_h264_video: Path, tmp_path: Path) -> Path:
    """Per-test copy of the H.264 video — safe to modify in place."""
    dest = tmp_path / "h264.mp4"
    shutil.copy(tiny_h264_video, dest)
    return dest


@pytest.fixture()
def mpeg4_video(tiny_mpeg4_video: Path, tmp_path: Path) -> Path:
    """Per-test copy of the MPEG-4 video — safe to modify in place."""
    dest = tmp_path / "mpeg4.mp4"
    shutil.copy(tiny_mpeg4_video, dest)
    return dest
