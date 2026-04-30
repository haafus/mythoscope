import logging
import signal
import sys
import gc
import torch
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .builder import EmbeddingBuilder
from .config_manager import ConfigManager

# Глобальная переменная для graceful shutdown
_builder = None


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger = logging.getLogger(__name__)
    logger.info("Получен сигнал прерывания, сохраняем метрики и очищаем ресурсы...")

    if _builder is not None:
        try:
            _builder.metrics.save()
            logger.info("Метрики сохранены")

            # Очистка GPU памяти
            if hasattr(_builder, 'unload_model'):
                _builder.unload_model()

            # Принудительная сборка мусора
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            logger.error(f"Ошибка при очистке: {e}")

    logger.info("Завершение работы...")
    sys.exit(0)


# Регистрация обработчиков сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def setup_logging(config_path: str = "config.yaml"):
    """Setup logging with rotation based on config"""
    config_mgr = ConfigManager(config_path)

    log_config = config_mgr.get("logging")
    log_file = Path(log_config.get("file", "logs/embedding.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),
        backupCount=log_config.get("backup_count", 5),
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_config.get("level", "INFO")))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def build_embeddings(clear_existing: bool = True, batch_size: int = 32, config_path: str = "config.yaml"):
    """Generate embeddings for all files in corpus directory"""
    global _builder

    # Setup logging
    logger = setup_logging(config_path)

    # Load configuration
    config_mgr = ConfigManager(config_path)

    CORPUS_DIR = config_mgr.get("paths.corpus_dir")
    OUT_DIR = config_mgr.get("paths.out_dir")
    CHROMA_PATH = config_mgr.get("paths.chroma_path")
    CACHE_DIR = config_mgr.get("paths.cache_dir")
    MODEL_NAME = config_mgr.get("embedding.default_model")
    TEXT_TYPE = config_mgr.get("embedding.text_type")
    CHUNKING = config_mgr.get("embedding.default_chunking")

    _builder = EmbeddingBuilder(
        corpus_dir=CORPUS_DIR,
        out_dir=OUT_DIR,
        text_type=TEXT_TYPE,
        embedding_model=MODEL_NAME,
        chunking=CHUNKING,
        chroma_path=CHROMA_PATH,
        cache_dir=CACHE_DIR,
        batch_size=batch_size,
    )

    logger.info("=" * 60)
    logger.info("Запуск генерации эмбеддингов...")
    logger.info(f"   Источник: {CORPUS_DIR}")
    logger.info(f"   Тип текстов: {_builder.text_type}")
    logger.info(f"   Chroma DB: {CHROMA_PATH}")
    logger.info(f"   Модель: {MODEL_NAME}")
    logger.info(f"   Папка результатов: {_builder.out_dir}")
    logger.info(f"   Очистка коллекции: {clear_existing}")
    logger.info(f"   Размер батча: {batch_size}")
    logger.info("=" * 60)

    try:
        _builder.save_all_corpus_to_chroma(collection_name="corpus", clear_existing=clear_existing)
    except Exception as e:
        logger.error(f"Ошибка при генерации эмбеддингов: {e}")
        _builder.metrics.save()
        raise
    finally:
        # Ensure metrics are saved even on error
        _builder.metrics.save()

    logger.info("=" * 60)
    logger.info("Все эмбеддинги сохранены в Chroma.")
    logger.info(f"Результаты анализа будут сохранены в: {_builder.out_dir}")
    logger.info(f"Метрики производительности: {_builder.out_dir}/performance_metrics.json")
    logger.info("=" * 60)

    return _builder