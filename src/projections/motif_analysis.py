import logging
from pathlib import Path

import numpy as np
from tqdm import tqdm

from chunk_cache import append_cache, chunk_hash, load_cache
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
) -> list[str]:
    from llm_client import LLMProcessor

    llm = LLMProcessor(use_json_mode=False)

    cache_path = output_dir / "motif_summaries.jsonl"
    cache = load_cache(cache_path)
    summaries: list[str] = []
    new_count = 0

    for item in tqdm(data, desc="Generating motif summaries", unit="chunk"):
        text = item.get("text", "")
        key = chunk_hash(text)

        if key in cache:
            summaries.append(cache[key])
            continue

        summary = llm.ask_text(SUMMARY_PROMPT, text[:4000])
        summaries.append(summary)
        new_count += 1

        if summary:
            append_cache(cache_path, key, summary)
            cache[key] = summary

    if new_count > 0:
        logger.info(f"Generated {new_count} new summaries, {len(summaries) - new_count} from cache")
    else:
        logger.info(f"All {len(summaries)} summaries loaded from cache")

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
) -> None:
    from .visualization import generate_scatter

    summaries = generate_motif_summaries(data, output_dir)

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
