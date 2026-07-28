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

from .clean_gutenberg import _content_marker_regex, clean_gutenberg_in_builder, trim_to_content
from .downloader import load_download_list
from .extraction import _decode_bytes, html_to_text, pdf_to_text
from .fingerprint import source_fingerprint
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


def _prune_orphan_texts(keep_paths) -> None:
    """Delete any ``.txt`` whose document is no longer in config. ``keep_paths`` is the set of
    every configured document's expected text path (not merely what built this run), so a
    document that only failed to (re)build keeps its previous ``.txt``. The raw archive
    (``corpus/raw/``, no ``.txt``) is untouched."""
    root = Path(settings.corpus_dir).resolve()
    keep = {Path(p).resolve() for p in keep_paths}
    for txt in root.rglob("*.txt"):
        if "raw" not in txt.relative_to(root).parts and txt.resolve() not in keep:
            txt.unlink(missing_ok=True)
            logger.info("Pruned orphan text %s (no longer in config)", txt.relative_to(root))


def _ensure_source_fp(row: dict, url: str, item: dict) -> None:
    """One-off fp-init: give a row without ``source_fp`` one from the pinned raw + config
    (no re-fetch, no re-clean), so the corpus stage can decide staleness offline."""
    if "source_fp" not in row:
        raw_cache = corpus_raw_path(Path(settings.corpus_dir) / "raw", url)
        if raw_cache.exists():
            row["source_fp"] = source_fingerprint(
                raw_cache.read_bytes(), item.get("content_start"), item.get("content_end")
            )


