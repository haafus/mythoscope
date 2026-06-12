import gc
import logging
import shutil
from pathlib import Path

import torch

from .builder import EmbeddingBuilder, normalize_text_type
from .cache_utils import cleanup_cache
from .chroma_manager import collection_name_for_model
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


def build_embeddings(
    clear_existing: bool | None = None,
    batch_size: int | None = None,
    config_path: str = "config/embedding.yaml",
    model_name: str | None = None,
    models: list | None = None,
    chunking: str | None = None,
    text_type: str | None = None,
):
    if clear_existing is False:
        raise ValueError("Incremental Chroma writes are not supported for full embedding generation.")

    config_mgr = ConfigManager(config_path)

    CORPUS_DIR = config_mgr.get("paths.corpus_dir")
    OUT_DIR = config_mgr.get("paths.out_dir")
    CHROMA_PATH = config_mgr.get("paths.chroma_path")
    CACHE_DIR = config_mgr.get("paths.cache_dir")
    CHUNKED_DIR = config_mgr.get("paths.chunked_dir", "outputs/corpus_chunked")
    MODEL_NAME = model_name or config_mgr.get("embedding.default_model")
    TEXT_TYPE: str = normalize_text_type(text_type or config_mgr.get("embedding.text_type")) or "all"
    CHUNKING = chunking or config_mgr.get("embedding.default_chunking")
    CACHE_BATCH = config_mgr.get("embedding.cache_batch_size", 50)
    CHROMA_BATCH = config_mgr.get("embedding.chroma_batch_size", 100)
    BATCH_SIZE = batch_size if batch_size is not None else config_mgr.get("embedding.batch_size")
    CLEAR_EXISTING = clear_existing if clear_existing is not None else True

    cleanup_cache(
        Path(CACHE_DIR),
        max_size_mb=config_mgr.get("cache.max_size_mb", 1024),
        ttl_days=config_mgr.get("cache.ttl_days", 30),
    )

    if CLEAR_EXISTING:
        chroma_dir = Path(CHROMA_PATH)
        if chroma_dir.exists():
            logger.info(f"Fully clearing ChromaDB directory: {chroma_dir.resolve()}")
            try:
                shutil.rmtree(chroma_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to fully remove database directory: {e}")

    builder = EmbeddingBuilder(
        corpus_dir=CORPUS_DIR,
        out_dir=OUT_DIR,
        text_type=TEXT_TYPE,
        embedding_model=MODEL_NAME,
        chunking=CHUNKING,
        chroma_path=CHROMA_PATH,
        cache_dir=CACHE_DIR,
        chunked_dir=CHUNKED_DIR,
        batch_size=BATCH_SIZE,
        cache_batch_size=CACHE_BATCH,
        chroma_batch_size=CHROMA_BATCH,
    )

    models_to_run = models or ([MODEL_NAME] if model_name else config_mgr.get("embedding.models", [MODEL_NAME]))

    logger.info("Starting embedding generation...")
    logger.info(f"   Source: {CORPUS_DIR}")
    logger.info(f"   Text type: {builder.text_type}")
    logger.info(f"   Chroma DB: {CHROMA_PATH}")
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
