import logging
from pathlib import Path

import numpy as np

from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from llm import map_concurrent
from settings import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = (
    "You are a comparative mythology analyst. "
    "Summarize the plot of this text fragment in 2-3 neutral sentences. "
    "Do NOT mention character names, place names, or culture-specific terms. "
    "Replace proper nouns with generic roles (e.g. 'the hero', 'the god', 'the trickster'). "
    "Focus only on the narrative structure: what happens, what transforms, what conflict arises."
)


def generate_motif_summaries(
    data: list[dict],
    output_dir: Path,
    force: bool = False,
) -> list[str]:
    from llm import LLMProcessor

    llm = LLMProcessor(use_json_mode=False)

    cache_path = output_dir / "motif_summaries.jsonl"
    if force:
        clear_cache(cache_path)
    cache = load_cache(cache_path)

    uncached = [item for item in data if chunk_hash(item.get("text", "")) not in cache]
    if uncached:
        logger.info(
            f"Generating {len(uncached)}/{len(data)} summaries "
            f"(concurrency={settings.projection.max_concurrent})..."
        )

        def _store(item: dict, summary: str) -> None:
            if summary:
                key = chunk_hash(item.get("text", ""))
                append_cache(cache_path, key, summary)
                cache[key] = summary

        completed = map_concurrent(
            uncached,
            lambda item: llm.ask_text(SUMMARY_PROMPT, item.get("text", "")[:4000]),
            settings.projection.max_concurrent,
            on_result=_store,
        )
        if not completed:
            logger.warning("Daily rate limit reached — some summaries are missing; rerun to resume.")

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


def run_motif_analysis(
    data: list[dict],
    output_dir: Path,
    embedding_model: str,
    force: bool = False,
) -> None:
    from .visualization import generate_scatter

    summaries = generate_motif_summaries(data, output_dir, force=force)

    empty_count = sum(1 for s in summaries if not s.strip())
    if empty_count > len(summaries) * 0.5:
        logger.error(f"Too many empty summaries ({empty_count}/{len(summaries)}), aborting motif UMAP")
        return

    motif_embeddings = embed_summaries(summaries, embedding_model)

    logger.info("Building motif UMAP projection...")
    generate_scatter(
        data,
        motif_embeddings,
        output_path=output_dir / "motif_umap.json",
        model_name=embedding_model,
    )
    logger.info("Motif UMAP projection saved")
