import argparse
from domain.models import DownloadRequest, MediaFormat
from adapters.ytdlp_downloader import YtDlpDownloader
from adapters.local_storage import LocalStorage
from app.use_cases import DownloadMedia


def main():
    parser = argparse.ArgumentParser(description="Download media from a URL")
    parser.add_argument("url")
    parser.add_argument("--format", "-f", default="mp4",
                        choices=[f.value for f in MediaFormat])
    parser.add_argument("--out", "-o", default="./downloads")
    args = parser.parse_args()

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
