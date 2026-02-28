#!/usr/bin/env python3
"""Detect stale documentation.

For each tracked doc file, reports code commits that landed after the doc
was last touched. Exits 0 if all docs are current; exits 1 if any are stale.

Run locally:
    python scripts/docs-freshness.py

In CI this runs as a non-blocking job so it never gates merges.
"""

import subprocess
import sys
from dataclasses import dataclass

# Source files that constitute "code changes".
CODE_PATHS = ["domain/", "adapters/", "app/", "api.py", "cli.py"]

# Docs that should be updated when the code above changes.
DOCS: dict[str, str] = {
    "README.md": "project overview and usage",
    "DIARY.md": "architectural decisions log",
    "EXPERIMENTS.md": "design proposals",
}


@dataclass
class Commit:
    sha: str
    subject: str


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def last_sha_touching(path: str) -> str | None:
    sha = git("log", "-1", "--format=%H", "--", path)
    return sha or None


def code_commits_since(since_sha: str | None) -> list[Commit]:
    cmd = ["log", "--format=%H %s"]
    if since_sha:
        cmd.append(f"{since_sha}..HEAD")
    cmd += ["--", *CODE_PATHS]
    output = git(*cmd)
    if not output:
        return []
    commits = []
    for line in output.splitlines():
        sha, _, subject = line.partition(" ")
        commits.append(Commit(sha=sha[:7], subject=subject))
    return commits


def main() -> None:
    stale: dict[str, list[Commit]] = {}

    for doc_path, _description in DOCS.items():
        last_sha = last_sha_touching(doc_path)
        undocumented = code_commits_since(last_sha)
        if undocumented:
            stale[doc_path] = undocumented

    if not stale:
        print("All docs are current.")
        sys.exit(0)

    print("Stale documentation detected:\n")
    for doc_path, commits in stale.items():
        description = DOCS[doc_path]
        last_sha = last_sha_touching(doc_path)
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
