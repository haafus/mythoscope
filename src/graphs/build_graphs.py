import json
import logging

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from corpus.iterator import iter_files
from corpus.utils import content_fingerprint
from embeddings.chunking import chunk_text
from llm import LLMProcessor, map_concurrent
from settings import settings

from .extraction import deduplicate_entities, deduplicate_relations, extract_from_chunk
from .graph_generator import (
    filter_by_names,
    generate_ages_graph,
    generate_beings_graph,
    generate_realms_graph,
    top_mentioned_names,
)
from .store import graph_dir

logger = logging.getLogger(__name__)

# Bump when the graph JSON *assembly* (graph_generator) changes but the extraction does not,
# so every book's `.fp` goes stale and a plain `mytho build graphs` regenerates the JSON from
# the pinned extraction cache — no LLM, no `--force` (which would clear the cache and re-extract).
# v2: strip trailing periods from attribute values.
GRAPH_ALGO_VERSION = "2"


def _extract_chunks(
    processor, uncached, chunk_prompts, cache, cache_path, max_concurrent, total_chunks, cached
) -> bool:
    """Extract uncached chunks concurrently, persisting each result to the cache.

    Progress is reported against the whole file (``cached`` already done +
    this run's progress, out of ``total_chunks``). Returns False if the run
    stopped early on the daily rate limit.
    """
    done = 0

    # Name the uncached chunks up front so a run stuck on one chunk shows exactly which
    # (id == extraction-cache key) and how big it is. Loud when few (the stuck case), quiet
    # on a big fresh build. Per-prompt latency/failure is logged in extraction._ask.
    level = logging.INFO if len(uncached) <= 3 else logging.DEBUG
    for c in uncached:
        logger.log(level, "  uncached chunk %s: %d chars | %r", chunk_hash(c), len(c), c[:80])

    def store(chunk: str, outcome: tuple[dict, bool]) -> None:
        nonlocal done
        done += 1
        chunk_results, complete = outcome
        if complete:
            key = chunk_hash(chunk)
            append_cache(cache_path, key, chunk_results)
            cache[key] = chunk_results
        suffix = "" if complete else " (incomplete, will retry next run)"
        logger.info(f"  Chunk {cached + done}/{total_chunks} extracted{suffix}.")

    return map_concurrent(
        uncached,
        lambda chunk: extract_from_chunk(processor, chunk, chunk_prompts),
        max_concurrent,
        on_result=store,
    )


def _graph_fingerprint(doc_fp: str, prompts: dict, graphs_cfg) -> str:
    """Canonical per-document graph fp: the doc content fingerprint folded with everything that
    changes the generated graphs — the extraction prompts, the LLM, the keep limit and chunking.
    A book whose .fp matches (and whose three JSONs exist) needs no regeneration."""
    parts = [
        doc_fp,
        GRAPH_ALGO_VERSION,
        str(graphs_cfg.llm),
        str(graphs_cfg.max_entities),
        str(graphs_cfg.chunk_size),
        str(graphs_cfg.chunk_overlap),
        prompts.get("beings", ""),
        prompts.get("relations", ""),
        prompts.get("locations", ""),
        prompts.get("time", ""),
    ]
    return content_fingerprint("\x00".join(parts).encode("utf-8"))


