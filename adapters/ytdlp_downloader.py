"""
Adapter: YtDlpDownloader

Implements the Downloader port using yt-dlp.
Swap this file to change the download backend — nothing else changes.
"""

from pathlib import Path

import yt_dlp

from domain.models import DownloadRequest, DownloadResult


class YtDlpDownloader:
    """Concrete Downloader backed by yt-dlp + ffmpeg."""

    def download(self, request: DownloadRequest) -> DownloadResult:
        opts = self._build_opts(request)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([request.url])
            return DownloadResult(
                request=request,
                file_path=Path(request.out_dir),
                success=True,
            )
        except Exception as e:
            return DownloadResult(
                request=request,
                file_path=Path(request.out_dir),
                success=False,
                error=str(e),
            )

    def _build_opts(self, request: DownloadRequest) -> dict[str, object]:
        if request.format.is_audio_only:
            return {
                "format": "bestaudio/best",
                "outtmpl": f"{request.out_dir}/%(title)s.%(ext)s",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": request.format.value,
                        "preferredquality": "192",
                    }
                ],
                "quiet": True,
            }
        return {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{request.out_dir}/%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": request.format.value,
                }
            ],
            "quiet": True,
        }
