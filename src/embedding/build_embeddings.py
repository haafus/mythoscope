import gc
import logging
import shutil
import signal
import sys
from pathlib import Path

import torch

from settings import setup_logging as _setup_logging

from .builder import EmbeddingBuilder, normalize_text_type
from .chroma_manager import collection_name_for_model
from .config_manager import ConfigManager


class ApplicationContext:
    def __init__(self):
        self.builder = None

    def signal_handler(self, signum, frame):
        logger = logging.getLogger(__name__)
        logger.info("Interrupt signal received, saving metrics and cleaning resources...")

        if self.builder is not None:
            try:
                self.builder.metrics.save()
                logger.info("Metrics saved")

                self.builder.close()

                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    torch.mps.empty_cache()

            except Exception as e:
                logger.error(f"Cleanup error: {e}")

        logger.info("Shutting down...")
        sys.exit(0)


app_context = ApplicationContext()
signal.signal(signal.SIGINT, app_context.signal_handler)
signal.signal(signal.SIGTERM, app_context.signal_handler)


def setup_logging(config_path: str = "config/embedding.yaml"):
    config_mgr = ConfigManager(config_path)
    log_config = config_mgr.get("logging")
    _setup_logging(
        log_filename=Path(log_config.get("file", "logs/embedding.log")).name,
        level=log_config.get("level"),
        max_bytes=log_config.get("max_bytes", 10485760),
        backup_count=log_config.get("backup_count", 5),
    )
    return logging.getLogger(__name__)


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

    logger = setup_logging(config_path)

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

    if CLEAR_EXISTING:
        chroma_dir = Path(CHROMA_PATH)
        if chroma_dir.exists():
            logger.info(f"Fully clearing ChromaDB directory: {chroma_dir.resolve()}")
            try:
                shutil.rmtree(chroma_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to fully remove database directory: {e}")

    app_context.builder = EmbeddingBuilder(
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
    logger.info(f"   Text type: {app_context.builder.text_type}")
    logger.info(f"   Chroma DB: {CHROMA_PATH}")
    logger.info(f"   Results directory: {app_context.builder.out_dir}")
    logger.info(f"   Clear collection: {CLEAR_EXISTING}")

    try:
        for model in models_to_run:
            logger.info(f"   Model: {model}")
            logger.info(f"   Model batch size: {BATCH_SIZE}")

            app_context.builder.set_model(model)

            collection_to_write = collection_name_for_model(model)

            logger.info(f"Collection: {collection_to_write}")

            app_context.builder.save_all_corpus_to_chroma()

    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise
    finally:
        app_context.builder.metrics.save()
        app_context.builder.close()

    logger.info("All embeddings saved to Chroma.")
    logger.info(f"Analysis results will be saved to: {app_context.builder.out_dir}")
    logger.info(f"Performance metrics: {app_context.builder.out_dir}/performance_metrics.json")

    return app_context.builder
