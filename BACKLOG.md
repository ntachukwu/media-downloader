# Backlog

Low-priority ideas. Not rejected — just not now.
Revisit when looking for the next feature to build.

To promote an item: move it to `EXPERIMENTS.md` as a `[PROPOSAL]` and flesh out the sketch.

---

## Format

```
### Idea title
**What**: one sentence.
**Why not now**: one sentence.
**Trigger**: what would make this worth doing?
```

---

## Items

---

### Flutter + FastAPI mobile share app
**What**: Flutter app registers as a share target on Android + iOS; receives URLs from
TikTok/YouTube/etc., calls the FastAPI backend, receives processed video, hands it to
WhatsApp/Instagram via native OS share sheet.
**Why not now**: Python engine needs to be stable first; FastAPI wrapper and Flutter shell
are delivery layers, not core logic.
**Trigger**: Destination port and pipeline are built and working end-to-end.

---

### Remote constraints registry for destination adapters
**What**: each `Destination` adapter fetches its constraints from a hosted JSON endpoint
(`https://your-api.com/constraints/whatsapp_status.json`) rather than relying solely on
hardcoded values. Falls back to hardcoded if the fetch fails. You push a JSON update and
all running instances pick up the new constraints without a code release.
**Why not now**: hardcoded adapters with `last_verified` dates are sufficient until
constraints actually change and cause a real problem.
**Trigger**: a platform changes a constraint (duration, size limit) and it causes a
production bug. That's the evidence that the fetch-on-startup mechanism is worth the
added complexity.

---

### Output naming strategy
**What**: let users customise how downloaded files are named (date-prefix, UUID, custom slug).
**Why not now**: current `%(title)s` naming is good enough for personal use; no one has asked.
**Trigger**: first user complaint about filename collisions or sorting.

---

### Retry / backoff decorator
**What**: wrap `Downloader` with configurable retry logic and exponential backoff.
**Why not now**: yt-dlp already retries internally; duplicate logic until we swap the backend.
**Trigger**: switching to a backend that doesn't handle retries natively.

---

### `inspect` subcommand
**What**: `python cli.py inspect <url>` prints title, duration, size, available formats before downloading.
**Why not now**: requires `MetadataExtractor` port which isn't built yet.
**Trigger**: `MetadataExtractor` lands (see `EXPERIMENTS.md`).

---

### Playlist support
**What**: handle playlist URLs and return per-item results instead of one opaque result.
**Why not now**: depends on `MetadataExtractor.is_playlist` to detect playlists reliably.
**Trigger**: `MetadataExtractor` lands (see `EXPERIMENTS.md`).

---

### Download history / deduplication
**What**: persist a record of downloaded URLs so re-running skips already-downloaded items.
**Why not now**: no persistent storage layer exists yet; adds complexity before the core is stable.
**Trigger**: user runs the tool on the same playlist repeatedly and wants skip logic.

---

### Config file support
**What**: read defaults (output dir, format, retries) from `~/.config/media-dl/config.toml`.
**Why not now**: CLI flags are sufficient for current usage; a config file is extra surface area.
**Trigger**: user sets the same flags on every invocation and asks for a default.

---

### Async / concurrent downloads
**What**: download multiple URLs in parallel using `asyncio` or `ThreadPoolExecutor`.
**Why not now**: single-item download is the only use case right now.
**Trigger**: playlist support lands and sequential download feels slow.

---

### `--dry-run` flag
**What**: resolve metadata and print what would be downloaded without downloading anything.
**Why not now**: requires `MetadataExtractor` port.
**Trigger**: `MetadataExtractor` lands.

---

### Shell completion
**What**: tab-completion for `--format` and `--out` flags in bash/zsh/fish.
**Why not now**: nice-to-have polish, not a functional gap.
**Trigger**: tool becomes something used daily and the friction of typing flags becomes annoying.

---

### Python API / library mode
**What**: expose `DownloadMedia` as a proper importable API so other scripts can use it.
**Why not now**: the architecture already supports this — `cli.py` is just one consumer.
  Only needs packaging (`pyproject.toml` entry points) and a documented public interface.
**Trigger**: someone wants to embed this in another project.

---

*Written by a non-deterministic automata.*
