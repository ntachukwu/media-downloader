"""
Integration tests — junction: use case ↔ adapters

Wire the real LocalStorage into the use case. Keep YtDlpDownloader faked
so no network or ffmpeg is required, but everything else is real.

These tests catch wiring mistakes that unit tests with fakes cannot:
- Use case calls storage with the right path
- Storage creates the real directory on disk
- Result flows correctly back through the use case boundary
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from adapters.local_storage import LocalStorage
from adapters.ytdlp_downloader import YtDlpDownloader
from app.use_cases import DownloadMedia
from domain.models import DownloadRequest, DownloadResult, MediaFormat


def _fake_ydl_download(request: DownloadRequest) -> DownloadResult:
    return DownloadResult(request=request, file_path=Path(request.out_dir), success=True)


class TestUseCaseWithRealStorage:
    """Use case + real LocalStorage. Downloader is faked."""

    def test_output_directory_is_created_on_disk(self, tmp_path: Path) -> None:
        out = str(tmp_path / "downloads" / "nested")

        with patch("adapters.ytdlp_downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.return_value = MagicMock()
            result = DownloadMedia(
                downloader=YtDlpDownloader(),
                storage=LocalStorage(),
            ).execute(DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir=out))

        assert Path(out).exists()
        assert result.success

    def test_storage_creates_directory_before_download_is_attempted(self, tmp_path: Path) -> None:
        out = str(tmp_path / "out")
        call_order: list[str] = []

        class OrderedStorage:
            def ensure(self, path: str) -> Path:
                call_order.append("storage")
                return Path(path)

        class OrderedDownloader:
            def download(self, request: DownloadRequest) -> DownloadResult:
                call_order.append("download")
                return DownloadResult(request=request, file_path=Path(out), success=True)

        DownloadMedia(downloader=OrderedDownloader(), storage=OrderedStorage()).execute(
            DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir=out)
        )

        assert call_order == ["storage", "download"]

    def test_failed_download_still_leaves_directory(self, tmp_path: Path) -> None:
        out = str(tmp_path / "out")

        with patch("adapters.ytdlp_downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.side_effect = Exception("network error")
            result = DownloadMedia(
                downloader=YtDlpDownloader(),
                storage=LocalStorage(),
            ).execute(DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir=out))

        assert Path(out).exists()
        assert not result.success


class TestYtDlpAdapterWithRealRequest:
    """YtDlpDownloader + real DownloadRequest — tests the translation seam."""

    def _opts_for(self, fmt: MediaFormat) -> dict[str, object]:
        request = DownloadRequest(url="http://x.com/v", format=fmt, out_dir="/tmp")
        return YtDlpDownloader()._build_opts(request)

    def test_mp4_request_produces_video_convertor_key(self) -> None:
        opts = self._opts_for(MediaFormat.MP4)
        postprocessors = opts["postprocessors"]
        assert isinstance(postprocessors, list)
        assert postprocessors[0]["key"] == "FFmpegVideoConvertor"

    def test_mp3_request_produces_audio_extractor_key(self) -> None:
        opts = self._opts_for(MediaFormat.MP3)
        postprocessors = opts["postprocessors"]
        assert isinstance(postprocessors, list)
        assert postprocessors[0]["key"] == "FFmpegExtractAudio"

    def test_out_dir_appears_in_output_template(self) -> None:
        request = DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir="/my/dir")
        opts = YtDlpDownloader()._build_opts(request)
        assert "/my/dir" in str(opts["outtmpl"])

    def test_all_video_formats_produce_video_convertor(self) -> None:
        for fmt in (MediaFormat.MP4, MediaFormat.MKV, MediaFormat.WEBM):
            opts = self._opts_for(fmt)
            postprocessors = opts["postprocessors"]
            assert isinstance(postprocessors, list)
            assert postprocessors[0]["key"] == "FFmpegVideoConvertor", f"Failed for {fmt}"

    def test_all_audio_formats_produce_audio_extractor(self) -> None:
        for fmt in (MediaFormat.MP3, MediaFormat.M4A, MediaFormat.WAV):
            opts = self._opts_for(fmt)
            postprocessors = opts["postprocessors"]
            assert isinstance(postprocessors, list)
            assert postprocessors[0]["key"] == "FFmpegExtractAudio", f"Failed for {fmt}"
