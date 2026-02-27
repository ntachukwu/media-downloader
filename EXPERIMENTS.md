# Experiments & Design Proposals

A scratchpad for ideas, port sketches, and architectural proposals.
Nothing here is committed code — it is thinking made visible.

Promote an idea to `domain/ports.py` only when the interface feels stable.
Raw ideas that don't need a sketch yet go in `BACKLOG.md` instead.

---

## Active Proposals

---

### [PROPOSAL] Signals — Django-style event system (replaces ProgressReporter port)

**Problem**: downloads are silent, and adding progress feedback via a `ProgressReporter`
port couples the use case to a specific observer interface. The deeper problem: any new
cross-cutting behaviour (logging, WhatsApp post-processing, notifications) would require
adding another constructor argument to `DownloadMedia`. That does not scale.

**Insight from Django**: Django's signal system decouples senders from receivers entirely.
Models fire `post_save` without knowing or caring who is listening. Listeners connect
independently. New behaviour is added by connecting a new receiver — nothing else changes.

**Sketch**

```python
# domain/signals.py  ← new file

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any


@dataclass
class Signal:
    """Lightweight observer. Receivers connect; senders fire."""
    _receivers: list[Callable[..., Any]] = field(default_factory=list)

    def connect(self, receiver: Callable[..., Any]) -> None:
        self._receivers.append(receiver)

    def send(self, **kwargs: Any) -> None:
        for receiver in self._receivers:
            receiver(**kwargs)


# The named signals — senders fire these, receivers listen to them
download_started  = Signal()   # kwargs: url, title, total_bytes
download_progress = Signal()   # kwargs: downloaded, total, speed
download_complete = Signal()   # kwargs: file_path, request
download_failed   = Signal()   # kwargs: error, request
```

**How ProgressReporter becomes a receiver**

```python
# adapters/cli_progress.py

from domain.signals import download_started, download_progress, download_complete

def on_start(url, title, total_bytes, **_):
    print(f"Downloading: {title}")

def on_progress(downloaded, total, speed, **_):
    pct = int(downloaded / total * 100) if total else 0
    print(f"\r{pct}%", end="", flush=True)

def on_complete(file_path, **_):
    print(f"\nSaved to {file_path}")

# Connect at startup in cli.py — zero changes to domain or use case
download_started.connect(on_start)
download_progress.connect(on_progress)
download_complete.connect(on_complete)
```

**How WhatsApp post-processing becomes a receiver**

```python
# adapters/whatsapp_processor.py

from domain.signals import download_complete

def prepare_for_whatsapp(file_path, request, **_):
    # trim to 30s, enforce 16MB, ensure H.264/AAC
    ...

download_complete.connect(prepare_for_whatsapp)
```

**How the use case fires signals** (minimal change)

```python
# app/use_cases.py  — only change is adding signal.send() calls

from domain import signals

class DownloadMedia:
    def execute(self, request):
        self._storage.ensure(request.out_dir)
        result = self._downloader.download(request)
        if result.success:
            signals.download_complete.send(
                file_path=result.file_path, request=request
            )
        else:
            signals.download_failed.send(error=result.error, request=request)
        return result
```

**What this replaces**
- `ProgressReporter` port — no longer needed as a domain interface
- The `reporter=` constructor argument on `DownloadMedia` — never needed
- Any future `WhatsAppProcessor` port — it just connects to `download_complete`

**Trade-offs**
- Receivers are fire-and-forget; errors in receivers are silent unless `send_robust` is added
- Global signal instances are module-level state — makes testing require explicit
  connect/disconnect (or resetting receivers between tests)
- yt-dlp's progress hooks are called from a thread; `download_progress` receivers
  must be thread-safe if they hold state

**Status**: this is the right model. Build `domain/signals.py` before `ProgressReporter`.

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

### [PROPOSAL] Management commands — Django-style CLI registry

**Problem**: `cli.py` is a single flat function. As subcommands grow (`download`, `inspect`,
`prepare`, `history`), the file will accumulate argument parsing branches. Django solved
this in 2005 and the solution has not needed to change since.

**Sketch**

```
cli/
├── __init__.py
├── base.py            ← BaseCommand
└── commands/
    ├── download.py    ← class Command(BaseCommand): handle download
    ├── inspect.py     ← class Command(BaseCommand): handle inspect (needs MetadataExtractor)
    └── prepare.py     ← class Command(BaseCommand): handle WhatsApp preparation
```

```python
# cli/base.py

import argparse
from abc import abstractmethod


class BaseCommand:
    help: str = ""

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description=self.help)
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass  # Override to add args

    @abstractmethod
    def handle(self, **options: object) -> None:
        raise NotImplementedError

    def run(self, argv: list[str]) -> None:
        parser = self.create_parser()
        options = vars(parser.parse_args(argv))
        self.handle(**options)
```

```python
# cli/commands/download.py

from cli.base import BaseCommand
from adapters.local_storage import LocalStorage
from adapters.ytdlp_downloader import YtDlpDownloader
from app.use_cases import DownloadMedia
from domain.models import DownloadRequest, MediaFormat
from domain import signals


class Command(BaseCommand):
    help = "Download media from a URL"

    def add_arguments(self, parser):
        parser.add_argument("url")
        parser.add_argument("--format", "-f", default="mp4",
                            choices=[f.value for f in MediaFormat])
        parser.add_argument("--out", "-o", default="./downloads")

    def handle(self, url, format, out, **_):
        request = DownloadRequest(
            url=url, format=MediaFormat(format), out_dir=out
        )
        result = DownloadMedia(
            downloader=YtDlpDownloader(),
            storage=LocalStorage(),
        ).execute(request)

        if not result.success:
            print(f"Download failed: {result.error}")
            raise SystemExit(1)
```

