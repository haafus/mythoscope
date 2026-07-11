import concurrent.futures
import json
import logging
import statistics
import threading
from datetime import datetime, timezone
from pathlib import Path

from fetch_cache import cache_path, fetch_to_cache
from settings import settings

from .clean_gutenberg import clean_gutenberg_in_builder, trim_to_content
from .downloader import load_download_list
from .extraction import _decode_bytes, html_to_text, pdf_to_text
from .sources import (
    WEB_SCHEMES,
    file_source_unchanged,
    is_file_source,
    read_local_to_cache,
    source_scheme,
)
from .utils import (
    count_sentences,
    count_words,
    ensure_dir,
    get_tradition_color,
    md5,
    normalize_text,
    text_path,
)

logger = logging.getLogger(__name__)
data_lock = threading.Lock()




def _finalize_text(
    text: str,
    url: str,
    title: str,
    content_start: str | None = None,
    content_end: str | None = None,
) -> tuple[bytes, dict]:
    text = normalize_text(text)
    text = clean_gutenberg_in_builder(text, url, title)
    text = trim_to_content(text, content_start, content_end, title)
    data_utf8 = text.encode("utf-8")
    stats = {
        "md5": md5(data_utf8),
        "char_count": len(text),
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
    }
    return data_utf8, stats


def _build_metadata(item: dict, *, path: str, stats: dict) -> dict:
    return {
        **item,
        "date_downloaded": datetime.now(timezone.utc).isoformat(),
        "path": path,
        **stats,
    }



def _extract_text(data: bytes, url: str, title: str, content_type: str = "") -> str:
    is_pdf = url.lower().endswith(".pdf") or "application/pdf" in content_type or data[:4] == b"%PDF"
    is_html = (
        b"<html" in data[:200].lower() or "text/html" in content_type or b"<!doctype html" in data[:200].lower()
    )

    if is_pdf:
        logger.debug(f"{title}: PDF detected, extracting text")
        return pdf_to_text(
            data,
            extract_tables=settings.corpus.pdf_extract_tables,
            preserve_layout=settings.corpus.pdf_preserve_layout,
        )
    if is_html:
        logger.debug(f"{title}: HTML detected, converting to text")
        return html_to_text(
            data,
            include_comments=settings.corpus.html_include_comments,
            include_tables=settings.corpus.html_include_tables,
        )
    return _decode_bytes(data)


def _download_and_process(item: dict, force: bool = False) -> dict | None:
    title = item["title"]
    url = item["url"]

    try:
        raw_cache = cache_path(Path(settings.corpus_dir) / "raw", url)
        scheme = source_scheme(url)
        if scheme in WEB_SCHEMES:
            data = fetch_to_cache(url, raw_cache, force=force)
        elif is_file_source(url):
            data = read_local_to_cache(url, raw_cache, settings.sources_dir)
        else:
            raise ValueError(f"Unsupported source scheme {scheme!r} in url {url!r}")
        content_type = item.get("content_type", "")
        text = _extract_text(data, url, title, content_type)

        if not text or not text.strip():
            raise ValueError("Empty content after conversion")

        data_utf8, stats = _finalize_text(
            text, url, title, item.get("content_start"), item.get("content_end")
        )

        filename = text_path(settings.corpus_dir, item["major_tradition"], item["tradition"], title)

        with data_lock:
            ensure_dir(filename.parent)
            filename.write_bytes(data_utf8)

        rel_path = str(filename.resolve().relative_to(Path(settings.corpus_dir).resolve()))
        meta = _build_metadata(item, path=rel_path, stats=stats)
        logger.info(f"Saved successfully: {filename.name} (words: {stats['word_count']})")
        return meta

    except Exception:
        logger.exception("%s: Processing error", title)
        return None


# config/traditions.json is a category tree: major -> {traditions: {tradition -> info}}.
# major_tradition lives here, once per tradition (not duplicated per book).
def _load_traditions_config() -> dict:
    path = settings.config_dir / "traditions.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Error reading %s", path)
        return {}


def _flat_tradition_info(tree: dict) -> dict[str, dict]:
    flat: dict[str, dict] = {}
    for node in tree.values():
        for trad, info in (node.get("traditions") or {}).items():
            flat[trad] = info
    return flat


