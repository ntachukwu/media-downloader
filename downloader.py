import yt_dlp
from pathlib import Path


def build_opts(url: str, fmt: str, out_dir: str) -> dict:
    """Build yt-dlp options for a given format and output directory."""
    return {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": fmt}],
        "quiet": True,
        "no_warnings": True,
    }


def ensure_dir(path: str) -> Path:
    """Create output directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_download(url: str, opts: dict) -> None:
    """Execute the download with the given options."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
