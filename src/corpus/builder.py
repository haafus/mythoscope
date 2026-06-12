import concurrent.futures
import csv
import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import catalog, logger
from .clean_gutenberg import clean_gutenberg_in_builder
from .config import CATALOG_FILE, CORPUS_DIR, DOWNLOAD_LIST_FILE, METADATA_FILE, PROCESSED_URLS_FILE, config
from .downloader import download_file, load_download_list
from .utils import (
    _decode_bytes,
    corpus_text_path,
    count_sentences,
    count_words,
    ensure_dir,
    get_tradition_color,
    html_to_text,
    md5,
    normalize_text,
    pdf_to_text,
)

data_lock = threading.Lock()


def _item_tid(item: dict) -> str:
    return item.get("title", item.get("id", "unknown_id"))


def _finalize_text(text: str, url: str, tid: str) -> dict:
    text = normalize_text(text)
    text = clean_gutenberg_in_builder(text, url, tid)
    data_utf8 = text.encode("utf-8")
    return {
        "text": text,
        "data_utf8": data_utf8,
        "md5": md5(data_utf8),
        "char_count": len(text),
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
    }


def _build_metadata(item: dict, *, path: str, color: str, stats: dict) -> dict:
    return {
        "id": _item_tid(item),
        "major_tradition": item.get("major_tradition", "Unknown"),
        "tradition": item["tradition"],
        "language": item["language"],
        "type": item["type"],
        "url": item["url"],
        "date_downloaded": datetime.now(timezone.utc).isoformat(),
        "md5": stats["md5"],
        "path": path,
        "char_count": stats["char_count"],
        "word_count": stats["word_count"],
        "sentence_count": stats["sentence_count"],
        "color": color,
    }


def _extract_text(data: bytes, url: str, tid: str, content_type: str = "") -> str:
    is_pdf = url.lower().endswith(".pdf") or "application/pdf" in content_type or data[:4] == b"%PDF"
    is_html = (
        b"<html" in data[:200].lower() or "text/html" in content_type or b"<!doctype html" in data[:200].lower()
    )

    if is_pdf:
        logger.debug(f"{tid}: PDF detected, extracting text")
        return pdf_to_text(data)
    if is_html:
        logger.debug(f"{tid}: HTML detected, converting to text")
        return html_to_text(data)
    return _decode_bytes(data)


def process_local_file(filename: Path, item: dict, color: str) -> dict | None:
    tid = _item_tid(item)
    url = item["url"]

    try:
        logger.info(f"{tid}: Processing existing file {filename}")
        data = filename.read_bytes()
        text = _extract_text(data, url, tid)
        stats = _finalize_text(text, url, tid)
        return _build_metadata(item, path=str(filename.resolve()), color=color, stats=stats)
    except Exception as e:
        logger.error(f"{tid}: Error processing local file {filename}: {e}")
        return None


def process_single_item(item: dict, force: bool, metadata: list[dict], processed_urls: set[str]):
    tid = _item_tid(item)
    url = item["url"]
    color = get_tradition_color(item["tradition"])

    if "_local_file" in item and not force:
        filename = Path(item["_local_file"])
        if filename.exists():
            local_meta = process_local_file(filename, item, color)
            if local_meta:
                with data_lock:
                    metadata.append(local_meta)
                    processed_urls.add(url)
                catalog.add_item_to_catalog(item, tid=tid, color=color, success=True, stats=local_meta)
            else:
                catalog.add_item_to_catalog(item, tid=tid, color=color, success=False, error="Local file read error")
            return
        else:
            logger.warning(f"{tid}: Local file {filename} not found, trying download")

    try:
        data = download_file(url)
        content_type = item.get("content_type", "")
        text = _extract_text(data, url, tid, content_type)

        if not text or not text.strip():
            raise ValueError("Empty content after conversion")

        stats = _finalize_text(text, url, tid)

        filename = corpus_text_path(CORPUS_DIR, item.get("major_tradition", "Unknown"), item["tradition"], tid)

        with data_lock:
            ensure_dir(filename.parent)
            filename.write_bytes(stats["data_utf8"])

        with data_lock:
            metadata.append(
                _build_metadata(item, path=str(filename.resolve()), color=color, stats=stats)
            )
            processed_urls.add(url)

        catalog.add_item_to_catalog(item, tid=tid, color=color, success=True, stats=stats)
        logger.info(f"Saved successfully: {filename.name} (words: {stats['word_count']}, color: {color})")

    except Exception as e:
        logger.error(f"{tid}: Processing error: {e}")
        catalog.add_item_to_catalog(item, tid=tid, color=color, success=False, error=f"Error: {e}")


