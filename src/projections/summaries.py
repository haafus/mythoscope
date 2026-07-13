import json
import logging
from pathlib import Path

import numpy as np

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from llm import map_concurrent
from settings import settings

logger = logging.getLogger(__name__)


def load_summary_prompt() -> str:
    """The plot-summary prompt, shared with the graph prompts in ``config/prompts.json``."""
    prompts_path = settings.config_dir / "prompts.json"
    try:
        return json.loads(prompts_path.read_text(encoding="utf-8"))["summary"]
    except Exception as e:
        raise RuntimeError(f"Failed to load 'summary' prompt from {prompts_path}: {e}") from e


def generate_summaries(
    data: list[dict],
    output_dir: Path,
    force: bool = False,
) -> list[str]:
    from llm import LLMProcessor

    llm = LLMProcessor(use_json_mode=False)
    summary_prompt = load_summary_prompt()

    cache_path = output_dir / "summaries.jsonl"
    if force:
        clear_cache(cache_path)
    cache = load_cache(cache_path)

    uncached = [item for item in data if chunk_hash(item.get("text", "")) not in cache]
    if uncached:
        logger.info(
            f"Generating {len(uncached)}/{len(data)} summaries "
            f"(concurrency={settings.projections.max_concurrent})..."
        )
        def _store(item: dict, summary: str) -> None:
            if summary:
                key = chunk_hash(item.get("text", ""))
                append_cache(cache_path, key, summary)
                cache[key] = summary

        completed = map_concurrent(
            uncached,
            lambda item: llm.ask_text(summary_prompt, item.get("text", "")[:4000]),
            settings.projections.max_concurrent,
            on_result=_store,
        )
        if not completed:
            logger.warning("Daily rate limit reached — some summaries are missing; rerun to resume.")

    if llm.governor.stats()["requests"]:
        logger.info(f"LLM usage: {llm.governor.summary()}")

    summaries = [cache.get(chunk_hash(item.get("text", "")), "") for item in data]
    cached_count = sum(1 for s in summaries if s)
    logger.info(f"Summaries ready: {cached_count}/{len(summaries)} ({len(uncached)} attempted this run)")

    return summaries


def embed_summaries(summaries: list[str], model_name: str) -> np.ndarray:
    from embeddings.model_manager import EmbeddingEncoder

    logger.info(f"Embedding {len(summaries)} summaries with {model_name}...")
    encoder = EmbeddingEncoder()
    encoder.load(model_name)
    embeddings: np.ndarray = encoder.encode(
        summaries,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    encoder.unload()
    return embeddings


def run_summaries(
    data: list[dict],
    output_dir: Path,
    embedding_model: str,
    force: bool = False,
) -> None:
    from .visualization import generate_scatter

    summaries = generate_summaries(data, output_dir, force=force)

    empty_count = sum(1 for s in summaries if not s.strip())
    if empty_count > len(summaries) * 0.5:
        logger.error(f"Too many empty summaries ({empty_count}/{len(summaries)}), aborting summaries UMAP")
        return
    if empty_count:
        logger.warning(
            f"{empty_count}/{len(summaries)} summaries are empty (failed or not yet generated) "
            "and enter the UMAP as degenerate points — rerun to fill them in."
        )

    summary_embeddings = embed_summaries(summaries, embedding_model)

    logger.info("Building summaries UMAP projection...")
    generate_scatter(
        data,
        summary_embeddings,
        output_path=output_dir / "summaries_umap.json",
        model_name=embedding_model,
    )
    logger.info("Summary UMAP projection saved")
