import json
import logging
from itertools import islice
from pathlib import Path

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from corpus.iterator import iter_files
from embeddings.chunking import chunk_text
from llm import LLMProcessor, map_concurrent
from settings import settings

from .completion import is_book_complete
from .extraction import deduplicate_entities, deduplicate_relations, extract_from_chunk
from .graph_generator import (
    filter_by_names,
    generate_ages_graph,
    generate_beings_graph,
    generate_realms_graph,
    top_mentioned_names,
)

logger = logging.getLogger(__name__)


def _extract_chunks(
    processor, uncached, chunk_prompts, cache, cache_path, max_concurrent, total_chunks, cached
) -> bool:
    """Extract uncached chunks concurrently, persisting each result to the cache.

    Progress is reported against the whole file (``cached`` already done +
    this run's progress, out of ``total_chunks``). Returns False if the run
    stopped early on the daily rate limit.
    """
    done = 0

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


def build_graphs(
    llm: str | None = None,
    force: bool = False,
    max_texts: int | None = None,
    regraph: bool = False,
) -> None:
    """Extract entities and build graphs.

    With ``regraph=True`` no LLM is used: graphs are rebuilt from the cached
    extraction (``extraction_cache.jsonl``) only, overwriting existing outputs.
    Books whose extraction isn't fully cached are skipped.
    """
    prompts_path = Path("config/graphs_prompts.json")
    try:
        prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to load prompts from {prompts_path}: {e}") from e

    graphs_cfg = settings.graphs
    # In regraph mode we never call the LLM, so don't construct a client
    # (it would require an API key even though no request is made).
    processor = None if regraph else LLMProcessor(model_alias=llm, use_json_mode=graphs_cfg.use_json_mode)

    if regraph:
        logger.info("Rebuilding graphs from cached extraction (no LLM calls)...")
    else:
        logger.info(f"Starting graph generation (model={processor.model_name}, force={force})...")

    files = iter_files(settings.corpus_dir)
    if max_texts is not None:
        files = islice(files, max_texts)

    stopped = False
    for file_info in files:
        text_id = file_info.text_id

        book_out_dir = settings.graphs_dir / text_id
        book_out_dir.mkdir(parents=True, exist_ok=True)

        if is_book_complete(book_out_dir) and not force and not regraph:
            logger.info(f"--- Skipping: {text_id} (already complete) ---")
            continue

        text = file_info.read_text()

        logger.info(f"--- Processing: {text_id} ---")

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
        if uncached and not regraph:
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
            if regraph:
                logger.warning(
                    f"{text_id}: {missing}/{len(chunks)} chunks not in cache — "
                    "run extraction first; skipping."
                )
            else:
                logger.warning(
                    f"{text_id}: {missing}/{len(chunks)} chunks failed extraction — "
                    "book left incomplete, rerun to retry."
                )
            continue

        results: dict[str, list] = {"beings": [], "relations": [], "locations": [], "times": []}
        for chunk in chunks:
            chunk_results = cache[chunk_hash(chunk)]
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

        def _kept(total, keep):
            return total if keep is None else len(keep)

        logger.info(
            f"Entities — Beings: {len(all_beings)} found, kept {_kept(len(all_beings), keep_beings)}; "
            f"Realms: {len(all_locations)} found, kept {_kept(len(all_locations), keep_realms)}; "
            f"Ages: {len(all_times)} found, kept {_kept(len(all_times), keep_ages)} "
            f"(Relations: {len(all_relations)})"
        )

        try:
            generate_beings_graph(all_beings, all_relations, book_out_dir, keep=keep_beings)
            generate_realms_graph(all_locations, book_out_dir, keep=keep_realms)
            generate_ages_graph(top_times, book_out_dir)

        except Exception:
            logger.exception("Error generating graph for %s", text_id)

    if processor is not None and processor.governor.stats()["requests"]:
        logger.info(f"LLM usage: {processor.governor.summary()}")

    if stopped:
        logger.warning("Graph generation stopped early (rate limit); rerun to resume.")
    elif regraph:
        logger.info("Graph rebuild complete.")
    else:
        logger.info("Graph generation complete.")
