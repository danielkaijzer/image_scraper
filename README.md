# Media Scraper

A Python CLI tool to concurrently download images and videos from almost any URL. It combines `BeautifulSoup` for static image scraping and `yt-dlp` for robust video extraction from 1,000+ platforms (Vimeo, YouTube, Instagram, etc.).

## Features
- **Dual Engine**: Automatically switches between image scraping and video downloading based on your input.
- **Universal Video Support**: Downloads video from major platforms (Vimeo, YouTube, TikTok, etc.) using `yt-dlp`.
- **Authenticated Scraping**: Supports `cookies.txt` to bypass login walls (e.g., private Vimeo portfolios).
- **Smart Filtering**: 
  - **Images**: Filters out tiny icons and tracking pixels (< 5KB).
  - **Videos**: Regex-based title filtering (e.g., download only videos containing "Campaign").
- **Concurrency**: Uses `ThreadPoolExecutor` for fast parallel image downloads.
- **Resumable**: Skips files that already exist in the output folder.

## Prerequisites

For video downloading, **FFmpeg** is highly recommended (and often required) to merge separate audio/video streams into a single `.mp4` file.

- **macOS**: `brew install ffmpeg`
- **Windows**: `choco install ffmpeg` or download binaries manually.

## Installation

1. Clone this repository.
2. Install the required Python packages:

```bash
pip install requests beautifulsoup4 tqdm yt-dlp

```

## Usage

Run the script from your terminal. The script is smart enough to detect if you want videos based on the arguments you provide.

### Scrape Images

Downloads all images from a webpage to the `images_download` folder.

```bash
python img_scrape.py https://example.com/gallery -o my_images

```

### Scrape Videos (Filtered)

Downloads videos from a profile (e.g., Vimeo, YouTube) that match a specific keyword.
*Note: The script automatically switches to Video Mode when `-k` is used.*

```bash
python img_scrape.py https://vimeo.com/user123 -k "Fashion"

```

### Authenticated Scraping (Private/Login-Walled Content)

If a site requires you to be logged in (e.g., private Vimeo videos, Instagram, age-gated content), you must provide your browser cookies.

1. **Install Extension**: Install "Get cookies.txt LOCALLY" for Chrome/Firefox.
2. **Export**: Log in to the target site, open the extension, and export cookies.
3. **Save**: Save the file as `cookies.txt` in the same folder as this script.
4. **Run**: The script automatically detects the file and uses it.

```bash
python img_scrape.py https://vimeo.com/user123 -k "Internal Review"

```

### Scrape Everything (Images & Video)

Force the script to check for both images and video content.

```bash
python img_scrape.py https://example.com/mixed-media -m both

```

## Arguments

| Argument | Flag | Default | Description |
| --- | --- | --- | --- |
| **URL** | `url` | Required | The target URL to scrape. |
| **Output** | `-o` | `media_download` | Directory to save downloaded files. |
| **Mode** | `-m` | `image` | Operation mode: `image`, `video`, or `both`. Auto-switches to `video` if `-k` is present. |
| **Keyword** | `-k` | `None` | Regex keyword to filter video titles (case-insensitive). |
| **Workers** | `-w` | `5` | Number of parallel threads (Images only). |
| **Min Size** | `--min-size` | `5` | Minimum image size in KB to download. |

## Disclaimer

This tool is for educational purposes only. Please ensure you have the legal right to download content from the target website and respect their Terms of Service.
