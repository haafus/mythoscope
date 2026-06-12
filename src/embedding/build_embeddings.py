from __future__ import annotations

import gc
import logging
import shutil
from pathlib import Path

import torch

from .builder import EmbeddingBuilder, normalize_text_type
from .cache_utils import cleanup_cache
from .chroma_manager import collection_name_for_model
from .config_manager import EmbeddingConfig, load_embedding_config

logger = logging.getLogger(__name__)


def build_embeddings(
    clear_existing: bool | None = None,
    batch_size: int | None = None,
    config: EmbeddingConfig | None = None,
    config_path: str | None = None,
    model_name: str | None = None,
    models: list | None = None,
    chunking: str | None = None,
    text_type: str | None = None,
):
    if clear_existing is False:
        raise ValueError("Incremental Chroma writes are not supported for full embedding generation.")

    cfg = config or load_embedding_config(config_path)

    MODEL_NAME = model_name or cfg.default_model
    TEXT_TYPE: str = normalize_text_type(text_type or cfg.text_type) or "all"
    CHUNKING = chunking or cfg.default_chunking
    BATCH_SIZE = batch_size if batch_size is not None else cfg.batch_size
    CLEAR_EXISTING = clear_existing if clear_existing is not None else True

    cleanup_cache(Path(cfg.cache_dir), max_size_mb=cfg.max_size_mb, ttl_days=cfg.ttl_days)

    if CLEAR_EXISTING:
        chroma_dir = Path(cfg.chroma_path)
        if chroma_dir.exists():
            logger.info(f"Fully clearing ChromaDB directory: {chroma_dir.resolve()}")
            try:
                shutil.rmtree(chroma_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to fully remove database directory: {e}")

    builder = EmbeddingBuilder(
        corpus_dir=cfg.corpus_dir,
        out_dir=cfg.out_dir,
        text_type=TEXT_TYPE,
        embedding_model=MODEL_NAME,
        chunking=CHUNKING,
        chroma_path=cfg.chroma_path,
        cache_dir=cfg.cache_dir,
        chunked_dir=cfg.chunked_dir,
        batch_size=BATCH_SIZE,
        cache_batch_size=cfg.cache_batch_size,
        chroma_batch_size=cfg.chroma_batch_size,
    )

    models_to_run = models or ([MODEL_NAME] if model_name else cfg.models or [MODEL_NAME])

    logger.info("Starting embedding generation...")
    logger.info(f"   Source: {cfg.corpus_dir}")
    logger.info(f"   Text type: {builder.text_type}")
    logger.info(f"   Chroma DB: {cfg.chroma_path}")
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
