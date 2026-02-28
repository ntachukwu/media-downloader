"""
Tests for docs_freshness detection logic.

Uses a FakeFreshnessStrategy to exercise find_stale_docs() without
touching git. The CLI entry point (main) is not tested here — it wires
the real GitFreshnessStrategy and is exercised by CI.
"""

from typing import ClassVar

from scripts.docs_freshness import (
    Commit,
    FreshnessStrategy,
    find_stale_docs,
)

# ---------------------------------------------------------------------------
# Fake
# ---------------------------------------------------------------------------


class FakeFreshnessStrategy:
    """In-memory FreshnessStrategy for testing."""

    def __init__(
        self,
        last_shas: dict[str, str | None],
        commits_to_return: list[Commit],
    ) -> None:
        self._shas = last_shas
        self._commits = commits_to_return

    def last_commit_sha(self, path: str) -> str | None:
        return self._shas.get(path)

    def commits_since(self, since_sha: str | None, paths: list[str]) -> list[Commit]:
        return list(self._commits)


# Verify the fake satisfies the Protocol at import time.
_: FreshnessStrategy = FakeFreshnessStrategy({}, [])  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFindStaleDocs:
    _docs: ClassVar[dict[str, str]] = {"README.md": "overview", "DIARY.md": "decisions"}
    _paths: ClassVar[list[str]] = ["domain/", "adapters/"]

    def test_returns_empty_when_no_commits(self) -> None:
        strategy = FakeFreshnessStrategy(
            last_shas={"README.md": "abc1234", "DIARY.md": "def5678"},
            commits_to_return=[],
        )
        assert find_stale_docs(strategy, self._docs, self._paths) == {}

    def test_stale_doc_is_reported(self) -> None:
        commit = Commit(sha="abc1234", subject="feat: add thing")
        strategy = FakeFreshnessStrategy(
            last_shas={"README.md": "old", "DIARY.md": "old"},
            commits_to_return=[commit],
        )
        result = find_stale_docs(strategy, self._docs, self._paths)
        assert "README.md" in result
        assert "DIARY.md" in result

    def test_stale_doc_contains_the_commits(self) -> None:
        commit = Commit(sha="abc1234", subject="feat: add thing")
        strategy = FakeFreshnessStrategy(
            last_shas={"README.md": "old", "DIARY.md": "old"},
            commits_to_return=[commit],
        )
        result = find_stale_docs(strategy, self._docs, self._paths)
        assert result["README.md"] == [commit]

    def test_fresh_doc_not_in_result(self) -> None:
        strategy = FakeFreshnessStrategy(
            last_shas={"README.md": "current", "DIARY.md": "current"},
            commits_to_return=[],
        )
        result = find_stale_docs(strategy, self._docs, self._paths)
        assert "README.md" not in result
        assert "DIARY.md" not in result

    def test_doc_with_no_known_sha_treated_as_never_updated(self) -> None:
        """A doc that has never been committed is treated as maximally stale."""
        commit = Commit(sha="abc1234", subject="feat: add thing")
        strategy = FakeFreshnessStrategy(
            last_shas={},  # no shas known — doc was never touched
            commits_to_return=[commit],
        )
        result = find_stale_docs(strategy, {"README.md": "overview"}, self._paths)
        assert "README.md" in result

    def test_only_stale_docs_appear(self) -> None:
        """When the fake returns commits, every doc in the set is stale."""
        commit = Commit(sha="abc1234", subject="chore: something")
        strategy = FakeFreshnessStrategy(
            last_shas={"README.md": "old", "DIARY.md": "current"},
            commits_to_return=[commit],
        )
        # Both docs see commits_to_return=[commit] from the fake, so both stale.
        result = find_stale_docs(strategy, self._docs, self._paths)
        assert set(result.keys()) == {"README.md", "DIARY.md"}
