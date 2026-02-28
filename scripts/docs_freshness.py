#!/usr/bin/env python3
"""Detect stale documentation.

For each tracked doc file, reports code commits that landed after the doc
was last touched. Exits 0 if all docs are current; exits 1 if any are stale.

Run locally:
    python scripts/docs_freshness.py

In CI this runs as a non-blocking job so it never gates merges.

Architecture
------------
``FreshnessStrategy`` is a Protocol (port). ``GitFreshnessStrategy`` is the
concrete adapter that shells out to git. ``find_stale_docs`` accepts the
protocol — swap the strategy to target a different VCS or use a fake in tests.
"""

import subprocess
import sys
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

# Source files that constitute "code changes".
CODE_PATHS = ["domain/", "adapters/", "app/", "api.py", "cli.py"]

# Docs that should be updated when the code above changes.
DOCS: dict[str, str] = {
    "README.md": "project overview and usage",
    "DIARY.md": "architectural decisions log",
    "EXPERIMENTS.md": "design proposals",
}


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class Commit:
    sha: str
    subject: str


# ---------------------------------------------------------------------------
# Port — swap this for any VCS backend
# ---------------------------------------------------------------------------


@runtime_checkable
class FreshnessStrategy(Protocol):
    """Knows how to query commit history for a set of paths."""

    def last_commit_sha(self, path: str) -> str | None:
        """Return the SHA of the most recent commit touching *path*, or None."""
        ...

    def commits_since(self, since_sha: str | None, paths: list[str]) -> list[Commit]:
        """Return commits touching *paths* that landed after *since_sha*.

        If *since_sha* is None, return all commits touching *paths*.
        """
        ...


# ---------------------------------------------------------------------------
# Adapter — concrete git implementation
# ---------------------------------------------------------------------------


class GitFreshnessStrategy:
    """FreshnessStrategy backed by ``git log``."""

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def last_commit_sha(self, path: str) -> str | None:
        sha = self._git("log", "-1", "--format=%H", "--", path)
        return sha or None

    def commits_since(self, since_sha: str | None, paths: list[str]) -> list[Commit]:
        cmd = ["log", "--format=%H %s"]
        if since_sha:
            cmd.append(f"{since_sha}..HEAD")
        cmd += ["--", *paths]
        output = self._git(*cmd)
        if not output:
            return []
        commits = []
        for line in output.splitlines():
            sha, _, subject = line.partition(" ")
            commits.append(Commit(sha=sha[:7], subject=subject))
        return commits


# Static check: GitFreshnessStrategy satisfies the port.
_: FreshnessStrategy = GitFreshnessStrategy()


# ---------------------------------------------------------------------------
# Detection logic — pure, testable, VCS-agnostic
# ---------------------------------------------------------------------------


def find_stale_docs(
    strategy: FreshnessStrategy,
    docs: dict[str, str],
    code_paths: list[str],
) -> dict[str, list[Commit]]:
    """Return docs that have unseen code commits.

    Keys are doc paths; values are the commits that landed after that doc
    was last touched.  An empty result means all docs are current.
    """
    stale: dict[str, list[Commit]] = {}
    for doc_path in docs:
        last_sha = strategy.last_commit_sha(doc_path)
        undocumented = strategy.commits_since(last_sha, code_paths)
        if undocumented:
            stale[doc_path] = undocumented
    return stale


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    strategy = GitFreshnessStrategy()
    stale = find_stale_docs(strategy, DOCS, CODE_PATHS)

    if not stale:
        print("All docs are current.")
        sys.exit(0)

    print("Stale documentation detected:\n")
    for doc_path, commits in stale.items():
        description = DOCS[doc_path]
        last_sha = strategy.last_commit_sha(doc_path)
        last_short = last_sha[:7] if last_sha else "never"
        print(f"  {doc_path}  ({description})")
        print(f"  Last updated: {last_short}")
        print(f"  Code commits since then: {len(commits)}")
        for c in commits[:5]:
            print(f"    {c.sha}  {c.subject}")
        if len(commits) > 5:
            print(f"    ... and {len(commits) - 5} more")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
