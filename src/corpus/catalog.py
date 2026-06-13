import logging
import threading
from dataclasses import dataclass, fields

logger = logging.getLogger(__name__)

_catalog_lock = threading.Lock()
catalog_rows: list["CatalogRow"] = []
_seen_urls: set[str] = set()


@dataclass(frozen=True)
class CatalogRow:
    tid: str
    major_tradition: str
    tradition: str
    language: str
    ftype: str
    url: str
    available: bool
    word_count: int
    sentence_count: int
    color: str
    description: str = ""

    def as_csv_row(self) -> list:
        return [getattr(self, f.name) for f in fields(self)]


CSV_HEADER = [
    "id",
    "major_tradition",
    "tradition",
    "language",
    "type",
    "url",
    "availability",
    "word_count",
    "sentence_count",
    "color",
    "description",
]


def clear_catalog() -> None:
    with _catalog_lock:
        catalog_rows.clear()
        _seen_urls.clear()


def add_to_catalog(
    tid: str,
    major_tradition: str,
    tradition: str,
    lang: str,
    ftype: str,
    url: str,
    availability: bool,
    word_count: int,
    sentence_count: int,
    color: str,
    description: str = "",
) -> None:
    with _catalog_lock:
        if url in _seen_urls:
            logger.warning(f"Duplicate attempt to add URL to catalog: {url}. Skipping.")
            return

        catalog_rows.append(
            CatalogRow(
                tid=tid,
                major_tradition=major_tradition,
                tradition=tradition,
                language=lang,
                ftype=ftype,
                url=url,
                available=availability,
                word_count=word_count,
                sentence_count=sentence_count,
                color=color,
                description=description,
            )
        )
        _seen_urls.add(url)

    status_str = "available" if availability else "unavailable"
    logger.info(f"{tid}: {status_str} (words: {word_count}, sentences: {sentence_count}, color: {color})")


def add_item_to_catalog(
    item: dict, *, tid: str, color: str, success: bool, stats: dict | None = None, error: str = ""
) -> None:
    """Catalog entry from a download-list item: success with stats or failure with error text."""
    description = item.get("description", "")
    if success and stats:
        add_to_catalog(
            tid, item.get("major_tradition", "Unknown"), item["tradition"],
            item["language"], item["type"], item["url"],
            True, stats["word_count"], stats["sentence_count"], color, description,
        )
    else:
        err_desc = f"{description} [{error}]" if description else error
        add_to_catalog(
            tid, item.get("major_tradition", "Unknown"), item["tradition"],
            item["language"], item["type"], item["url"],
            False, 0, 0, color, err_desc,
        )
