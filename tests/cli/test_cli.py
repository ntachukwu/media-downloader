"""
CLI tests — junction: CLI ↔ use case

Verify the CLI correctly translates argv into a DownloadRequest
and routes it to the use case. The use case is patched — we're testing
the wiring only, not the download behaviour.
"""

from unittest.mock import MagicMock, patch

import pytest

from domain.models import MediaFormat


class TestCliConstruction:
    """CLI correctly builds a DownloadRequest from argv."""

    def _run_cli(self, argv: list[str]) -> MagicMock:
        """Run cli.main() with given argv, return the mock use case."""
        mock_result = MagicMock(success=True)
        mock_execute = MagicMock(return_value=mock_result)

        with (
            patch("sys.argv", ["cli", *argv]),
            patch("app.use_cases.DownloadMedia.execute", mock_execute),
        ):
            import cli

            cli.main()

        return mock_execute

    def test_url_is_passed_to_use_case(self) -> None:
        execute = self._run_cli(["http://x.com/v"])
        request = execute.call_args[0][0]
        assert request.url == "http://x.com/v"

    def test_default_format_is_mp4(self) -> None:
        execute = self._run_cli(["http://x.com/v"])
        request = execute.call_args[0][0]
        assert request.format == MediaFormat.MP4

    def test_format_flag_is_forwarded(self) -> None:
        execute = self._run_cli(["http://x.com/v", "--format", "mkv"])
        request = execute.call_args[0][0]
        assert request.format == MediaFormat.MKV

    def test_out_flag_is_forwarded(self) -> None:
        execute = self._run_cli(["http://x.com/v", "--out", "/my/dir"])
        request = execute.call_args[0][0]
        assert request.out_dir == "/my/dir"

    def test_default_out_dir(self) -> None:
        execute = self._run_cli(["http://x.com/v"])
        request = execute.call_args[0][0]
        assert request.out_dir == "./downloads"

    def test_failed_result_exits_with_code_1(self) -> None:
        mock_result = MagicMock(success=False, error="boom")
        with (
            patch("sys.argv", ["cli", "http://x.com/v"]),
            patch("app.use_cases.DownloadMedia.execute", return_value=mock_result),
            pytest.raises(SystemExit) as exc,
        ):
            import cli

            cli.main()
        assert exc.value.code == 1

    def test_invalid_format_exits(self) -> None:
        with (
            patch("sys.argv", ["cli", "http://x.com/v", "--format", "avi"]),
            pytest.raises(SystemExit),
        ):
            import cli

            cli.main()

    def test_whatsapp_flag_connects_processor(self) -> None:
        with (
            patch("sys.argv", ["cli", "http://x.com/v", "--whatsapp"]),
            patch("app.use_cases.DownloadMedia.execute", return_value=MagicMock(success=True)),
            patch("adapters.whatsapp.processor.connect") as mock_connect,
        ):
            import cli

            cli.main()
        mock_connect.assert_called_once()

    def test_without_whatsapp_flag_processor_is_not_connected(self) -> None:
        with (
            patch("sys.argv", ["cli", "http://x.com/v"]),
            patch("app.use_cases.DownloadMedia.execute", return_value=MagicMock(success=True)),
            patch("adapters.whatsapp.processor.connect") as mock_connect,
        ):
            import cli

            cli.main()
        mock_connect.assert_not_called()
