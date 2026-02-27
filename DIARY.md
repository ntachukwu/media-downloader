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

**Pre-commit hook configuration lessons learned**
The first commit attempt failed on three hook issues, each revealing a nuance:

1. **ruff `RUF005`** — `["cli"] + argv` should be `["cli", *argv]`. List concatenation is
   a Python anti-pattern when one side is a spread; the spread form is both faster and
   cleaner. This is exactly the kind of micro-improvement that automated linting catches
   and humans skip over in review.

2. **mypy `exclude` in pre-commit** — adding `--exclude=tests` as a CLI arg to mypy does
   not work when pre-commit passes files as positional arguments (positional args override
   the exclude). The correct mechanism is the pre-commit `exclude:` key at the hook level,
   which filters files *before* they are passed to mypy. Tests are intentionally excluded
   from strict mypy: they use fakes and mocks that would require heavy type annotation for
   no practical gain.

3. **pytest-cov not in pre-commit environment** — the `language: system` hook runs in the
   system Python, not the project's `.venv`. The `pyproject.toml` `addopts` includes
   `--cov` flags, which require `pytest-cov`. The fix is to pass
   `--override-ini=addopts=` to the hook's `entry`, stripping coverage flags. Coverage
   enforcement belongs in CI, not in the local pre-commit fast path.

---

## Commit 4 — `test: assert TikTok URL passes through the adapter unchanged`

### What changed
Added one test to `tests/adapters/test_ytdlp_downloader.py` asserting that a TikTok URL
is handed to yt-dlp exactly as given, without modification.

### Decisions

**Does the source site matter?**
No. yt-dlp resolves which extractor to use internally based on the URL pattern.
Our adapter is site-agnostic by design — it receives a URL string and passes it
to `ydl.download([url])`. The test documents this contract explicitly.

**Why write a test for something that obviously works?**
Because "obviously works" is not the same as "tested". The test pins a contract:
*this code must never inspect or mangle URLs*. If someone later adds URL normalisation,
sanitisation, or domain filtering, this test will catch it and force a conscious decision.
Tests are not just correctness checks — they are specifications.

**Why TikTok specifically?**
It's a real-world URL with a path structure (`/@user/video/id`) that looks different
from a plain YouTube URL. Using a realistic URL makes the intent of the test legible
to anyone reading it later.

---

## Commit 5 — `docs: add Django-inspired proposals to experiments`

### What changed
Four new proposals added to `EXPERIMENTS.md`, all borrowed from studying Django's
open-source architecture. The original `ProgressReporter` port proposal was replaced.

### Decisions

**Why replace ProgressReporter with Signals?**
A `ProgressReporter` port is the right shape for one observer. But the project now has
a second cross-cutting concern (WhatsApp post-processing) and will have more. If every
new concern requires a new constructor argument on `DownloadMedia`, the use case becomes
a configuration object — a smell. Django's signal system solves this: the use case fires
named events, listeners connect independently. Adding WhatsApp processing is one
`signals.download_complete.connect(...)` call, not a change to the domain.

**Why study Django specifically?**
Django is 20 years old and still growing. Its patterns have been tested at scale and
refined through real use over a long time. The management commands system has not
meaningfully changed since Django 1.x. The middleware chain is the same pattern.
These are not clever ideas — they are proven ones. Borrowing from proven designs is
faster than inventing equivalent designs from scratch.

**Build order implied by the proposals**
```
1. Signals (domain/signals.py)         ← no dependencies, unlocks everything else
2. Management commands (cli/commands/) ← needs a second subcommand to justify it
3. Middleware pipeline                 ← needs signals + ffmpeg
4. LazySettings (conf.py)             ← needs the pipeline to configure
```

**Why not build all of this now?**
The proposals are sketches, not implementation plans. The right time to build each one
is when the pain it solves is actually felt. Signals become necessary when the second
cross-cutting concern appears. Management commands become necessary when the second
subcommand is ready. Building ahead of the pain produces unnecessary complexity.

---

*Written by a non-deterministic automata.*
