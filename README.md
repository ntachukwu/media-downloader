# media-downloader

Download video or audio from any URL, convert to your chosen format, and optionally prepare it for WhatsApp Status.

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) (1,000+ supported sites) and ffmpeg.

## Requirements

- Python 3.11+
- ffmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)

## Setup

```bash
git clone <repo-url>
cd media-downloader

# With uv (recommended)
uv sync --extra dev

# Or with pip
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## CLI usage

```bash
# Download as mp4 (default)
python cli.py https://youtube.com/watch?v=...

# Specify format
python cli.py https://youtube.com/watch?v=... --format mkv

# Specify output directory
python cli.py https://youtube.com/watch?v=... --out ~/Videos

# Download and prepare for WhatsApp Status
# (splits into ≤90s parts, enforces H.264/AAC and 16 MB per part)
# Videos over 4m30s are rejected.
python cli.py https://youtube.com/watch?v=... --whatsapp
```

Supported formats: `mp4`, `mkv`, `webm`, `mp3`, `m4a`, `wav`.

## HTTP API

```bash
uvicorn api:app --reload
```

### GET /destinations

Returns all supported destination platforms with their constraints.

```bash
curl http://localhost:8000/destinations
```

```json
[
  {
    "name": "whatsapp_status",
    "label": "WhatsApp Status",
    "constraints": {
      "max_duration_seconds": 90,
      "max_file_mb": 16,
      "preferred_aspect": "9:16",
      "required_codec": "h264",
      "last_verified": "2024-02-01"
    }
  }
]
```

### POST /download

```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=...", "format": "mp4", "out_dir": "./downloads"}'
```

Returns `{"success": true, "file_path": "...", "error": null}` on success,
or `{"success": false, "file_path": null, "error": "..."}` on failure.

## Development

```bash
# Run tests with coverage
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy domain/ adapters/ app/ cli.py api.py
```

Coverage report is written to `coverage/index.html`. The 80% floor is enforced in CI.

## Project structure

```
media-downloader/
├── domain/                        # Pure data structures and port interfaces
│   ├── models.py                  # DownloadRequest, DownloadResult, MediaFormat
│   ├── ports.py                   # Downloader, Storage, Destination protocols
│   ├── signals.py                 # Django-style event system
│   └── pipeline.py                # Sequential processor chain
├── adapters/                      # Concrete implementations
│   ├── ytdlp_downloader.py        # Downloader port → yt-dlp
│   ├── local_storage.py           # Storage port → local filesystem
│   ├── cli_progress.py            # Signal receivers for terminal progress
│   ├── destinations/              # Destination adapters + registry
│   │   ├── whatsapp_status.py
│   │   ├── instagram_story.py
│   │   └── registry.py
│   └── whatsapp/                  # WhatsApp post-processing pipeline
│       ├── processor.py           # Wires pipeline to download_complete signal
│       ├── trim.py
│       ├── codec.py               # Ensures H.264/AAC
│       ├── resize.py              # Enforces file size limit
│       └── split.py               # Splits video into ≤90s parts
├── app/
│   └── use_cases.py               # DownloadMedia orchestrator
├── api.py                         # FastAPI HTTP layer
├── cli.py                         # CLI entry point
├── tests/
│   ├── adapters/
│   ├── api/
│   ├── app/
│   ├── cli/
│   ├── contracts/
│   ├── domain/
│   └── integration/
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Contributing

1. Branch off `main`: `git checkout -b feature/your-feature`
2. Write a failing test first (TDD)
3. Implement until tests pass
4. Open a PR — coverage must stay above 80%
