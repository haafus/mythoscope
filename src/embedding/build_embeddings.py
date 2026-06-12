from __future__ import annotations

import gc
import logging
import shutil
from pathlib import Path

import torch

from settings import settings

from .builder import EmbeddingBuilder, normalize_text_type
from .cache_utils import cleanup_cache
from .chroma_manager import collection_name_for_model

logger = logging.getLogger(__name__)


def build_embeddings(
    clear_existing: bool | None = None,
    batch_size: int | None = None,
    model_name: str | None = None,
    models: list | None = None,
    chunking: str | None = None,
    text_type: str | None = None,
):
    if clear_existing is False:
        raise ValueError("Incremental Chroma writes are not supported for full embedding generation.")

    emb = settings.embedding

    MODEL_NAME = model_name or emb.default_model
    TEXT_TYPE: str = normalize_text_type(text_type or emb.text_type) or "all"
    CHUNKING = chunking or emb.default_chunking
    BATCH_SIZE = batch_size if batch_size is not None else emb.batch_size
    CLEAR_EXISTING = clear_existing if clear_existing is not None else True

    cleanup_cache(Path(str(settings.cache_dir)), max_size_mb=emb.cache_max_size_mb, ttl_days=emb.cache_ttl_days)

    if CLEAR_EXISTING:
        chroma_dir = Path(str(settings.chroma_dir))
        if chroma_dir.exists():
            logger.info(f"Fully clearing ChromaDB directory: {chroma_dir.resolve()}")
            try:
                shutil.rmtree(chroma_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to fully remove database directory: {e}")

    builder = EmbeddingBuilder(
        corpus_dir=str(settings.corpus_dir),
        out_dir=str(settings.analysis_dir),
        text_type=TEXT_TYPE,
        embedding_model=MODEL_NAME,
        chunking=CHUNKING,
        chroma_path=str(settings.chroma_dir),
        cache_dir=str(settings.cache_dir),
        chunked_dir=str(settings.corpus_chunked_dir),
        batch_size=BATCH_SIZE,
        cache_batch_size=emb.cache_batch_size,
        chroma_batch_size=emb.chroma_batch_size,
    )

    models_to_run = models or ([MODEL_NAME] if model_name else emb.models or [MODEL_NAME])

    logger.info("Starting embedding generation...")
    logger.info(f"   Source: {settings.corpus_dir}")
    logger.info(f"   Text type: {builder.text_type}")
    logger.info(f"   Chroma DB: {settings.chroma_dir}")
    logger.info(f"   Results directory: {builder.out_dir}")
    logger.info(f"   Clear collection: {CLEAR_EXISTING}")

    try:
        for model in models_to_run:
            logger.info(f"   Model: {model}")
            logger.info(f"   Model batch size: {BATCH_SIZE}")

            builder.set_model(model)
            logger.info(f"Collection: {collection_name_for_model(model)}")
            builder.save_all_corpus_to_chroma()

    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise
    finally:
        builder.metrics.save()
        builder.close()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()

    logger.info("All embeddings saved to Chroma.")
    logger.info(f"Analysis results will be saved to: {builder.out_dir}")
    logger.info(f"Performance metrics: {builder.out_dir}/performance_metrics.json")

    return builder
