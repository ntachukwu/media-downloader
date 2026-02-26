# media-downloader

Download video or audio from any URL and convert to your chosen format.

Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) (1,000+ supported sites) and ffmpeg.

## Requirements

- Python 3.11+
- ffmpeg (`brew install ffmpeg` / `sudo apt install ffmpeg`)

## Setup

```bash
git clone <repo-url>
cd media-downloader

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
# Download as mp4 (default)
python cli.py https://youtube.com/watch?v=...

# Specify format
python cli.py https://youtube.com/watch?v=... --format mkv

# Specify output directory
python cli.py https://youtube.com/watch?v=... --format mp4 --out ~/Videos
```

## Development

```bash
pip install -r requirements-dev.txt

# Run tests with coverage
pytest

# Coverage report is written to coverage/index.html
```

## Project structure

```
media-downloader/
├── downloader.py       # core — three pure functions
├── cli.py              # argument parsing and wiring
├── tests/
│   └── test_downloader.py
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Contributing

1. Branch off `main`: `git checkout -b feature/your-feature`
2. Write a failing test first (TDD)
3. Implement until tests pass
4. Open a PR — coverage must stay above 80%
