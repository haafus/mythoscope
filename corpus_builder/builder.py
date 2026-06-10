import concurrent.futures
import csv
import json
import shutil
import threading
from datetime import datetime
from pathlib import Path

from . import catalog, logger
from .config import CATALOG_FILE, CORPUS_DIR, DOWNLOAD_LIST_FILE, METADATA_FILE, PROCESSED_URLS_FILE
from .downloader import download_file, load_download_list
from .utils import (
    _decode_bytes,
    count_sentences,
    count_words,
    ensure_dir,
    get_tradition_color,
    html_to_text,
    md5,
    normalize_text,
    pdf_to_text,
    sanitize_filename,
)

data_lock = threading.Lock()


def process_local_file(filename: Path, item: dict, color: str) -> dict | None:
    tid = item.get("title", item.get("id", "unknown_id"))
    url = item["url"]

    try:
        logger.info(f"{tid}: Processing existing file {filename}")
        existing_data = filename.read_bytes()
        h = md5(existing_data)

        if filename.suffix.lower() == ".pdf":
            text = pdf_to_text(existing_data)
        else:
            text = _decode_bytes(existing_data)

        text = normalize_text(text)
        char_count = len(text)
        word_count = count_words(text)
        sentence_count = count_sentences(text)

        return {
            "id": tid,
            "major_tradition": item.get("major_tradition", "Unknown"),
            "tradition": item["tradition"],
            "language": item["language"],
            "type": item["type"],
            "url": url,
            "date_downloaded": datetime.utcnow().isoformat(),
            "md5": h,
            "path": str(filename.resolve()),
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "color": color,
        }
    except Exception as e:
        logger.error(f"{tid}: Error processing local file {filename}: {e}")
        return None


def process_single_item(item: dict, force: bool, metadata: list[dict], processed_urls: set[str]):
    tid = item.get("title", item.get("id", "unknown_id"))
    tradition = item["tradition"]
    major_tradition = item.get("major_tradition", "Unknown")
    lang = item["language"]
    ftype = item["type"]
    url = item["url"]
    description = item.get("description", "")

    color = get_tradition_color(tradition)

    if "_local_file" in item and not force:
        filename = Path(item["_local_file"])
        if filename.exists():
            local_meta = process_local_file(filename, item, color)
            if local_meta:
                with data_lock:
                    metadata.append(local_meta)
                    processed_urls.add(url)

                catalog.add_to_catalog(
                    tid,
                    major_tradition,
                    tradition,
                    lang,
                    ftype,
                    url,
                    True,
                    local_meta["word_count"],
                    local_meta["sentence_count"],
                    color,
                    description,
                )
            else:
                err_desc = f"{description} [Local file read error]" if description else "Local file read error"
                catalog.add_to_catalog(tid, major_tradition, tradition, lang, ftype, url, False, 0, 0, color, err_desc)
            return
        else:
            logger.warning(f"{tid}: Local file {filename} not found, trying download")

    try:
        data = download_file(url)
        content_type = item.get("content_type", "")
        text = ""

        is_pdf = url.lower().endswith(".pdf") or "application/pdf" in content_type or data[:4] == b"%PDF"
        is_html = (
            b"<html" in data[:200].lower() or "text/html" in content_type or b"<!doctype html" in data[:200].lower()
        )

        if is_pdf:
            logger.debug(f"{tid}: PDF detected, extracting text")
            text = pdf_to_text(data)
        elif is_html:
            logger.debug(f"{tid}: HTML detected, converting to text")
            text = html_to_text(data)
        else:
            text = normalize_text(_decode_bytes(data))

        if not text or not text.strip():
            raise ValueError("Empty content after conversion")

        data_utf8 = text.encode("utf-8")

        major_tradition_path = sanitize_filename(major_tradition.replace("/", "_").replace(" ", "_"))
        tradition_path = sanitize_filename(tradition.replace("/", "_").replace(" ", "_"))
        title_path = sanitize_filename(tid.replace("/", "_").replace(" ", "_"))

        folder = CORPUS_DIR / major_tradition_path / tradition_path / title_path
        filename = folder / f"{title_path}.txt"

        with data_lock:
            ensure_dir(filename.parent)

        filename.write_bytes(data_utf8)

        h = md5(data_utf8)
        char_count = len(text)
        word_count = count_words(text)
        sentence_count = count_sentences(text)

        with data_lock:
            metadata.append(
                {
                    "id": tid,
                    "major_tradition": major_tradition,
                    "tradition": tradition,
                    "language": lang,
                    "type": ftype,
                    "url": url,
                    "date_downloaded": datetime.utcnow().isoformat(),
                    "md5": h,
                    "path": str(filename.resolve()),
                    "char_count": char_count,
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "color": color,
                }
            )
            processed_urls.add(url)

        catalog.add_to_catalog(
            tid, major_tradition, tradition, lang, ftype, url, True, word_count, sentence_count, color, description
        )
        logger.info(f"Saved successfully: {title_path}.txt (words: {word_count}, color: {color})")

    except Exception as e:
        logger.error(f"{tid}: Processing error: {e}")

        err_desc = f"{description} [Error: {e}]" if description else str(e)
        catalog.add_to_catalog(tid, major_tradition, tradition, lang, ftype, url, False, 0, 0, color, err_desc)


