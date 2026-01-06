import os
import time
import argparse
import requests
import urllib.robotparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def can_fetch(url, user_agent):
    """Checks robots.txt to see if scraping is allowed."""
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(urljoin(url, "/robots.txt"))
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True # Default to True if robots.txt is unreachable

def download_image(session, image_url, folder, base_url, min_size_kb=5):
    """Downloads an image with size filtering and returns a status dict."""
    try:
        full_url = urljoin(base_url, image_url)
        base_name = full_url.split("/")[-1].split("?")[0]
        if not base_name:
            return {"status": "skipped", "reason": "invalid name"}
        
        filename = os.path.join(folder, base_name)
        if os.path.exists(filename):
            return {"status": "exists"}

        # Stream to check headers before downloading full content
        response = session.get(full_url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Filter by size
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) < (min_size_kb * 1024):
            return {"status": "skipped", "reason": "too small"}

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return {"status": "downloaded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description="A polite and concurrent image scraper.")
    parser.add_argument("url", help="The URL to scrape images from")
    parser.add_argument("-o", "--output", default="images_download", help="Output directory")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Number of concurrent workers")
    parser.add_argument("--min-size", type=int, default=5, help="Minimum image size in KB to download")
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if not can_fetch(args.url, USER_AGENT):
        print(f"⚠️ Warning: {args.url} robots.txt discourages scraping. Proceed with caution.")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            return

    print(f"🔍 Fetching images from {args.url}...")
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        try:
            response = session.get(args.url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ Failed to retrieve the page: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        
        unique_urls = set()
        for img in img_tags:
            img_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src")
            if img_url and not img_url.startswith("data:image"):
                unique_urls.add(img_url)

        if not unique_urls:
            print("No images found.")
            return

        print(f"✅ Found {len(img_tags)} tags, identified {len(unique_urls)} unique images.")

        stats = {"downloaded": 0, "exists": 0, "skipped": 0, "error": 0}

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(download_image, session, u, args.output, args.url, args.min_size) for u in unique_urls]
            for future in tqdm(futures, total=len(unique_urls), desc="Downloading"):
                res = future.result()
                stats[res["status"]] += 1

    print(f"\n--- Scrape Summary ---")
    print(f"New images downloaded: {stats['downloaded']}")
    print(f"Images already present: {stats['exists']}")
    print(f"Images skipped (small): {stats['skipped']}")
    print(f"Errors encountered:     {stats['error']}")
    print(f"Total files in folder:  {len([f for f in os.listdir(args.output) if not f.startswith('.')])}")

if __name__ == "__main__":
    main()