import threading
from typing import List, Set
from . import logger

_catalog_lock = threading.Lock()
catalog_rows: List[list] = []
_seen_urls: Set[str] = set()


def clear_catalog() -> None:
    with _catalog_lock:
        catalog_rows.clear()
        _seen_urls.clear()


def add_to_catalog(tid: str, major_tradition: str, tradition: str, lang: str, ftype: str, url: str,
                   availability: bool, word_count: int, sentence_count: int, color: str, description: str = "") -> None:
    with _catalog_lock:
        if url in _seen_urls:
            logger.warning(f"Duplicate attempt to add URL to catalog: {url}. Skipping.")
            return

        catalog_rows.append([
            tid, major_tradition, tradition, lang, ftype, url, availability, word_count, sentence_count, color, description
        ])
        _seen_urls.add(url)

    status_str = "available" if availability else "unavailable"
    logger.info(f"{tid}: {status_str} (words: {word_count}, sentences: {sentence_count}, color: {color})")
