import json
from pathlib import Path
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
from .utils import sanitize_filename, get_tradition_color

from .config import DOWNLOAD_LIST_FILE, PROCESSED_URLS_FILE, CORPUS_DIR
from .utils import sanitize_filename
from . import catalog
from . import logger

def create_retry_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

http_session = create_retry_session()
ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")


def load_download_list(filter_type: set[str], force: bool = False) -> List[Dict]:
    if not Path(DOWNLOAD_LIST_FILE).exists():
        logger.error(f"Download list file not found: {DOWNLOAD_LIST_FILE}")
        return []

    with open(DOWNLOAD_LIST_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    items = [item for item in items if item["type"] in filter_type]

    processed_urls = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, "r", encoding="utf-8") as f:
            processed_urls = set(json.load(f))
        logger.info(f"Loaded {len(processed_urls)} previously processed URLs from {PROCESSED_URLS_FILE}")

    seen_urls = set()
    filtered = []

    for item in items:
        url = item["url"]
        tid = item.get("title", item.get("id", "unknown_id"))
        tradition = item["tradition"]
        major_tradition = item.get("major_tradition", "Unknown")
        lang = item["language"]
        ftype = item["type"]
        description = item.get("description", "")  

        if url in seen_urls:
            logger.warning(f"Duplicate URL: {url}, skipping")
            catalog.add_to_catalog(tid, major_tradition, tradition, lang, ftype, url, False, 0, 0, get_tradition_color(tradition), description)
            continue

        major_tradition_path = sanitize_filename(major_tradition.replace('/', '_').replace(' ', '_'))
        tradition_path = sanitize_filename(tradition.replace('/', '_').replace(' ', '_'))
        title_path = sanitize_filename(tid.replace('/', '_').replace(' ', '_'))

        folder = CORPUS_DIR / major_tradition_path / tradition_path / title_path
        filename = folder / f"{title_path}.txt"

        if filename.exists() and not force:
            logger.info(f"File exists for {tid}, will be processed locally")
            new_item = item.copy()
            new_item['_local_file'] = str(filename)
            seen_urls.add(url)
            filtered.append(new_item)
        elif url in processed_urls and not force:
            logger.info(f"URL was already processed earlier (file is missing): {url}, skipping")
            catalog.add_to_catalog(tid, major_tradition, tradition, lang, ftype, url, False, 0, 0, get_tradition_color(tradition), description)
            continue
        else:
            seen_urls.add(url)
            filtered.append(item)

    return filtered

def download_file(url: str) -> bytes:
    logger.info(f"Downloading: {url}")
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
    response = http_session.get(url, headers=headers, timeout=(10, 30))
    response.raise_for_status()
    return response.content