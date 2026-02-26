import pytest
from domain.models import DownloadRequest, DownloadResult, MediaFormat
from pathlib import Path


class TestMediaFormat:
    def test_audio_formats_are_audio_only(self):
        for fmt in (MediaFormat.MP3, MediaFormat.M4A, MediaFormat.WAV):
            assert fmt.is_audio_only

    def test_video_formats_are_not_audio_only(self):
        for fmt in (MediaFormat.MP4, MediaFormat.MKV, MediaFormat.WEBM):
            assert not fmt.is_audio_only

    def test_format_value_is_string(self):
        assert MediaFormat.MP4.value == "mp4"


class TestDownloadRequest:
    def test_valid_request_is_created(self):
        req = DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir="/tmp")
        assert req.url == "http://x.com/v"

    def test_empty_url_raises(self):
        with pytest.raises(ValueError):
            DownloadRequest(url="   ", format=MediaFormat.MP4, out_dir="/tmp")

    def test_request_is_immutable(self):
        req = DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir="/tmp")
        with pytest.raises(Exception):
            req.url = "other"


class TestDownloadResult:
    def test_successful_result(self):
        req = DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir="/tmp")
        result = DownloadResult(request=req, file_path=Path("/tmp/vid.mp4"), success=True)
        assert result.success
        assert result.error is None

    def test_failed_result_carries_error(self):
        req = DownloadRequest(url="http://x.com/v", format=MediaFormat.MP4, out_dir="/tmp")
        result = DownloadResult(request=req, file_path=Path("/tmp"), success=False, error="404")
        assert not result.success
        assert result.error == "404"
