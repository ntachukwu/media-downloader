"""
WhatsApp adapter tests — trim, codec, resize, and processor.

Each test that modifies a file uses a per-test copy from conftest.py so
session-scoped fixtures remain intact.
"""

from pathlib import Path

from adapters.whatsapp import codec, resize, trim
from adapters.whatsapp._ffmpeg import probe_audio_codec, probe_duration, probe_video_codec


class TestTrimToDuration:
    def test_returns_path_unchanged_when_within_limit(self, h264_video: Path) -> None:
        result = trim.trim_to_duration(h264_video, max_seconds=10)
        assert result == h264_video

    def test_file_is_not_modified_when_within_limit(self, h264_video: Path) -> None:
        size_before = h264_video.stat().st_size
        trim.trim_to_duration(h264_video, max_seconds=10)
        assert h264_video.stat().st_size == size_before

    def test_trims_video_when_over_limit(self, h264_video: Path) -> None:
        trim.trim_to_duration(h264_video, max_seconds=1)
        duration = probe_duration(h264_video)
        assert duration is not None
        assert duration <= 1.5  # 0.5 s tolerance for keyframe alignment

    def test_trimmed_file_replaces_original(self, h264_video: Path) -> None:
        """The file is modified in place; the returned path is the same."""
        result = trim.trim_to_duration(h264_video, max_seconds=1)
        assert result == h264_video
        assert h264_video.exists()


class TestEnsureH264Aac:
    def test_returns_path_unchanged_when_already_h264_aac(self, h264_video: Path) -> None:
        result = codec.ensure_h264_aac(h264_video)
        assert result == h264_video

    def test_file_is_not_modified_when_already_h264_aac(self, h264_video: Path) -> None:
        size_before = h264_video.stat().st_size
        codec.ensure_h264_aac(h264_video)
        assert h264_video.stat().st_size == size_before

    def test_re_encodes_non_h264_video_to_h264(self, mpeg4_video: Path) -> None:
        assert probe_video_codec(mpeg4_video) == "mpeg4"
        codec.ensure_h264_aac(mpeg4_video)
        assert probe_video_codec(mpeg4_video) == "h264"

    def test_re_encoded_file_replaces_original(self, mpeg4_video: Path) -> None:
        result = codec.ensure_h264_aac(mpeg4_video)
        assert result == mpeg4_video
        assert mpeg4_video.exists()


class TestEnforceMaxMb:
    def test_returns_path_unchanged_when_within_limit(self, h264_video: Path) -> None:
        result = resize.enforce_max_mb(h264_video, max_mb=100)
        assert result == h264_video

    def test_file_is_not_modified_when_within_limit(self, h264_video: Path) -> None:
        size_before = h264_video.stat().st_size
        resize.enforce_max_mb(h264_video, max_mb=100)
        assert h264_video.stat().st_size == size_before


class TestFfmpegProbes:
    def test_probe_duration_returns_float_for_valid_video(self, tiny_h264_video: Path) -> None:
        duration = probe_duration(tiny_h264_video)
        assert duration is not None
        assert 2.5 <= duration <= 3.5

    def test_probe_duration_returns_none_for_non_existent_file(self, tmp_path: Path) -> None:
        result = probe_duration(tmp_path / "ghost.mp4")
        assert result is None

    def test_probe_video_codec_returns_h264_for_h264_video(self, tiny_h264_video: Path) -> None:
        assert probe_video_codec(tiny_h264_video) == "h264"

    def test_probe_audio_codec_returns_aac_for_aac_audio(self, tiny_h264_video: Path) -> None:
        assert probe_audio_codec(tiny_h264_video) == "aac"

    def test_probe_video_codec_returns_mpeg4_for_mpeg4_video(self, tiny_mpeg4_video: Path) -> None:
        assert probe_video_codec(tiny_mpeg4_video) == "mpeg4"


class TestWhatsAppProcessor:
    def test_connect_registers_receiver_on_download_complete(self) -> None:
        from adapters.whatsapp import processor
        from domain import signals

        signals.download_complete.disconnect(processor._prepare_for_whatsapp)
        processor.connect()
        assert processor._prepare_for_whatsapp in signals.download_complete._receivers
        signals.download_complete.disconnect(processor._prepare_for_whatsapp)

    def test_prepare_for_whatsapp_is_no_op_on_h264_aac_within_limits(
        self, h264_video: Path
    ) -> None:
        from adapters.whatsapp.processor import _prepare_for_whatsapp

        size_before = h264_video.stat().st_size
        _prepare_for_whatsapp(file_path=h264_video)
        assert h264_video.stat().st_size == size_before

    def test_prepare_for_whatsapp_swallows_exceptions_silently(self, tmp_path: Path) -> None:
        """A non-existent file must not raise — signal receivers are fault-tolerant."""
        from adapters.whatsapp.processor import _prepare_for_whatsapp

        _prepare_for_whatsapp(file_path=tmp_path / "ghost.mp4")  # no error
