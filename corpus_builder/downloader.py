import json
from pathlib import Path
from typing import List, Dict, Optional
import requests
from .config import DOWNLOAD_LIST_FILE, PROCESSED_URLS_FILE, CORPUS_DIR
from . import catalog
from . import logger

def load_download_list(filter_type: Optional[str] = None, force: bool = False) -> List[Dict]:
    with open(DOWNLOAD_LIST_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    if filter_type:
        items = [item for item in items if item["type"] == filter_type]
    processed_urls = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, "r", encoding="utf-8") as f:
            processed_urls = set(json.load(f))
        logger.info(f"Загружено {len(processed_urls)} ранее обработанных URL из {PROCESSED_URLS_FILE}")
    seen_urls = set()
    filtered = []
    for item in items:
        url = item["url"]
        tid = item["id"]
        tradition = item["tradition"]
        lang = item["language"]
        ftype = item["type"]
        if url in seen_urls:
            logger.warning(f"Дубликат URL: {url}, пропускаем")
            catalog.add_to_catalog(tid, tradition, lang, ftype, url, False, 0, 0, "")
            continue
        tradition_path = tradition.replace('/', '_').replace(' ', '_')
        folder = CORPUS_DIR / tradition_path / tid
        filename = folder / f"{tid}.txt"
        if filename.exists() and not force:
            logger.info(f"Файл существует для {tid}, будет обработан локально")
            item['_local_file'] = str(filename)
            seen_urls.add(url)
            filtered.append(item)
        elif url in processed_urls and not force:
            logger.info(f"URL уже обработан ранее (файл отсутствует): {url}, пропускаем")
            catalog.add_to_catalog(tid, tradition, lang, ftype, url, True, 0, 0, "")
            continue
        else:
            seen_urls.add(url)
            filtered.append(item)
    return filtered

def download_file(url: str) -> bytes:
    logger.info(f"Загрузка: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.content