import os
import argparse
import requests
import urllib.robotparser
import yt_dlp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from yt_dlp.utils import DownloadError

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def can_fetch(url, user_agent):
    """Checks robots.txt to see if scraping is allowed."""
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(urljoin(url, "/robots.txt"))
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def download_image(session, image_url, folder, base_url, min_size_kb=5):
    """Downloads an image with size filtering."""
    try:
        full_url = urljoin(base_url, image_url)
        base_name = full_url.split("/")[-1].split("?")[0]
        if not base_name: return {"status": "skipped"}
        
        filename = os.path.join(folder, base_name)
        if os.path.exists(filename): return {"status": "exists"}

        response = session.get(full_url, timeout=10, stream=True)
        response.raise_for_status()
        
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) < (min_size_kb * 1024):
            return {"status": "skipped"}

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return {"status": "downloaded"}
    except Exception:
        return {"status": "error"}

def download_videos(url, folder, keyword=None):
    """General purpose video downloader using yt-dlp."""
    cookies_path = 'cookies.txt'
    cookies_found = os.path.exists(cookies_path)
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        'matchtitle': f'(?i){keyword}' if keyword else None,
        'cookiefile': cookies_path if cookies_found else None,
        'quiet': False,
        'no_warnings': True,
        'restrictfilenames': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🎥 Scanning for video content at {url}...")
            if cookies_found:
                print(f"🍪 Using cookies from {cookies_path}")
            else:
                print("⚠️ No cookies.txt found. Public videos only.")
            
            ydl.download([url])
            
    except DownloadError as e:
        # Check specifically for errors that look like auth failures
        error_msg = str(e).lower()
        if not cookies_found and ("sign in" in error_msg or "logged-in" in error_msg or "403" in error_msg):
            print("\n❌ AUTHENTICATION ERROR: The site blocked the download.")
            print(f"💡 FIX: You are missing a '{cookies_path}' file in this folder.")
            print("👉 Please check the README 'Authentication' section on how to export your browser cookies.")
        else:
            print(f"⚠️ Video download failed: {e}")
    except Exception as e:
        print(f"⚠️ An unexpected error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="A production-grade Media Scraper for images and video.")
    parser.add_argument("url", help="The URL to scrape")
    parser.add_argument("-m", "--mode", choices=['image', 'video', 'both'], default='image', 
                        help="Scrape images, video, or both (default: image)")
    parser.add_argument("-o", "--output", default="media_download", help="Output directory")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Concurrent workers for images")
    parser.add_argument("-k", "--keyword", help="Filter videos by title (regex supported)")
    parser.add_argument("--min-size", type=int, default=5, help="Minimum image size in KB")
    args = parser.parse_args()

    # --- INTELLIGENT MODE SWITCHING ---
    if args.keyword and args.mode == 'image':
        print(f"ℹ️ Keyword '{args.keyword}' detected. Auto-switching to VIDEO mode.")
        args.mode = 'video'
    # ----------------------------------

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if not can_fetch(args.url, USER_AGENT):
        print(f"⚠️ Warning: {args.url} robots.txt discourages scraping.")

    if args.mode in ['video', 'both']:
        download_videos(args.url, args.output, args.keyword)

    if args.mode in ['image', 'both']:
        print(f"🔍 Scraping images from {args.url}...")
        with requests.Session() as session:
            session.headers.update({"User-Agent": USER_AGENT})
            try:
                response = session.get(args.url, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                img_tags = soup.find_all("img")
                unique_urls = {img.get(attr) for img in img_tags for attr in ["src", "data-src", "data-lazy-src"] 
                               if img.get(attr) and not img.get(attr).startswith("data:image")}
                
                stats = {"downloaded": 0, "exists": 0, "skipped": 0, "error": 0}
                if unique_urls:
                    with ThreadPoolExecutor(max_workers=args.workers) as executor:
                        futures = [executor.submit(download_image, session, u, args.output, args.url, args.min_size) for u in unique_urls if u]
                        for future in tqdm(futures, total=len(futures), desc="Downloading Images"):
                            res = future.result()
                            stats[res["status"]] += 1
                
                print(f"\n--- Image Summary: {stats['downloaded']} new, {stats['exists']} existing ---")
            except Exception as e:
                print(f"❌ Image scraping failed: {e}")

if __name__ == "__main__":
    main()