def _tradition_major_map(tree: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for major, node in tree.items():
        for trad in (node.get("traditions") or {}):
            mapping[trad] = major
    return mapping


def _update_traditions(force: bool) -> None:
    output_path = settings.corpus_dir / "traditions.json"
    flat = _flat_tradition_info(_load_traditions_config())

    corpus_traditions: set[str] = set()
    corpus_config = settings.config_dir / "corpus.json"
    if corpus_config.exists():
        with open(corpus_config, encoding="utf-8") as f:
            for item in json.load(f):
                if "tradition" in item:
                    corpus_traditions.add(item["tradition"])

    # Built corpus/traditions.json stays flat (tradition -> info) so nothing
    # downstream changes; the tree is only the source of truth in config/.
    result: dict = {}
    for trad in sorted(corpus_traditions | set(flat.keys())):
        info = dict(flat.get(trad, {"description": "", "coordinates": []}))
        info["color"] = get_tradition_color(trad)
        result[trad] = info

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def _load_existing_metadata() -> dict[str, dict]:
    path = settings.corpus_dir / "corpus.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        return {row["title"]: row for row in rows if "title" in row}
    except (OSError, json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to read existing %s: %s", path, e)
        return {}


def build_corpus(force: bool = False, max_texts: int | None = None):
    ensure_dir(settings.corpus_dir)

    download_list = load_download_list()
    if max_texts is not None:
        download_list = download_list[:max_texts]

    _update_traditions(force)

    # Books carry only `tradition`; resolve major_tradition from the tree so the
    # file path and the metadata row keep it (downstream is unchanged).
    trad_major = _tradition_major_map(_load_traditions_config())
    for item in download_list:
        item["major_tradition"] = trad_major.get(item.get("tradition"), "")
        if not item["major_tradition"]:
            logger.warning("No major_tradition for tradition %r (title=%r)",
                           item.get("tradition"), item.get("title"))

    existing = {} if force else _load_existing_metadata()

    to_download = []
    metadata: list[dict] = []
    corpus_root = Path(settings.corpus_dir).resolve()

    for item in download_list:
        title = item["title"]
        url = item.get("url", "")
        prev = existing.get(title)
        output_present = bool(prev) and (corpus_root / prev.get("path", "")).exists()
        # A local file source is reused only if its content hash still matches the
        # raw snapshot from the previous build (on-disk edits are re-ingested); the
        # snapshot lives in corpus/raw, so no hash is stored in the metadata. Web
        # sources are reused whenever their output file is still present.
        if output_present and is_file_source(url):
            raw_cache = cache_path(Path(settings.corpus_dir) / "raw", url)
            reuse = file_source_unchanged(url, raw_cache, settings.sources_dir)
        else:
            reuse = output_present

        if reuse:
            metadata.append(prev)
            logger.debug(f"{title}: already in corpus, skipping")
        else:
            to_download.append(item)

    logger.info(f"Corpus: {len(metadata)} cached, {len(to_download)} to download")

    if to_download:
        new_metadata: list[dict] = []

        # Manage the pool explicitly so Ctrl+C cancels pending downloads instead of
        # draining the whole queue (shutdown(wait=True) on a `with` exit would block).
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=settings.corpus.max_workers)
        try:
            futures = {executor.submit(_download_and_process, item, force): item for item in to_download}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    new_metadata.append(result)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        metadata.extend(new_metadata)
        logger.info(f"Downloaded: {len(new_metadata)}, failed: {len(to_download) - len(new_metadata)}")

    with open(settings.corpus_dir / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info("Corpus build complete. Total: %d texts", len(metadata))

    if metadata:
        counts = [m.get("word_count", 0) for m in metadata]
        total_sentences = sum(m.get("sentence_count", 0) for m in metadata)
        logger.info(f"  Total words: {sum(counts)}")
        logger.info(f"  Total sentences: {total_sentences}")
        logger.info(
            f"  Median words per text: {int(statistics.median(counts))} "
            f"(min {min(counts)}, max {max(counts)})"
        )
