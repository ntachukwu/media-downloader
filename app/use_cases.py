"""
Use case: DownloadMedia

Orchestrates the ports — knows the workflow, owns no implementation.
Receives its dependencies via constructor injection (testable, swappable).
"""

from domain import signals
from domain.models import DownloadRequest, DownloadResult
from domain.ports import Downloader, Storage


class DownloadMedia:
    """
    Single use case: take a request, prepare storage, execute download.

    Dependencies injected — never instantiated internally.
    Test by passing in fakes. Swap backends by passing different adapters.
    """

    def __init__(self, downloader: Downloader, storage: Storage) -> None:
        self._downloader = downloader
        self._storage = storage

    def execute(self, request: DownloadRequest) -> DownloadResult:
        self._storage.ensure(request.out_dir)
        signals.download_started.send(url=request.url)
        result = self._downloader.download(request)
        if result.success:
            signals.download_complete.send(file_path=result.file_path, request=request)
        else:
            signals.download_failed.send(error=result.error, request=request)
        return result
