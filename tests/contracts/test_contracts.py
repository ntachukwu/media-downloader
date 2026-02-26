"""
Contract tests — junction: adapters ↔ ports

Verify that every concrete adapter structurally satisfies its port.
If an adapter stops implementing the required interface, these fail
before anything else does.
"""

from adapters.local_storage import LocalStorage
from adapters.ytdlp_downloader import YtDlpDownloader
from domain.ports import Downloader, Storage


class TestDownloaderContract:
    def test_ytdlp_downloader_satisfies_downloader_port(self):
        assert isinstance(YtDlpDownloader(), Downloader)

    def test_downloader_port_requires_download_method(self):
        class Missing:
            pass

        assert not isinstance(Missing(), Downloader)

    def test_downloader_port_rejects_wrong_method_name(self):
        class WrongName:
            def fetch(self, request):  # type: ignore[no-untyped-def]
                ...

        assert not isinstance(WrongName(), Downloader)


class TestStorageContract:
    def test_local_storage_satisfies_storage_port(self):
        assert isinstance(LocalStorage(), Storage)

    def test_storage_port_requires_ensure_method(self):
        class Missing:
            pass

        assert not isinstance(Missing(), Storage)

    def test_storage_port_rejects_wrong_method_name(self):
        class WrongName:
            def create(self, path: str):  # type: ignore[no-untyped-def]
                ...

        assert not isinstance(WrongName(), Storage)
