# Image Scraper Utility

A production-grade Python script to concurrently download images from a given URL. Features include session management, multi-threading, and size filtering.

## Features
- **Concurrency**: Uses `ThreadPoolExecutor` for fast parallel downloads.
- **Polite**: Respects `robots.txt` and uses a custom User-Agent.
- **Smart Filtering**: Skips tracking pixels and tiny icons (default < 5KB).
- **Resumable**: Automatically skips images that have already been downloaded.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python img_scrape.py https://example.com/gallery -o my_images --workers 5
```

### Arguments
- `url`: The target URL to scrape.
- `-o`, `--output`: Directory to save images (default: `images_download`).
- `-w`, `--workers`: Number of parallel threads (default: 5).
- `--min-size`: Minimum image size in KB to download (default: 5).

## Disclaimer
This tool is for educational purposes only. Please ensure you have the legal right to download content from the target website and respect their Terms of Service.