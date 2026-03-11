from typing import List
from . import logger

catalog_rows: List[list] = []

def add_to_catalog(tid, tradition, lang, ftype, url, availability, word_count, sentence_count, description=""):
    for row in catalog_rows:
        if row[4] == url:
            logger.warning(f"Повторная попытка добавить URL в каталог: {url}. Пропускаем.")
            return
    catalog_rows.append([
        tid, tradition, lang, ftype, url, availability, word_count, sentence_count,
        description
    ])
    status_str = "доступен" if availability else "недоступен"
    logger.info(
        f"{tid}: {status_str} (слова: {word_count}, предложения: {sentence_count})")