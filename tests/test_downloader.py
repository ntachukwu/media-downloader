import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from downloader import build_opts, ensure_dir, run_download


# ---------------------------------------------------------------------------
# build_opts
# ---------------------------------------------------------------------------

class TestBuildOpts:
    def test_output_template_contains_out_dir(self):
        opts = build_opts("http://x.com/v", "mp4", "/tmp/vids")
        assert opts["outtmpl"].startswith("/tmp/vids/")

    def test_output_template_uses_title_placeholder(self):
        opts = build_opts("http://x.com/v", "mp4", "/tmp/vids")
        assert "%(title)s" in opts["outtmpl"]

    def test_format_is_set_in_postprocessor(self):
        opts = build_opts("http://x.com/v", "mkv", "/tmp/vids")
        pp = opts["postprocessors"][0]
        assert pp["preferedformat"] == "mkv"

    def test_postprocessor_is_ffmpeg_convertor(self):
        opts = build_opts("http://x.com/v", "mp4", "/tmp/vids")
        pp = opts["postprocessors"][0]
        assert pp["key"] == "FFmpegVideoConvertor"

    def test_source_format_is_best_quality(self):
        opts = build_opts("http://x.com/v", "mp4", "/tmp/vids")
        assert opts["format"] == "bestvideo+bestaudio/best"

    def test_different_formats_produce_different_opts(self):
        opts_mp4 = build_opts("http://x.com/v", "mp4", "/out")
        opts_mkv = build_opts("http://x.com/v", "mkv", "/out")
        assert opts_mp4["postprocessors"][0]["preferedformat"] != \
               opts_mkv["postprocessors"][0]["preferedformat"]

    def test_different_dirs_produce_different_templates(self):
        opts_a = build_opts("http://x.com/v", "mp4", "/dir_a")
        opts_b = build_opts("http://x.com/v", "mp4", "/dir_b")
        assert opts_a["outtmpl"] != opts_b["outtmpl"]


# ---------------------------------------------------------------------------
# ensure_dir
# ---------------------------------------------------------------------------

class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        target = tmp_path / "new" / "nested"
        ensure_dir(str(target))
        assert target.exists()

    def test_returns_path_object(self, tmp_path):
        result = ensure_dir(str(tmp_path / "out"))
        assert isinstance(result, Path)

    def test_is_idempotent(self, tmp_path):
        target = tmp_path / "out"
        ensure_dir(str(target))
        ensure_dir(str(target))  # should not raise
        assert target.exists()

    def test_existing_dir_is_not_overwritten(self, tmp_path):
        sentinel = tmp_path / "sentinel.txt"
        sentinel.write_text("keep me")
        ensure_dir(str(tmp_path))
        assert sentinel.read_text() == "keep me"


# ---------------------------------------------------------------------------
# run_download
# ---------------------------------------------------------------------------

class TestRunDownload:
    def test_calls_ydl_download_with_url(self):
        mock_ydl = MagicMock()
        opts = {"format": "bestvideo+bestaudio/best", "quiet": True}
        with patch("downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.return_value = mock_ydl
            run_download("http://x.com/v", opts)
        mock_ydl.download.assert_called_once_with(["http://x.com/v"])

    def test_passes_opts_to_ydl_constructor(self):
        opts = {"format": "best", "quiet": True}
        with patch("downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.return_value = MagicMock()
            run_download("http://x.com/v", opts)
        MockYDL.assert_called_once_with(opts)

    def test_uses_context_manager(self):
        opts = {}
        with patch("downloader.yt_dlp.YoutubeDL") as MockYDL:
            ctx = MockYDL.return_value
            ctx.__enter__.return_value = MagicMock()
            ctx.__exit__.return_value = False
            run_download("http://x.com/v", opts)
        ctx.__enter__.assert_called_once()
        ctx.__exit__.assert_called_once()

    def test_different_urls_are_passed_through(self):
        mock_ydl = MagicMock()
        with patch("downloader.yt_dlp.YoutubeDL") as MockYDL:
            MockYDL.return_value.__enter__.return_value = mock_ydl
            run_download("http://vimeo.com/123", {})
        mock_ydl.download.assert_called_once_with(["http://vimeo.com/123"])
