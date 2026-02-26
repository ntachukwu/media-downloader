# Experiments & Design Proposals

A scratchpad for ideas, port sketches, and architectural proposals.
Nothing here is committed code — it is thinking made visible.

Promote an idea to `domain/ports.py` only when the interface feels stable.
Raw ideas that don't need a sketch yet go in `BACKLOG.md` instead.

---

## Active Proposals

---

### [PROPOSAL] ProgressReporter port

**Problem**: downloads are silent. The user gets no feedback until the file appears.
yt-dlp has a rich progress hook system — we're currently discarding it entirely (`quiet: True`).

**Sketch**

```python
# domain/ports.py

from typing import Protocol

class ProgressReporter(Protocol):
    def on_start(self, url: str, title: str, total_bytes: int | None) -> None: ...
    def on_progress(self, downloaded: int, total: int | None, speed: float | None) -> None: ...
    def on_complete(self, file_path: Path) -> None: ...
    def on_error(self, error: str) -> None: ...
```

**Concrete implementations to consider**
- `SilentReporter` — current behaviour, no output (default)
- `CliProgressReporter` — prints a progress bar via `rich` or `tqdm`
- `CallbackReporter` — wraps an arbitrary callable, useful for GUI/API consumers

**Wiring**
`DownloadMedia` would accept an optional `reporter: ProgressReporter = SilentReporter()`.
The adapter maps yt-dlp's `progress_hooks` dict to the port's methods.

**Trade-offs**
- `total_bytes` is `None` for live streams — callers must handle that
- yt-dlp calls hooks from a thread; the reporter must be thread-safe if stateful
- Adding this port means `YtDlpDownloader._build_opts` needs to inject the hook,
  which changes its signature — that is fine, it's internal

**Status**: worth building. Low risk, high UX value.

---

### [PROPOSAL] MetadataExtractor port

**Problem**: the use case downloads blind — it cannot inspect a URL before committing to
a download. This prevents: title preview, format selection by duration, size checks.

**Sketch**

```python
# domain/ports.py

@dataclass(frozen=True)
class MediaMetadata:
    url: str
    title: str
    duration_seconds: float | None
    filesize_bytes: int | None
    available_formats: list[str]
    is_playlist: bool

class MetadataExtractor(Protocol):
    def extract(self, url: str) -> MediaMetadata: ...
```

**Concrete implementation**
`YtDlpMetadataExtractor` calls `ydl.extract_info(url, download=False)` — yt-dlp already
supports this; it is a pure read operation.

**New use case this enables**

```python
class InspectMedia:
    def __init__(self, extractor: MetadataExtractor) -> None: ...
    def execute(self, url: str) -> MediaMetadata: ...
```

CLI addition: `python cli.py inspect https://...` prints title, size, available formats.

**Trade-offs**
- Adds a network round-trip before download; annoying for automated pipelines
- Not every site returns all fields — `None` handling is real burden for callers
- `is_playlist` opens a larger design question (see Playlist proposal below)

**Status**: useful but optional. Build `InspectMedia` as a separate use case, not a
precondition of `DownloadMedia`.

---

### [PROPOSAL] Playlist support

**Problem**: yt-dlp handles playlist URLs natively, but our `DownloadRequest` models a
single item. Passing a playlist URL today produces one `DownloadResult` that hides
how many files actually downloaded.

**Option A — Transparent (no model change)**
Let `YtDlpDownloader` handle playlists silently. The result's `file_path` points to the
directory. Simple, but `DownloadResult` becomes a lie (it implies one file).

**Option B — Explicit playlist model**

```python
@dataclass(frozen=True)
class PlaylistDownloadResult:
    request: DownloadRequest
    results: list[DownloadResult]

    @property
    def success(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def failed(self) -> list[DownloadResult]:
        return [r for r in self.results if not r.success]
```

A new `DownloadPlaylist` use case handles this. Single-item and playlist downloads
stay separate — the CLI detects which to invoke via `MetadataExtractor.is_playlist`.

**Option C — Union return type**
`Downloader.download()` returns `DownloadResult | PlaylistDownloadResult`.
Avoids a second use case but forces callers to branch on type — an antipattern.

**Recommendation**: Option B. Keeps the domain clean, lets single-item and batch
paths evolve independently.

**Status**: depends on MetadataExtractor. Do not build without it.

---

## Closed / Decided

*(Move proposals here once they are built or explicitly rejected, with a one-line outcome.)*

- **Retry / backoff** — moved to `BACKLOG.md`; yt-dlp handles retries natively, no sketch needed yet.
- **Output naming strategy** — moved to `BACKLOG.md`; adapter-internal concern, not a domain port.

---

*Written by a non-deterministic automata.*
