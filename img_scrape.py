import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# 1. Configuration
folder_name = "images_download"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def download_image(session, image_url, folder, base_url):
    """Downloads a single image and returns True if successful, False otherwise."""
    try:
        full_url = urljoin(base_url, image_url)
        base_name = full_url.split("/")[-1].split("?")[0]
        if not base_name:
            return False
        
        filename = os.path.join(folder, base_name)
        if os.path.exists(filename):
            return "exists"

        img_data = session.get(full_url, timeout=10).content
        with open(filename, "wb") as handler:
            handler.write(img_data)
        return "downloaded"
    except Exception as e:
        return f"error: {e}"

def main():
    # 2. Setup folder
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Get URL from user
    target_url = input("Enter the URL to scrape images from: ").strip()
    if not target_url:
        print("No URL provided. Exiting.")
        return

    # 3. Get the page content
    print(f"Fetching images from {target_url}...")
    with requests.Session() as session:
        session.headers.update(headers)
        try:
            response = session.get(target_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve the page: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        
        # Extract unique URLs
        unique_urls = set()
        for img in img_tags:
            img_url = img.get("data-src") or img.get("data-lazy-src") or img.get("src")
            if img_url and not img_url.startswith("data:image"):
                unique_urls.add(img_url)

        print(f"Found {len(img_tags)} tags, identified {len(unique_urls)} unique images.")

        downloaded = 0
        existed = 0
        errors = 0

        # 4. Parallel Download
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Map the download function to our unique URLs
            results = list(tqdm(executor.map(lambda u: download_image(session, u, folder_name, target_url), unique_urls), 
                                total=len(unique_urls), desc="Downloading"))

        for res in results:
            if res == "downloaded": downloaded += 1
            elif res == "exists": existed += 1
            else: errors += 1

    print(f"\n--- Scrape Summary ---")
    print(f"New images downloaded: {downloaded}")
    print(f"Images already present: {existed}")
    print(f"Errors encountered:     {errors}")
    print(f"Total files in folder:  {len([f for f in os.listdir(folder_name) if not f.startswith('.')])}")

if __name__ == "__main__":
    main()