def build_graphs(
    rebuild: set[str],
    force: bool = False,
) -> None:
    """(Re)build graphs for exactly the books in ``rebuild`` (a set of document_ids).

    ``rebuild`` IS the authoritative work-list: the driver's desired/actual diff already
    decided which books are missing/stale (via the same ``_graph_fingerprint``), so the builder
    just executes it — it does **not** re-derive freshness. The LLM is invoked only for chunks not
    yet in ``extraction_cache.jsonl`` (constructed lazily, so a rebuild from a complete cache needs
    no API key), then the graphs are regenerated. ``force`` clears each book's cache first, forcing
    a full re-extraction. Freshness/skip decisions live only in the driver (see ``GraphsStage``).
    """
    prompts_path = settings.config_dir / "prompts.json"
    try:
        prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to load prompts from {prompts_path}: {e}") from e

    graphs_cfg = settings.graphs
    # Built lazily on the first uncached chunk so a pure cache rebuild needs no key.
    processor = None

    logger.info(f"Building graphs (force={force})...")

    files = list(iter_files(settings.corpus_dir))
    by_id = {fi.document_id: fi for fi in files}

    # `rebuild` IS the authoritative work-list — the driver's desired/actual diff already decided
    # (via the same `_graph_fingerprint`) which books are missing/stale. Build precisely those,
    # unconditionally: the builder does not re-derive freshness (that lives only in the driver).
    # `document_id` keys the graph dir (D1) — rename-invariant, so a rename never orphans a dir.
    pending: list[tuple] = []  # (file_info, book_out_dir, fp, fp_path) per book that WILL build
    for did in rebuild:
        file_info = by_id.get(did)
        if file_info is None:
            logger.warning("graphs: requested document_id %s is not in the corpus — skipping", did)
            continue
        book_out_dir = graph_dir(did)
        book_out_dir.mkdir(parents=True, exist_ok=True)
        fp = _graph_fingerprint(file_info.content_fingerprint(), prompts, graphs_cfg)
        pending.append((file_info, book_out_dir, fp, book_out_dir / ".fp"))

    total = len(pending)  # the denominator: how many books this run will build, not the corpus size

    stopped = False
    for idx, (file_info, book_out_dir, fp, fp_path) in enumerate(pending, start=1):
        text_id = file_info.text_id  # readable label for logs only

        text = file_info.read_text()

        logger.info(f"--- Processing: {text_id} ({idx}/{total}) ---")

        chunks = chunk_text(text, chunk_size=graphs_cfg.chunk_size, chunk_overlap=graphs_cfg.chunk_overlap)
        logger.info(f"Text split into {len(chunks)} chunks.")

        chunk_prompts = {
            "beings": prompts.get("beings", "Extract characters..."),
            "relations": prompts.get("relations", "Extract relations..."),
            "locations": prompts.get("locations", "Extract locations..."),
            "time": prompts.get("time", "Extract time..."),
        }

        cache_path = book_out_dir / "extraction_cache.jsonl"
        if force:
            clear_cache(cache_path)
        cache = load_cache(cache_path)

        uncached = [c for c in chunks if chunk_hash(c) not in cache]
        if uncached:
            if processor is None:  # first chunk that actually needs the LLM
                processor = LLMProcessor(
                    model_alias=graphs_cfg.llm,
                    temperature=graphs_cfg.temperature,
                    use_json_mode=graphs_cfg.use_json_mode,
                )
                logger.info(f"Extracting with model={processor.model_name}...")
            cached = len(chunks) - len(uncached)
            logger.info(
                f"Extracting {len(uncached)} new chunks "
                f"({cached} cached, {len(chunks)} total, concurrency={graphs_cfg.max_concurrent})..."
            )
            completed = _extract_chunks(
                processor, uncached, chunk_prompts, cache, cache_path,
                graphs_cfg.max_concurrent, len(chunks), cached,
            )
            if not completed:
                logger.warning(
                    f"Daily rate limit reached while processing '{text_id}' — stopping. "
                    "Cached progress is saved; rerun to resume."
                )
                stopped = True
                break

        missing = sum(1 for c in chunks if chunk_hash(c) not in cache)
        if missing:
            # Don't skip: build the graph from whatever chunks are cached.
            logger.warning(
                f"{text_id}: {missing}/{len(chunks)} chunks not cached — "
                "building the graph from the cached chunks only."
            )

        results: dict[str, list] = {"beings": [], "relations": [], "locations": [], "times": []}
        for chunk in chunks:
            chunk_results = cache.get(chunk_hash(chunk))
            if chunk_results is None:  # not cached — skip just this chunk
                continue
            for k in results:
                results[k].extend(chunk_results.get(k, []))

        all_beings = deduplicate_entities(results["beings"])
        all_relations = deduplicate_relations(results["relations"])
        all_locations = deduplicate_entities(results["locations"])
        all_times = deduplicate_entities(results["times"])

        # Keep only the N most-mentioned entities in each graph (None = keep all).
        max_entities = graphs_cfg.max_entities
        keep_beings = top_mentioned_names(all_beings, results["beings"], max_entities)
        keep_realms = top_mentioned_names(all_locations, results["locations"], max_entities)
        keep_ages = top_mentioned_names(all_times, results["times"], max_entities)
        top_times = filter_by_names(all_times, keep_ages)

        def _summary(total, keep, limit=max_entities):
            kept = total if keep is None else len(keep)
            dropped = total - kept
            if dropped > 0:
                return f"{total} found, kept {kept}, {dropped} dropped by limit ({limit})"
            return f"{total} found, kept {kept}"

        logger.info(f"Beings:    {_summary(len(all_beings), keep_beings)}")
        logger.info(f"Realms:    {_summary(len(all_locations), keep_realms)}")
        logger.info(f"Ages:      {_summary(len(all_times), keep_ages)}")
        logger.info(f"Relations: {len(all_relations)} found")

        try:
            generate_beings_graph(all_beings, all_relations, book_out_dir, keep=keep_beings)
            generate_realms_graph(all_locations, book_out_dir, keep=keep_realms)
            generate_ages_graph(top_times, book_out_dir)
            if not missing:  # stamp the fp only on a complete build so a partial one retries
                fp_path.write_text(fp, encoding="utf-8")
        except Exception:
            logger.exception("Error generating graph for %s", text_id)

    if processor is not None and processor.governor.stats()["requests"]:
        logger.info(f"LLM usage: {processor.governor.summary()}")

    if stopped:
        logger.warning("Graph generation stopped early (rate limit); rerun to resume.")
    else:
        logger.info("Graph build complete.")