def _build_metadata(item: dict, *, path: str, stats: dict, source_fp: str) -> dict:
    return {
        **item,
        # Stable identity (D1): blake2b of the normalized locator — rename-/edit-stable,
        # and the raw-archive key after the §6 re-key. Persisted once, never regenerated.
        "document_id": document_id(item["url"]),
        "date_downloaded": datetime.now(timezone.utc).isoformat(),
        "path": path,
        # Input fingerprint (pipeline §2.3): the stage's OWN offline staleness key
        # (raw + trim + clean_version), distinct from the output `fingerprint` in stats.
        "source_fp": source_fp,
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
        source_fp = source_fingerprint(data, item.get("content_start"), item.get("content_end"))
        meta = _build_metadata(item, path=rel_path, stats=stats, source_fp=source_fp)
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


def _validate_content_markers(download_list: list[dict]) -> None:
    """Warn — every build, not just when a doc rebuilds — for any configured
    ``content_start``/``content_end`` that does not match its book's text. A non-matching
    marker is a **silent no-op** in ``trim_to_content`` (the editorial front/back is kept,
    which can bloat extraction — e.g. the Poetic Edda proper-name index that ran the graph
    LLM into repeated timeouts). Runs up front against the pinned raw so a latent broken
    marker surfaces even when the document itself is up-to-date and skipped. Books whose raw
    is not cached yet are left to ``trim_to_content`` to warn about when they first build."""
    raw_dir = Path(settings.corpus_dir) / "raw"
    misses = 0
    for item in download_list:
        markers = {k: item[k] for k in ("content_start", "content_end") if item.get(k)}
        if not markers:
            continue
        raw = corpus_raw_path(raw_dir, item["url"])
        if not raw.exists():
            continue
        try:
            text = clean_gutenberg_in_builder(
                _extract_text(raw.read_bytes(), item["url"], item["title"]), item["url"], item["title"])
        except Exception:
            continue  # a real extract failure will surface in the actual build below
        for field, marker in markers.items():
            if not _content_marker_regex(marker).search(text):
                misses += 1
                logger.warning(
                    "content marker NOT FOUND: %s %s=%r — editorial matter is NOT being trimmed; "
                    "fix the marker in config/corpus.json", item["title"], field, marker)
    if misses:
        logger.warning("%d content marker(s) did not match their text (see warnings above)", misses)


def build_corpus(force: bool = False, rebuild: set[str] | None = None):
    """Build the corpus catalog + .txt tree — incrementally.

    The catalog is accumulated state: whichever documents this run doesn't process carry their
    existing built row, so a partial build merges into the full catalog rather than truncating
    it. ``rebuild`` (the driver's key set of document_ids) is authoritative when given — process
    EXACTLY those ids and nothing else missing (honouring Stage.build's "exactly these keys"
    contract, which is what lets a scoped or ``--sample`` build touch only its keys); ``None``
    makes every configured document eligible. ``force`` re-derives every processed document."""
    ensure_dir(settings.corpus_dir)

    download_list = load_download_list()  # the FULL desired set — always

    # Fail loud before any work: an unknown tradition or a non-canon region must stop the
    # build, not silently degrade to "" / a grey default (§2.12).
    tree = load_traditions_tree(settings.config_dir)
    validate_traditions(tree, download_list)
    _validate_content_markers(download_list)  # warn on any content_start/end that no longer matches

    # Region groups the file layout (corpus/<Region>/<Tradition>/<Title>.txt, §6) but is
    # NOT stored on the row — books carry `tradition` only; region/colour resolve from the
    # tree at serve time (B1). `traditions.json` is no longer generated (config is served, §2.9).
    trad_region = flat_traditions(tree)

    # Which documents this run (re)processes; every other configured document carries its
    # existing built row, so a partial build merges into the full catalog rather than truncating.
    # `rebuild` (the driver's key set) is authoritative — process EXACTLY those document_ids,
    # honouring Stage.build's "exactly these keys" contract, so a scoped/sampled build touches
    # only its keys instead of every missing document; otherwise everything is eligible.
    if rebuild is not None:
        process_titles = {item["title"] for item in download_list if document_id(item.get("url", "")) in rebuild}
    else:
        process_titles = {item["title"] for item in download_list}
    existing = _load_existing_metadata()  # always, so unprocessed documents carry their built row

    to_download = []
    metadata: list[dict] = []
    corpus_root = Path(settings.corpus_dir).resolve()

    for item in download_list:
        title = item["title"]
        url = item.get("url", "")
        prev = existing.get(title)
        output_present = bool(prev) and (corpus_root / prev.get("path", "")).exists()

        if title not in process_titles:
            # Not processed this run — carry its built row (if any) so the catalog stays full.
            if output_present:
                prev.setdefault("document_id", document_id(url))
                _ensure_source_fp(prev, url, item)
                metadata.append(prev)
            continue

        # A local file source is reused only if its content hash still matches the raw snapshot
        # from the previous build (on-disk edits are re-ingested); web sources are reused
        # whenever their output file is still present.
        if output_present and is_file_source(url):
            raw_cache = corpus_raw_path(Path(settings.corpus_dir) / "raw", url)
            reuse = file_source_unchanged(url, raw_cache, settings.sources_dir)
        else:
            reuse = output_present

        # force re-derives every processed document; rebuild forces the driver's named ids.
        if force or (rebuild is not None and document_id(url) in rebuild):
            reuse = False

        if reuse:
            prev.setdefault("document_id", document_id(url))
            _ensure_source_fp(prev, url, item)
            metadata.append(prev)
            logger.debug(f"{title}: already in corpus, skipping")
        else:
            to_download.append(item)

    logger.info(f"Corpus: {len(metadata)} cached, {len(to_download)} to (re)build")

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

    # Self-prune orphans (symmetric to build_embeddings pruning chunks whose document left the
    # corpus): reap any .txt whose document is no longer in config. Config-authoritative and
    # always safe — the catalog stays full every run, so this never touches a valid text.
    keep = {
        text_path(settings.corpus_dir, trad_region[item["tradition"]], item["tradition"], item["title"])
        for item in download_list
    }
    _prune_orphan_texts(keep)

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
