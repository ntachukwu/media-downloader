# Development Diary — media-downloader

A running log of decisions made during development, with the reasoning behind each one.

---

## Commit 1 — `feat: initial project setup`

### What was built
A flat Python script (`downloader.py`) with three pure functions:
- `build_opts(url, fmt, out_dir)` — assembles yt-dlp option dict
- `ensure_dir(path)` — creates output directory if needed
- `run_download(url, opts)` — executes the download via yt-dlp context manager

A minimal CLI (`cli.py`) wires those three functions together. Tests in `tests/test_downloader.py`.

### Decisions

**Why yt-dlp?**
yt-dlp supports 1,000+ sites and is actively maintained. It is the de-facto standard for
scriptable media downloads and requires no API keys. ffmpeg handles format conversion as a
post-processor, keeping the download and conversion steps separate.

**Why three pure functions?**
The first working version is always a straight-line script. Pure functions are trivial to test
without mocking, and they make the logic explicit before any structure is layered on top.
At this stage, adding more abstraction would be premature — there is only one use case and
one user.

**Why a virtual environment, not global packages?**
Reproducibility. `requirements.txt` pins the minimum version of yt-dlp so any contributor
or CI runner gets the same dependency.

---

## Commit 2 — `refactor: hexagonal architecture (ports & adapters)`

### What changed
The flat script was split into four layers:

```
domain/         — pure data structures and interface definitions
adapters/       — concrete implementations (yt-dlp, local filesystem)
app/            — single use case wired via dependency injection
cli.py          — entry point that builds the dependency graph
```

Tests were reorganised to mirror the layer structure:
`tests/domain/`, `tests/adapters/`, `tests/app/`.
The original flat tests were kept at `tests/legacy/`.

### Decisions

**Why hexagonal architecture at this stage?**
The flat script was already showing a seam: the logic that *decides what to download*
(format, quality, output path) is separate from the logic that *executes the download*
(yt-dlp calls). Hexagonal architecture makes that seam explicit as a `Downloader` port.

The immediate payoff is testability — the use case can be tested with a `FakeDownloader`
and `FakeStorage` without any network calls or filesystem side effects.

**Why Python `Protocol` for ports instead of `ABC`?**
`Protocol` is structural (duck typing), not nominal. Adapters do not need to inherit from
the port — they just need to implement the right methods. This keeps adapters free from
the domain layer's import graph. `runtime_checkable` lets contract tests verify conformance
with `isinstance()`.

**Why frozen dataclasses for domain models?**
`DownloadRequest` and `DownloadResult` are value objects — they describe intent, not state.
Freezing them (`frozen=True`) prevents accidental mutation and makes them safe to pass
across layers. It also communicates intent clearly: these objects are not meant to change.

**Why `StrEnum` for `MediaFormat`?**
`StrEnum` means the enum value *is* a plain string. The CLI can accept `"mp4"` directly, and
yt-dlp options accept the value directly, without any `.value` conversion leaking into both
places. The `is_audio_only` property encapsulates the branching logic that would otherwise
be duplicated in the adapter and the CLI.

**Why keep `downloader.py` around after the refactor?**
The original file is still valid Python. Its tests (`tests/legacy/`) continue to pass.
Deleting it immediately would erase history — it is better left as an explicit artifact until
it is confirmed that every capability it had is covered by the new architecture.
(Spoiler: it is. The legacy folder is now dead code and will be removed in a future commit.)

**Why dependency injection in `DownloadMedia`?**
The use case receives its `Downloader` and `Storage` via the constructor, not by
instantiating them internally. This means tests can inject fakes without patching.
It also means swapping LocalStorage for S3Storage in the future is one line in `cli.py`,
not a change to the business logic.

---

## Commit 3 — `feat: CI pipeline, pre-commit hooks, expanded test suite`

### What changed

**CI (`.github/workflows/ci.yml`)**
Two jobs: `quality` (ruff lint + format check + mypy) and `test` (pytest with coverage).
They run on every push and pull request to `main`.

**Pre-commit (`.pre-commit-config.yaml`)**
Ruff (lint + format), mypy, and pytest run before every commit.
This catches formatting drift and type errors at the earliest possible moment.

**Expanded test suite**
| New file | What it tests |
|---|---|
| `tests/cli/test_cli.py` | CLI → use case wiring (argv translation, exit codes) |
| `tests/contracts/test_contracts.py` | Adapters structurally satisfy their ports |
| `tests/integration/test_integration.py` | Use case + real LocalStorage + faked yt-dlp |

**Code quality pass**
- Import order normalised (isort via ruff)
- `dict` → `dict[str, object]` (strict mypy)
- Whitespace alignment removed from assignments
- `main()` return type annotated as `-> None`
- Unused `MediaFormat` import removed from adapter

### Decisions

**Why separate lint and test jobs in CI?**
Lint fails fast — it catches obvious errors in seconds without spinning up test
infrastructure. Keeping jobs separate means a formatting error doesn't waste minutes
running the full test suite.

**Why pytest is also a pre-commit hook?**
The cost of running the test suite locally is low (all tests are fast — no network, no
real filesystem beyond tmp). Catching a broken test before it reaches CI is cheaper than
waiting for a CI run, reviewing the failure, and pushing a fix.

**Why contract tests?**
The `@runtime_checkable Protocol` makes structural conformance checkable at runtime.
Contract tests (`isinstance(YtDlpDownloader(), Downloader)`) pin this — if someone renames
`download` to `fetch` in the adapter and forgets to update the port, the contract test
fails immediately rather than at integration time.

**Why integration tests when we already have unit tests with fakes?**
Unit tests with fakes verify behaviour in isolation. Integration tests catch wiring mistakes:
does the use case actually call `storage.ensure` *before* `downloader.download`? Does the
real directory get created on disk? Fakes cannot answer these questions.

**Why keep the legacy tests?**
Until `downloader.py` is deleted, keeping its tests alive ensures the file doesn't silently
break. They serve as a safety net, not a design goal. Once the file is removed, the tests
go with it.

**Why `dict[str, object]` instead of `dict`?**
Mypy strict mode rejects bare `dict` — it demands type parameters. `dict[str, object]` is
the honest type: keys are strings, values are heterogeneous. Using a TypedDict would be
more precise but would couple the adapter to a schema that yt-dlp can change at any time.
`dict[str, object]` is the right balance of honesty and pragmatism.

---

*Written by a non-deterministic automata.*
