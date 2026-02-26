from unittest.mock import MagicMock, patch

from adapters.ytdlp_downloader import YtDlpDownloader
from domain.models import DownloadRequest, MediaFormat


def make_request(fmt=MediaFormat.MP4, out="/tmp"):
    return DownloadRequest(url="http://x.com/v", format=fmt, out_dir=out)


class TestYtDlpDownloader:
    def _run(self, request):
        mock_ydl = MagicMock()
        with patch("adapters.ytdlp_downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.return_value = mock_ydl
            result = YtDlpDownloader().download(request)
        return result, mock_ydl, MockYDL

    def test_successful_download_returns_success(self):
        result, _, _ = self._run(make_request())
        assert result.success

    def test_url_passed_to_ydl(self):
        _, mock_ydl, _ = self._run(make_request())
        mock_ydl.download.assert_called_once_with(["http://x.com/v"])

    def test_video_format_uses_video_convertor(self):
        _, _, MockYDL = self._run(make_request(fmt=MediaFormat.MP4))
        opts = MockYDL.call_args[0][0]
        assert opts["postprocessors"][0]["key"] == "FFmpegVideoConvertor"

    def test_audio_format_uses_audio_extractor(self):
        _, _, MockYDL = self._run(make_request(fmt=MediaFormat.MP3))
        opts = MockYDL.call_args[0][0]
        assert opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"

    def test_audio_format_selects_bestaudio(self):
        _, _, MockYDL = self._run(make_request(fmt=MediaFormat.MP3))
        opts = MockYDL.call_args[0][0]
        assert opts["format"] == "bestaudio/best"

    def test_video_format_selects_bestvideo(self):
        _, _, MockYDL = self._run(make_request(fmt=MediaFormat.MP4))
        opts = MockYDL.call_args[0][0]
        assert opts["format"] == "bestvideo+bestaudio/best"

    def test_ydlp_exception_returns_failure(self):
        with patch("adapters.ytdlp_downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.side_effect = Exception("network error")
            result = YtDlpDownloader().download(make_request())
        assert not result.success
        assert "network error" in result.error

    def test_tiktok_url_is_passed_through_unchanged(self):
        # The source site is irrelevant — yt-dlp handles routing internally.
        # Our code must not inspect or transform the URL.
        tiktok_url = "https://www.tiktok.com/@user/video/1234567890"
        request = DownloadRequest(url=tiktok_url, format=MediaFormat.MP4, out_dir="/tmp")
        _, mock_ydl, _ = self._run(request)
        mock_ydl.download.assert_called_once_with([tiktok_url])
