import json
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from settings import settings

from . import catalog, logger
from .utils import corpus_text_path, get_tradition_color

# Lazily initialized: creating a session / UserAgent at import time would make
# any `import corpus.*` pay for it (UserAgent may even hit the network).
_http_session: requests.Session | None = None
_user_agent = None


def create_retry_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=settings.corpus.retry_total,
        backoff_factor=settings.corpus.retry_backoff_factor,
        status_forcelist=settings.corpus.retry_status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = create_retry_session()
    return _http_session


def _get_user_agent():
    global _user_agent
    if _user_agent is None:
        from fake_useragent import UserAgent

        _user_agent = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return _user_agent


def load_download_list(filter_type: set[str], force: bool = False) -> list[dict]:
    if not Path(settings.download_list_file).exists():
        logger.error(f"Download list file not found: {settings.download_list_file}")
        return []

    with open(settings.download_list_file, encoding="utf-8") as f:
        items = json.load(f)

    items = [item for item in items if item["type"] in filter_type]

    processed_urls = set()
    if settings.processed_urls_path.exists():
        with open(settings.processed_urls_path, encoding="utf-8") as f:
            processed_urls = set(json.load(f))
        logger.info(f"Loaded {len(processed_urls)} previously processed URLs from {settings.processed_urls_path}")

    seen_urls = set()
    filtered = []

    for item in items:
        url = item["url"]
        tid = item.get("title", item.get("id", "unknown_id"))
        tradition = item["tradition"]
        color = get_tradition_color(tradition)

        if url in seen_urls:
            logger.warning(f"Duplicate URL: {url}, skipping")
            catalog.add_item_to_catalog(item, tid=tid, color=color, success=False, error="Duplicate URL")
            continue

        filename = corpus_text_path(settings.corpus_dir, item.get("major_tradition", "Unknown"), tradition, tid)

        if filename.exists() and not force:
            logger.info(f"File exists for {tid}, will be processed locally")
            new_item = item.copy()
            new_item["_local_file"] = str(filename)
            seen_urls.add(url)
            filtered.append(new_item)
        elif url in processed_urls and not force:
            logger.info(f"URL was already processed earlier (file is missing): {url}, skipping")
            catalog.add_item_to_catalog(item, tid=tid, color=color, success=False, error="Previously processed, file missing")
            continue
        else:
            seen_urls.add(url)
            filtered.append(item)

    return filtered


def download_file(url: str) -> bytes:
    logger.info(f"Downloading: {url}")
    headers = {
        "User-Agent": _get_user_agent().random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
    response = _get_http_session().get(url, headers=headers, timeout=(settings.corpus.timeout_connect, settings.corpus.timeout_read))
    response.raise_for_status()
    content: bytes = response.content
    return content
