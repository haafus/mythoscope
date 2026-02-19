import logging

from .builder import EmbeddingBuilder
from .config import DEFAULTS


def build_embeddings():
    """
    Точка входа для скрипта. Запускает обработку всего корпуса.
    """
    # Настройка логгирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("embedding.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    CORPUS_DIR = DEFAULTS["corpus_dir"]
    OUT_DIR = DEFAULTS["out_dir"]
    CHROMA_PATH = DEFAULTS["chroma_path"]
    CACHE_DIR = DEFAULTS["cache_dir"]

    builder = EmbeddingBuilder(
        corpus_dir=CORPUS_DIR,
        out_dir=OUT_DIR,
        text_type=DEFAULTS["text_type"],
        embedding_model=DEFAULTS["embedding_model"],
        chunking=DEFAULTS["chunking"],
        chroma_path=CHROMA_PATH,
        cache_dir=CACHE_DIR,
    )

    logging.info("Запуск генерации эмбеддингов...")
    logging.info(f"   Источник: {CORPUS_DIR}")
    logging.info(f"   Тип текстов: {builder.text_type}")
    logging.info(f"   Chroma DB: {CHROMA_PATH}")

    builder.save_all_corpus_to_chroma(collection_name="corpus")

    logging.info("Все эмбеддинги сохранены в Chroma.")
