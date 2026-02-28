"""
FastAPI entry point — HTTP layer.

Adapters are injected via FastAPI Depends so tests can swap them with fakes
using app.dependency_overrides without touching the domain or app layer.

Run locally:
    uvicorn api:app --reload
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from adapters.destinations import registry
from adapters.local_storage import LocalStorage
from adapters.ytdlp_downloader import YtDlpDownloader
from app.use_cases import DownloadMedia
from domain.models import DownloadRequest, MediaFormat
from domain.ports import Downloader, Storage

app = FastAPI(title="media-downloader")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConstraintsOut(BaseModel):
    max_duration_seconds: int | None
    max_file_mb: int | None
    preferred_aspect: str | None
    required_codec: str
    last_verified: str


class DestinationOut(BaseModel):
    name: str
    label: str
    constraints: ConstraintsOut


class DownloadRequestBody(BaseModel):
    url: str
    format: MediaFormat = MediaFormat.MP4
    out_dir: str = "./downloads"


class DownloadResponseBody(BaseModel):
    success: bool
    file_path: str | None = None  # stringified Path; None on failure
    error: str | None = None


# ---------------------------------------------------------------------------
# Dependency providers
# ---------------------------------------------------------------------------


def get_downloader() -> Downloader:
    return YtDlpDownloader()


def get_storage() -> Storage:
    return LocalStorage()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/destinations", response_model=list[DestinationOut])
def list_destinations() -> list[DestinationOut]:
    """Return all registered destination adapters with their platform constraints."""
    return [
        DestinationOut(
            name=d.name,
            label=d.label,
            constraints=ConstraintsOut(
                max_duration_seconds=d.constraints.max_duration_seconds,
                max_file_mb=d.constraints.max_file_mb,
                preferred_aspect=d.constraints.preferred_aspect,
                required_codec=d.constraints.required_codec,
                last_verified=d.constraints.last_verified,
            ),
        )
        for d in registry.all_destinations()
    ]


@app.post("/download", response_model=DownloadResponseBody)
def download(
    body: DownloadRequestBody,
    downloader: Annotated[Downloader, Depends(get_downloader)],
    storage: Annotated[Storage, Depends(get_storage)],
) -> DownloadResponseBody:
    """Download media from a URL.

    Returns 200 with ``success=true`` and a ``file_path`` on success, or
    ``success=false`` and an ``error`` message when the download fails.
    Returns 400 if the URL is empty (domain validation); 422 for malformed
    request bodies or unknown format values.
    """
    try:
        request = DownloadRequest(url=body.url, format=body.format, out_dir=body.out_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = DownloadMedia(downloader=downloader, storage=storage).execute(request)

    return DownloadResponseBody(
        success=result.success,
        file_path=str(result.file_path) if result.success else None,
        error=result.error,
    )
