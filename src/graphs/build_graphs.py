import json
import logging
from itertools import islice
from pathlib import Path

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from corpus.iterator import iter_files
from embeddings.chunking import chunk_text
from json_utils import save_json
from llm import LLMProcessor, map_concurrent
from settings import settings

from .completion import is_book_complete
from .extraction import deduplicate_entities, deduplicate_relations, extract_from_chunk
from .graph_generator import generate_ages_graph, generate_beings_graph, generate_realms_graph

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


def build_graphs(llm: str | None = None, force: bool = False, max_texts: int | None = None) -> None:
    prompts_path = Path("config/graphs_prompts.json")
    try:
        prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to load prompts from {prompts_path}: {e}") from e

    graphs_cfg = settings.graphs
    processor = LLMProcessor(
        model_alias=llm,
        use_json_mode=graphs_cfg.use_json_mode,
    )

    logger.info(f"Starting graph generation (model={processor.model_name}, force={force})...")

    files = iter_files(settings.corpus_dir)
    if max_texts is not None:
        files = islice(files, max_texts)

    stopped = False
    for file_info in files:
        text_id = file_info.text_id

        book_out_dir = settings.graphs_dir / text_id
        book_out_dir.mkdir(parents=True, exist_ok=True)

        if is_book_complete(book_out_dir) and not force:
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
        if uncached:
            cached = len(chunks) - len(uncached)
            logger.info(
                f"Extracting {len(uncached)}/{len(chunks)} chunks "
                f"(concurrency={graphs_cfg.max_concurrent})..."
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
        logger.info(
            f"Extracted unique items: Beings ({len(all_beings)}), Relations ({len(all_relations)}), Locations ({len(all_locations)}), Times ({len(all_times)})"
        )

        try:
            save_json(book_out_dir / "raw_beings.json", all_beings, indent=2)
            save_json(book_out_dir / "relations.json", all_relations, indent=2)
            save_json(book_out_dir / "locations.json", all_locations, indent=2)
            save_json(book_out_dir / "times.json", all_times, indent=2)

            generate_beings_graph(all_beings, all_relations, book_out_dir)
            generate_realms_graph(all_locations, book_out_dir)
            generate_ages_graph(all_times, book_out_dir)

        except Exception:
            logger.exception("Error saving files or generating graph for %s", text_id)

    if processor.governor.stats()["requests"]:
        logger.info(f"LLM usage: {processor.governor.summary()}")

    if stopped:
        logger.warning("Graph generation stopped early (rate limit); rerun to resume.")
    else:
        logger.info("Graph generation complete.")
