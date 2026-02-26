import pytest
from pathlib import Path
from adapters.local_storage import LocalStorage


class TestLocalStorage:
    def test_creates_directory(self, tmp_path):
        storage = LocalStorage()
        target = tmp_path / "new" / "nested"
        storage.ensure(str(target))
        assert target.exists()

    def test_returns_path(self, tmp_path):
        storage = LocalStorage()
        result = storage.ensure(str(tmp_path / "out"))
        assert isinstance(result, Path)

    def test_idempotent(self, tmp_path):
        storage = LocalStorage()
        target = tmp_path / "out"
        storage.ensure(str(target))
        storage.ensure(str(target))
        assert target.exists()

    def test_existing_contents_preserved(self, tmp_path):
        sentinel = tmp_path / "keep.txt"
        sentinel.write_text("safe")
        LocalStorage().ensure(str(tmp_path))
        assert sentinel.read_text() == "safe"
