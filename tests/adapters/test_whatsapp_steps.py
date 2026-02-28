"""
WhatsApp adapter tests — trim, codec, resize, split, and processor.

Each test that modifies a file uses a per-test copy from conftest.py so
session-scoped fixtures remain intact.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from adapters.whatsapp import codec, resize, split, trim
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


class TestSplitByDuration:
    def test_returns_single_path_when_within_limit(self, h264_video: Path) -> None:
        result = split.split_by_duration(h264_video, max_seconds=10)
        assert result == [h264_video]

    def test_original_is_unchanged_when_within_limit(self, h264_video: Path) -> None:
        size_before = h264_video.stat().st_size
        split.split_by_duration(h264_video, max_seconds=10)
        assert h264_video.stat().st_size == size_before

    def test_splits_into_correct_number_of_parts(self, h264_video: Path) -> None:
        # 3s video split at 1s → 3 parts
        parts = split.split_by_duration(h264_video, max_seconds=1)
        assert len(parts) == 3

    def test_part_paths_follow_naming_convention(self, h264_video: Path) -> None:
        parts = split.split_by_duration(h264_video, max_seconds=1)
        stems = [p.stem for p in parts]
        assert stems == ["h264_part1", "h264_part2", "h264_part3"]

    def test_each_part_is_within_duration_limit(self, h264_video: Path) -> None:
        parts = split.split_by_duration(h264_video, max_seconds=1)
        for part in parts:
            duration = probe_duration(part)
            assert duration is not None
            assert duration <= 1.5  # 0.5s tolerance for keyframe alignment

    def test_original_file_is_preserved_after_split(self, h264_video: Path) -> None:
        split.split_by_duration(h264_video, max_seconds=1)
        assert h264_video.exists()

    def test_part_files_exist_on_disk(self, h264_video: Path) -> None:
        parts = split.split_by_duration(h264_video, max_seconds=1)
        for part in parts:
            assert part.exists()

    def test_split_two_parts(self, h264_video: Path) -> None:
        # 3s video split at 2s → 2 parts
        parts = split.split_by_duration(h264_video, max_seconds=2)
        assert len(parts) == 2


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

    def test_prepare_for_whatsapp_warns_when_too_long(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from adapters.whatsapp import processor

        video = tmp_path / "long.mp4"
        video.touch()

        with patch(
            "adapters.whatsapp.processor.probe_duration",
            return_value=float(processor.MAX_TOTAL_SECONDS + 1),
        ):
            processor._prepare_for_whatsapp(file_path=video)

        out = capsys.readouterr().out
        assert "too long" in out.lower()
        assert "4m30s" in out

    def test_prepare_for_whatsapp_does_not_warn_at_exact_limit(
        self, h264_video: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from adapters.whatsapp import processor

        with patch(
            "adapters.whatsapp.processor.probe_duration",
            return_value=float(processor.MAX_TOTAL_SECONDS),
        ):
            processor._prepare_for_whatsapp(file_path=h264_video)

        out = capsys.readouterr().out
        assert "too long" not in out.lower()
