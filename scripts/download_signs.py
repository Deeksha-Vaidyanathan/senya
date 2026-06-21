"""
Script 1: Download ASL reference clips from LifePrint.com

LifePrint (lifeprint.com) by Dr. Bill Vicars is free for educational use.
This script scrapes each word's page to find and download the sign video/gif.

Run BEFORE the hackathon. Output goes to /dictionary/source/
"""

import time
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from word_list import WORD_LIST

SOURCE_DIR = Path(__file__).parent.parent / "dictionary" / "source"
INDEX_PATH = Path(__file__).parent.parent / "dictionary" / "index.json"
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (educational ASL accessibility project)"}
LIFEPRINT_BASE = "https://www.lifeprint.com"

def get_sign_page_url(word: str) -> str:
    letter = word[0].lower()
    return f"{LIFEPRINT_BASE}/asl101/pages-signs/{letter}/{word}.htm"

def find_video_url(page_url: str) -> str | None:
    """Scrape the word page and return the best video/gif URL found."""
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. <video> or <source> tags (mp4)
        for tag in soup.find_all(["video", "source"]):
            src = tag.get("src")
            if src and src.endswith(".mp4"):
                return urljoin(page_url, src)

        # 2. Animated gifs in /gifs-animated/ (highest quality)
        for tag in soup.find_all("img"):
            src = tag.get("src", "")
            if "gifs-animated" in src and src.endswith(".gif"):
                return urljoin(page_url, src)

        # 3. Any gif in a /gifs/ folder
        for tag in soup.find_all("img"):
            src = tag.get("src", "")
            if "/gifs/" in src and src.endswith(".gif"):
                return urljoin(page_url, src)

        # 4. Any gif on the page as last resort
        for tag in soup.find_all("img"):
            src = tag.get("src", "")
            if src.endswith(".gif"):
                return urljoin(page_url, src)

    except Exception as e:
        print(f"  Error fetching {page_url}: {e}")
    return None

def download_file(url: str, dest: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        if resp.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return True
        print(f"  HTTP {resp.status_code} for {url}")
    except Exception as e:
        print(f"  Download error: {e}")
    return False

def load_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text())
    return {}

def save_index(index: dict):
    INDEX_PATH.write_text(json.dumps(index, indent=2))

def main():
    index = load_index()
    failed = []

    for word in WORD_LIST:
        if word in index and index[word].get("source"):
            print(f"[skip] {word} — already downloaded")
            continue

        print(f"[fetch] {word}")
        page_url = get_sign_page_url(word)
        video_url = find_video_url(page_url)

        if not video_url:
            print(f"  [!] No video found for '{word}'")
            failed.append(word)
            index.setdefault(word, {})["source"] = None
            save_index(index)
            time.sleep(0.3)
            continue

        ext = ".gif" if video_url.endswith(".gif") else ".mp4"
        dest = SOURCE_DIR / f"{word}{ext}"
        success = download_file(video_url, dest)

        if success:
            print(f"  [ok] {dest.name}")
            index.setdefault(word, {})["source"] = str(dest)
            index[word]["source_url"] = video_url
            index[word]["verified"] = False
            index[word]["generated"] = None
            index[word]["pika_asset_url"] = None
        else:
            print(f"  [!] Download failed: {video_url}")
            failed.append(word)
            index.setdefault(word, {})["source"] = None

        save_index(index)
        time.sleep(0.4)

    total = len(WORD_LIST)
    ok = total - len(failed)
    print(f"\nDone. {ok}/{total} words downloaded.")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")

if __name__ == "__main__":
    main()