def build_corpus(filter_type: set[str], force: bool = False):
    ensure_dir(CORPUS_DIR)
    catalog.clear_catalog()
    metadata = []

    download_list = load_download_list(filter_type, force)

    tradition_books = {}
    if Path(DOWNLOAD_LIST_FILE).exists():
        with open(DOWNLOAD_LIST_FILE, encoding="utf-8") as f:
            full_items = json.load(f)
            for item in full_items:
                if item.get("type") in filter_type and "tradition" in item:
                    trad = item["tradition"]
                    tid = item.get("title", item.get("id", "unknown_id"))

                    if trad not in tradition_books:
                        tradition_books[trad] = set()
                    tradition_books[trad].add(tid)

    unique_traditions = set(tradition_books.keys())

    info_file_path = CORPUS_DIR / "traditions_info.json"
    existing_info = {}

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

    added_new_traditions = False
    for trad in sorted(unique_traditions):
        color = get_tradition_color(trad)

        books_list = sorted(list(tradition_books[trad]))

        if trad not in existing_info:
            existing_info[trad] = {
                "description": "",
                "region": "",
                "coordinates": [],
                "color": color,
                "books": books_list,
            }
            added_new_traditions = True
        else:
            if "color" not in existing_info[trad]:
                existing_info[trad]["color"] = color
                added_new_traditions = True

            if existing_info[trad].get("books") != books_list:
                existing_info[trad]["books"] = books_list
                added_new_traditions = True

    with open(info_file_path, "w", encoding="utf-8") as f:
        json.dump(existing_info, f, ensure_ascii=False, indent=2)

    if added_new_traditions and not force:
        logger.info("traditions_info.json updated (colors added or book lists refreshed).")

    processed_urls: set[str] = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, encoding="utf-8") as f:
            processed_urls = set(json.load(f))

    logger.info(f"Starting multithreaded build (items: {len(download_list)})")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for item in download_list:
            executor.submit(process_single_item, item, force, metadata, processed_urls)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
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
        )
        writer.writerows(catalog.catalog_rows)

    with open(PROCESSED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_urls), f, ensure_ascii=False, indent=2)

    logger.info("Corpus build complete.")
    logger.info(f"Total records: {len(catalog.catalog_rows)}")

    available = sum(1 for row in catalog.catalog_rows if row[6])
    logger.info(f"Available: {available}")
    logger.info(f"Unavailable: {len(catalog.catalog_rows) - available}")

    if available > 0:
        total_words = sum(row[7] for row in catalog.catalog_rows if row[6])
        total_sentences = sum(row[8] for row in catalog.catalog_rows if row[6])
        logger.info("\nOverall statistics for available texts:")
        logger.info(f"  Total words: {total_words}")
        logger.info(f"  Total sentences: {total_sentences}")
        logger.info(f"  Average words per text: {total_words / available:.1f}")
