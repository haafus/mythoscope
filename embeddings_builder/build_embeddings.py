import logging

from .builder import EmbeddingBuilder
from .config import DEFAULTS

def build_embeddings(clear_existing: bool = True):
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
    MODEL_NAME = DEFAULTS["embedding_model"]

    builder = EmbeddingBuilder(
        corpus_dir=CORPUS_DIR,
        out_dir=OUT_DIR,
        text_type=DEFAULTS["text_type"],
        embedding_model=MODEL_NAME,
        chunking=DEFAULTS["chunking"],
        chroma_path=CHROMA_PATH,
        cache_dir=CACHE_DIR,
    )

    logging.info("="*60)
    logging.info("Запуск генерации эмбеддингов...")
    logging.info(f"   Источник: {CORPUS_DIR}")
    logging.info(f"   Тип текстов: {builder.text_type}")
    logging.info(f"   Chroma DB: {CHROMA_PATH}")
    logging.info(f"   Модель: {MODEL_NAME}")
    logging.info(f"   Папка результатов: {builder.out_dir}")
    logging.info(f"   Очистка коллекции: {clear_existing}")
    logging.info("="*60)

    builder.save_all_corpus_to_chroma(collection_name="corpus", clear_existing=clear_existing)

    logging.info("="*60)
    logging.info("Все эмбеддинги сохранены в Chroma.")
    logging.info(f"Результаты анализа будут сохранены в: {builder.out_dir}")
    logging.info("="*60)

    return builder

