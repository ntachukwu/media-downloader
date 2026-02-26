import argparse
from downloader import build_opts, ensure_dir, run_download


def main():
    parser = argparse.ArgumentParser(description="Download media from a URL")
    parser.add_argument("url")
    parser.add_argument("--format", "-f", default="mp4")
    parser.add_argument("--out",    "-o", default="./downloads")
    args = parser.parse_args()

    ensure_dir(args.out)
    opts = build_opts(args.url, args.format, args.out)
    run_download(args.url, opts)


if __name__ == "__main__":
    main()
