import argparse

import adapters.cli_progress  # noqa: F401 — connects progress receivers to signals
from adapters.local_storage import LocalStorage
from adapters.whatsapp import processor as whatsapp_processor
from adapters.ytdlp_downloader import YtDlpDownloader
from app.use_cases import DownloadMedia
from domain.models import DownloadRequest, MediaFormat


def main() -> None:
    parser = argparse.ArgumentParser(description="Download media from a URL")
    parser.add_argument("url")
    parser.add_argument("--format", "-f", default="mp4", choices=[f.value for f in MediaFormat])
    parser.add_argument("--out", "-o", default="./downloads")
    parser.add_argument(
        "--whatsapp",
        action="store_true",
        help="Prepare the downloaded file for WhatsApp Status (trim, codec, resize).",
    )
    args = parser.parse_args()

    if args.whatsapp:
        whatsapp_processor.connect()

    request = DownloadRequest(
        url=args.url,
        format=MediaFormat(args.format),
        out_dir=args.out,
    )

    result = DownloadMedia(
        downloader=YtDlpDownloader(),
        storage=LocalStorage(),
    ).execute(request)

    if not result.success:
        print(f"Download failed: {result.error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
