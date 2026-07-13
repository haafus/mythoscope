import json
import logging
from itertools import islice

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from corpus.iterator import iter_files
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
    force: bool = False,
    max_texts: int | None = None,
) -> None:
    """Extract entities and (re)build graphs from the cached extraction.

    Every run rebuilds all graphs from ``extraction_cache.jsonl``; the LLM is
    only invoked for chunks that aren't cached yet (and is constructed lazily, so
    rebuilding from a complete cache needs no API key). ``force`` clears each
    book's cache first, forcing a full re-extraction.
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

    files = iter_files(settings.corpus_dir)
    if max_texts is not None:
        files = islice(files, max_texts)

    stopped = False
    for file_info in files:
        text_id = file_info.text_id

        book_out_dir = settings.graphs_dir / text_id
        book_out_dir.mkdir(parents=True, exist_ok=True)

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

        def _kept(total, keep):
            return total if keep is None else len(keep)

        logger.info(f"Beings:    {len(all_beings)} found, kept {_kept(len(all_beings), keep_beings)}")
        logger.info(f"Realms:    {len(all_locations)} found, kept {_kept(len(all_locations), keep_realms)}")
        logger.info(f"Ages:      {len(all_times)} found, kept {_kept(len(all_times), keep_ages)}")
        logger.info(f"Relations: {len(all_relations)} found")

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
    else:
        logger.info("Graph build complete.")