def _update_traditions_info(filter_type: set[str], force: bool) -> None:
    tradition_books: dict[str, set] = {}
    if Path(DOWNLOAD_LIST_FILE).exists():
        with open(DOWNLOAD_LIST_FILE, encoding="utf-8") as f:
            full_items = json.load(f)
            for item in full_items:
                if item.get("type") in filter_type and "tradition" in item:
                    trad = item["tradition"]
                    if trad not in tradition_books:
                        tradition_books[trad] = set()
                    tradition_books[trad].add(_item_tid(item))

    info_file_path = CORPUS_DIR / "traditions_info.json"
    existing_info: dict = {}

    if info_file_path.exists():
        if force:
            backup_path = CORPUS_DIR / "traditions_info_backup.json"
            shutil.copy2(info_file_path, backup_path)
            logger.warning(f"force=True: old reference file saved as {backup_path.name}, creating a clean template.")
        else:
            try:
                with open(info_file_path, encoding="utf-8") as f:
                    existing_info = json.load(f)
            except Exception as e:
                logger.error(f"Error reading traditions_info.json: {e}")

    changed = False
    for trad in sorted(tradition_books):
        color = get_tradition_color(trad)
        books_list = sorted(tradition_books[trad])

        if trad not in existing_info:
            existing_info[trad] = {
                "description": "",
                "region": "",
                "coordinates": [],
                "color": color,
                "books": books_list,
            }
            changed = True
        else:
            if "color" not in existing_info[trad]:
                existing_info[trad]["color"] = color
                changed = True
            if existing_info[trad].get("books") != books_list:
                existing_info[trad]["books"] = books_list
                changed = True

    with open(info_file_path, "w", encoding="utf-8") as f:
        json.dump(existing_info, f, ensure_ascii=False, indent=2)

    if changed and not force:
        logger.info("traditions_info.json updated (colors added or book lists refreshed).")


def build_corpus(filter_type: set[str], force: bool = False):
    ensure_dir(CORPUS_DIR)
    catalog.clear_catalog()
    metadata: list[dict] = []

    download_list = load_download_list(filter_type, force)

    _update_traditions_info(filter_type, force)

    processed_urls: set[str] = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, encoding="utf-8") as f:
            processed_urls = set(json.load(f))

    logger.info(f"Starting multithreaded build (items: {len(download_list)})")

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [executor.submit(process_single_item, item, force, metadata, processed_urls) for item in download_list]
        for future in concurrent.futures.as_completed(futures):
            exc = future.exception()
            if exc:
                logger.error(f"Unhandled error in worker thread: {exc}")

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(catalog.CSV_HEADER)
        writer.writerows(row.as_csv_row() for row in catalog.catalog_rows)

    with open(PROCESSED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_urls), f, ensure_ascii=False, indent=2)

    logger.info("Corpus build complete.")
    logger.info(f"Total records: {len(catalog.catalog_rows)}")

    available_rows = [row for row in catalog.catalog_rows if row.available]
    logger.info(f"Available: {len(available_rows)}")
    logger.info(f"Unavailable: {len(catalog.catalog_rows) - len(available_rows)}")

    if available_rows:
        total_words = sum(row.word_count for row in available_rows)
        total_sentences = sum(row.sentence_count for row in available_rows)
        logger.info("\nOverall statistics for available texts:")
        logger.info(f"  Total words: {total_words}")
        logger.info(f"  Total sentences: {total_sentences}")
        logger.info(f"  Average words per text: {total_words / len(available_rows):.1f}")