```python
# cli/registry.py — auto-discovers commands from cli/commands/

import importlib
import pkgutil
from cli import commands as commands_pkg


def get_commands() -> dict[str, type]:
    registry = {}
    for _, name, _ in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"cli.commands.{name}")
        registry[name] = module.Command
    return registry


def run(argv: list[str]) -> None:
    commands = get_commands()
    if not argv or argv[0] not in commands:
        print(f"Available commands: {', '.join(commands)}")
        raise SystemExit(1)
    commands[argv[0]]().run(argv[1:])
```

**Adding a new command is one file**. Drop `cli/commands/status.py` with a `Command` class
and it appears automatically — `registry.py` never changes.

**Status**: build this when the second subcommand (`inspect`) is ready. Premature before that.

---

### [PROPOSAL] Middleware pipeline — for WhatsApp video processing

**Problem**: after a download, the file needs to be processed for WhatsApp Status:
trim to 30s, enforce 16MB, ensure H.264/AAC. These are distinct steps that should
be composable and skippable independently.

**Insight from Django**: each middleware receives the next handler and wraps it.
The chain is built once and called per-request. Steps are ordered, pluggable, and
each is independently testable.

**Sketch**

```python
# domain/pipeline.py

from pathlib import Path
from typing import Callable

ProcessorFn = Callable[[Path], Path]


def build_pipeline(steps: list[ProcessorFn], final: ProcessorFn) -> ProcessorFn:
    """Build a chain: each step wraps the next. Outermost step runs first."""
    handler = final
    for step in reversed(steps):
        previous = handler
        def make_handler(s, p):
            def h(path): return s(p(path))
            return h
        handler = make_handler(step, previous)
    return handler
```

```python
# adapters/whatsapp/trim.py
def trim_to_30s(path: Path) -> Path:
    """ffmpeg -t 30 ..."""
    ...

# adapters/whatsapp/resize.py
def enforce_16mb(path: Path) -> Path:
    """Re-encode at lower bitrate if > 16MB"""
    ...

# adapters/whatsapp/codec.py
def ensure_h264_aac(path: Path) -> Path:
    """ffmpeg -vcodec libx264 -acodec aac ..."""
    ...
```

```python
# Wired together via signal:
from domain import signals
from domain.pipeline import build_pipeline
from adapters.whatsapp import trim, resize, codec

whatsapp_pipeline = build_pipeline(
    steps=[trim.trim_to_30s, resize.enforce_16mb, codec.ensure_h264_aac],
    final=lambda path: path,  # identity — return path unchanged
)

def prepare_for_whatsapp(file_path, **_):
    whatsapp_pipeline(file_path)

signals.download_complete.connect(prepare_for_whatsapp)
```

**Adding a new processing step is one function**. The pipeline, the use case, and the
domain are untouched.

**Status**: build after signals land. Depends on ffmpeg being available.

---

### [PROPOSAL] LazySettings — Django-style configuration

**Problem**: defaults (output dir, format, WhatsApp constraints) are hardcoded as
CLI argument defaults. A user who always downloads to `~/Videos` as MP4 for WhatsApp
must type `--format mp4 --out ~/Videos` every time.

**Sketch**

```python
# conf.py

import importlib
import os
from typing import Any


DEFAULTS = {
    "DEFAULT_FORMAT": "mp4",
    "DEFAULT_OUT_DIR": "./downloads",
    "WHATSAPP_MAX_SECONDS": 30,
    "WHATSAPP_MAX_MB": 16,
    "WHATSAPP_MODE": False,
}


class LazySettings:
    _loaded: bool = False
    _data: dict[str, Any] = {}

    def _load(self) -> None:
        self._data = dict(DEFAULTS)
        module_path = os.environ.get("MEDIA_DL_SETTINGS")
        if module_path:
            module = importlib.import_module(module_path)
            self._data.update(
                {k: getattr(module, k) for k in dir(module) if k.isupper()}
            )
        self._loaded = True

    def __getattr__(self, name: str) -> Any:
        if not self._loaded:
            self._load()
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"No setting: {name}")


settings = LazySettings()  # module-level singleton, loaded on first access
```

```python
# User creates ~/.config/media-dl/settings.py:
DEFAULT_FORMAT = "mp4"
DEFAULT_OUT_DIR = "~/Videos/whatsapp"
WHATSAPP_MODE = True
WHATSAPP_MAX_SECONDS = 30

# Then:
export MEDIA_DL_SETTINGS=~/.config/media-dl.settings
```

**Status**: build after management commands. Feeds `WHATSAPP_MODE` into the pipeline.

---

## Closed / Decided

*(Move proposals here once they are built or explicitly rejected, with a one-line outcome.)*

- **Retry / backoff** — moved to `BACKLOG.md`; yt-dlp handles retries natively, no sketch needed yet.
- **Output naming strategy** — moved to `BACKLOG.md`; adapter-internal concern, not a domain port.
- **ProgressReporter port** — superseded by Signals proposal; a port is the wrong abstraction here.

---

*Written by a non-deterministic automata.*
