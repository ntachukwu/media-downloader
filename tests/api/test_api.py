"""
API endpoint tests.

Uses FastAPI's TestClient (sync) with dependency_overrides to inject fakes.
No mocking frameworks — just plain Python objects satisfying the ports.
"""

from pathlib import Path
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from api import app, get_downloader, get_storage
from domain.models import DownloadRequest, DownloadResult

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeDownloader:
    def __init__(self, succeeds: bool = True) -> None:
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
    def ensure(self, path: str) -> Path:
        return Path(path)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client_ok() -> pytest.FixtureRequest:
    app.dependency_overrides[get_downloader] = lambda: FakeDownloader(succeeds=True)
    app.dependency_overrides[get_storage] = lambda: FakeStorage()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def client_fail() -> pytest.FixtureRequest:
    app.dependency_overrides[get_downloader] = lambda: FakeDownloader(succeeds=False)
    app.dependency_overrides[get_storage] = lambda: FakeStorage()
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /destinations
# ---------------------------------------------------------------------------


class TestGetDestinations:
    def test_returns_200(self, client_ok: TestClient) -> None:
        response = client_ok.get("/destinations")
        assert response.status_code == 200

    def test_returns_a_list(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        assert isinstance(data, list)

    def test_list_is_not_empty(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        assert len(data) > 0

    def test_each_item_has_name_label_constraints(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        for item in data:
            assert "name" in item
            assert "label" in item
            assert "constraints" in item

    def test_constraints_has_required_fields(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        for item in data:
            c = item["constraints"]
            assert "max_duration_seconds" in c
            assert "max_file_mb" in c
            assert "preferred_aspect" in c
            assert "required_codec" in c
            assert "last_verified" in c

    def test_whatsapp_status_is_present(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        names = [d["name"] for d in data]
        assert "whatsapp_status" in names

    def test_instagram_story_is_present(self, client_ok: TestClient) -> None:
        data = client_ok.get("/destinations").json()
        names = [d["name"] for d in data]
        assert "instagram_story" in names


# ---------------------------------------------------------------------------
# POST /download — success
# ---------------------------------------------------------------------------


class TestPostDownloadSuccess:
    _body: ClassVar[dict[str, str]] = {
        "url": "https://example.com/video",
        "format": "mp4",
        "out_dir": "/tmp/out",
    }

    def test_returns_200(self, client_ok: TestClient) -> None:
        response = client_ok.post("/download", json=self._body)
        assert response.status_code == 200

    def test_success_is_true(self, client_ok: TestClient) -> None:
        data = client_ok.post("/download", json=self._body).json()
        assert data["success"] is True

    def test_file_path_is_a_string(self, client_ok: TestClient) -> None:
        data = client_ok.post("/download", json=self._body).json()
        assert isinstance(data["file_path"], str)

    def test_error_is_null_on_success(self, client_ok: TestClient) -> None:
        data = client_ok.post("/download", json=self._body).json()
        assert data["error"] is None

    def test_default_format_is_mp4(self, client_ok: TestClient) -> None:
        body = {"url": "https://example.com/video"}
        data = client_ok.post("/download", json=body).json()
        assert data["success"] is True

    def test_audio_format_is_accepted(self, client_ok: TestClient) -> None:
        body = {"url": "https://example.com/video", "format": "mp3"}
        data = client_ok.post("/download", json=body).json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# POST /download — failure
# ---------------------------------------------------------------------------


class TestPostDownloadFailure:
    _body: ClassVar[dict[str, str]] = {"url": "https://example.com/video"}

    def test_returns_200_with_success_false(self, client_fail: TestClient) -> None:
        response = client_fail.post("/download", json=self._body)
        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_error_field_is_populated(self, client_fail: TestClient) -> None:
        data = client_fail.post("/download", json=self._body).json()
        assert data["error"] == "fake error"

    def test_file_path_is_null_on_failure(self, client_fail: TestClient) -> None:
        data = client_fail.post("/download", json=self._body).json()
        assert data["file_path"] is None


# ---------------------------------------------------------------------------
# POST /download — validation
# ---------------------------------------------------------------------------


class TestPostDownloadValidation:
    def test_missing_url_returns_422(self, client_ok: TestClient) -> None:
        response = client_ok.post("/download", json={"format": "mp4"})
        assert response.status_code == 422

    def test_invalid_format_returns_422(self, client_ok: TestClient) -> None:
        response = client_ok.post("/download", json={"url": "https://x.com", "format": "gif"})
        assert response.status_code == 422

    def test_empty_url_returns_400(self, client_ok: TestClient) -> None:
        response = client_ok.post("/download", json={"url": ""})
        assert response.status_code == 400
