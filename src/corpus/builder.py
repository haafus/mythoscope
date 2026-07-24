import concurrent.futures
import json
import logging
import statistics
import threading
from datetime import datetime, timezone
from pathlib import Path

from fetch_cache import fetch_to_cache
from json_utils import save_json
from settings import settings

from .clean_gutenberg import clean_gutenberg_in_builder, trim_to_content
from .downloader import load_download_list
from .extraction import _decode_bytes, html_to_text, pdf_to_text
from .locator import corpus_raw_path, document_id
from .sources import (
    WEB_SCHEMES,
    file_source_unchanged,
    is_file_source,
    read_local_to_cache,
    source_scheme,
)
from .traditions_config import flat_traditions, load_traditions_tree, validate_traditions
from .utils import (
    content_fingerprint,
    count_sentences,
    count_words,
    ensure_dir,
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
        # Per-doc content fingerprint (D2): blake2b of the cleaned text. Stored once in
        # the catalog; the embeddings stage folds it into each chunk's staleness key so a
        # text edit re-embeds and a pure rename does not (pipeline §4).
        "fingerprint": content_fingerprint(data_utf8),
        "char_count": len(text),
        "word_count": count_words(text),
        "sentence_count": count_sentences(text),
    }
    return data_utf8, stats


def _build_metadata(item: dict, *, path: str, stats: dict) -> dict:
    return {
        **item,
        # Stable identity (D1): blake2b of the normalized locator — rename-/edit-stable,
        # and the raw-archive key after the §6 re-key. Persisted once, never regenerated.
        "document_id": document_id(item["url"]),
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
            source=title,
        )
    return _decode_bytes(data)


def _download_and_process(item: dict, region: str) -> dict | None:
    title = item["title"]
    url = item["url"]

    try:
        raw_cache = corpus_raw_path(Path(settings.corpus_dir) / "raw", url)
        scheme = source_scheme(url)
        if scheme in WEB_SCHEMES:
            # Raw is a pinned, immutable archive: build only acquires-if-missing and never
            # re-fetches (fetch/build split, pipeline §5). `--force` rebuilds the derived
            # text from this raw; re-fetching upstream is the separate `mytho refresh`.
            data = fetch_to_cache(url, raw_cache, force=False)
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

        filename = text_path(settings.corpus_dir, region, item["tradition"], title)

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

    # Fail loud before any work: an unknown tradition or a non-canon region must stop the
    # build, not silently degrade to "" / a grey default (§2.12).
    tree = load_traditions_tree(settings.config_dir)
    validate_traditions(tree, download_list)

    # Region groups the file layout (corpus/<Region>/<Tradition>/<Title>.txt, §6) but is
    # NOT stored on the row — books carry `tradition` only; region/colour resolve from the
    # tree at serve time (B1). `traditions.json` is no longer generated (config is served, §2.9).
    trad_region = flat_traditions(tree)

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
            raw_cache = corpus_raw_path(Path(settings.corpus_dir) / "raw", url)
            reuse = file_source_unchanged(url, raw_cache, settings.sources_dir)
        else:
            reuse = output_present

        if reuse:
            # Populate-once: an older catalog row predates document_id — backfill it (the
            # locator rule is deterministic, so this equals what a rebuild would mint).
            prev.setdefault("document_id", document_id(url))
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
            futures = {
                executor.submit(_download_and_process, item, trad_region[item["tradition"]]): item
                for item in to_download
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    new_metadata.append(result)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        metadata.extend(new_metadata)
        logger.info(f"Downloaded: {len(new_metadata)}, failed: {len(to_download) - len(new_metadata)}")

    # Atomic swap (write .tmp then os.replace) so a crash mid-write can't leave a
    # truncated catalog whose stored fingerprints would lie to the next build (§9.4).
    save_json(settings.corpus_dir / "corpus.json", metadata, indent=2)

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
