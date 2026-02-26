"""
Use case tests use fakes — in-memory implementations of the ports.
No mocking frameworks, no patching. Just plain Python objects.
This makes the tests readable and the contracts explicit.
"""

import pytest
from pathlib import Path
from domain.models import DownloadRequest, DownloadResult, MediaFormat
from app.use_cases import DownloadMedia


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeDownloader:
    def __init__(self, succeeds=True):
        self.received: DownloadRequest | None = None
        self._succeeds = succeeds

    def download(self, request: DownloadRequest) -> DownloadResult:
        self.received = request
        return DownloadResult(
            request=request,
            file_path=Path(request.out_dir) / "video.mp4",
            success=self._succeeds,
            error=None if self._succeeds else "fake error",
        )


class FakeStorage:
    def __init__(self):
        self.ensured: list[str] = []

    def ensure(self, path: str) -> Path:
        self.ensured.append(path)
        return Path(path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDownloadMedia:
    def _make(self, succeeds=True):
        downloader = FakeDownloader(succeeds=succeeds)
        storage    = FakeStorage()
        use_case   = DownloadMedia(downloader=downloader, storage=storage)
        request    = DownloadRequest(url="http://x.com/v",
                                     format=MediaFormat.MP4,
                                     out_dir="/tmp/out")
        return use_case, downloader, storage, request

    def test_successful_execute_returns_success(self):
        use_case, _, _, request = self._make()
        result = use_case.execute(request)
        assert result.success

    def test_storage_is_ensured_before_download(self):
        use_case, _, storage, request = self._make()
        use_case.execute(request)
        assert "/tmp/out" in storage.ensured

    def test_request_is_passed_to_downloader(self):
        use_case, downloader, _, request = self._make()
        use_case.execute(request)
        assert downloader.received is request

    def test_failed_download_propagates_failure(self):
        use_case, _, _, request = self._make(succeeds=False)
        result = use_case.execute(request)
        assert not result.success
        assert result.error == "fake error"

    def test_storage_ensured_even_on_failure(self):
        use_case, _, storage, request = self._make(succeeds=False)
        use_case.execute(request)
        assert len(storage.ensured) == 1

    def test_different_downloader_can_be_injected(self):
        """Swap the adapter — use case behaviour unchanged."""
        class AlwaysFailsDownloader:
            def download(self, request):
                return DownloadResult(request=request,
                                      file_path=Path("/"),
                                      success=False,
                                      error="always fails")

        use_case = DownloadMedia(downloader=AlwaysFailsDownloader(),
                                  storage=FakeStorage())
        request = DownloadRequest(url="http://x.com/v",
                                  format=MediaFormat.MP4,
                                  out_dir="/tmp")
        result = use_case.execute(request)
        assert not result.success
