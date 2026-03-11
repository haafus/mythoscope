import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
import chardet
import PyPDF2
from io import BytesIO
from .config import CORPUS_DIR, METADATA_FILE, CATALOG_FILE, PROCESSED_URLS_FILE
from .downloader import load_download_list, download_file
from .utils import md5, html_to_text, pdf_to_text, normalize_text, count_words, count_sentences, ensure_dir
from . import catalog
from . import logger

def process_local_file(filename: Path, item: Dict, metadata: List[Dict], processed_urls: Set[str]) -> bool:
    tid = item["id"]
    tradition = item["tradition"]
    lang = item["language"]
    ftype = item["type"]
    url = item["url"]
    try:
        logger.info(f"{tid}: Обработка существующего файла {filename}")
        existing_data = filename.read_bytes()
        h = md5(existing_data)
        if filename.suffix.lower() == '.pdf':
            text = pdf_to_text(existing_data)
        else:
            text = existing_data.decode("utf-8", errors="replace")
        text = normalize_text(text)
        char_count = len(text)
        word_count = count_words(text)
        sentence_count = count_sentences(text)
        metadata.append({
            "id": tid, "tradition": tradition, "language": lang, "type": ftype,
            "url": url, "date_downloaded": datetime.utcnow().isoformat(),
            "md5": h, "path": str(filename.resolve()),
            "char_count": char_count, "word_count": word_count, "sentence_count": sentence_count
        })
        catalog.add_to_catalog(tid, tradition, lang, ftype, url, True, word_count, sentence_count, "")
        processed_urls.add(url)
        return True
    except Exception as e:
        logger.exception(f"{tid}: Ошибка обработки локального файла {filename}: {e}")
        catalog.add_to_catalog(tid, tradition, lang, ftype, url, False, 0, 0, f"Ошибка чтения файла: {e}")
        return False


def build_corpus(filter_type: Optional[str] = None, force: bool = False):
    ensure_dir(CORPUS_DIR)
    catalog.catalog_rows = []
    metadata = []
    download_list = load_download_list(filter_type, force)
    processed_urls: Set[str] = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, "r", encoding="utf-8") as f:
            processed_urls = set(json.load(f))

    for item in download_list:
        tid = item["id"]
        tradition = item["tradition"]
        lang = item["language"]
        ftype = item["type"]
        url = item["url"]

        if '_local_file' in item and not force:
            filename = Path(item['_local_file'])
            if filename.exists():
                process_local_file(filename, item, metadata, processed_urls)
                continue
            else:
                logger.warning(f"{tid}: Локальный файл {filename} не найден, пробуем скачать")
                del item['_local_file']

        try:
            data = download_file(url)
            content_type = item.get('content_type', '')
            text = ""

            is_pdf = url.lower().endswith('.pdf') or 'application/pdf' in content_type
            is_html = b"<html" in data[:200].lower() or 'text/html' in content_type

            try:
                if is_pdf:
                    logger.debug(f"{tid}: Обнаружен PDF, извлекаем текст")
                    text = pdf_to_text(data)
                elif is_html:
                    logger.debug(f"{tid}: Обнаружен HTML, преобразуем в текст")
                    text = html_to_text(data)
                else:
                    detected = chardet.detect(data)
                    encoding = detected['encoding'] or 'utf-8'

                    if detected['confidence'] < 0.7:
                        logger.warning(
                            f"{tid}: Низкая уверенность в кодировке ({detected['confidence']:.2f}), пробуем несколько вариантов")

                        encodings_to_try = [encoding, 'utf-8', 'windows-1251', 'koi8-r', 'iso-8859-1']
                        for enc in encodings_to_try:
                            try:
                                text = data.decode(enc, errors="replace")
                                logger.info(f"{tid}: Успешно декодировано с {enc}")
                                break
                            except:
                                continue
                    else:
                        text = data.decode(encoding, errors="replace")

            except Exception as e:
                logger.error(f"{tid}: Ошибка преобразования контента: {e}")
                catalog.add_to_catalog(tid, tradition, lang, ftype, url, False, 0, 0, str(e))
                continue

            if not text or not text.strip():
                logger.warning(f"{tid}: Контент пуст после преобразования")
                catalog.add_to_catalog(tid, tradition, lang, ftype, url, False, 0, 0, "Пустой контент")
                continue

            text = normalize_text(text)

            data_utf8 = text.encode("utf-8")

            tradition_path = tradition.replace('/', '_').replace(' ', '_')
            folder = CORPUS_DIR / tradition_path / tid
            filename = folder / f"{tid}.txt"

            for old_file in filename.parent.glob(f"{tid}.*"):
                if old_file != filename:
                    logger.info(f"Удаление старого файла: {old_file.name}")
                    try:
                        old_file.unlink()
                    except Exception as e:
                        logger.warning(f"Не удалось удалить {old_file}: {e}")

            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_bytes(data_utf8)

            h = md5(data_utf8)
            char_count = len(text)
            word_count = count_words(text)
            sentence_count = count_sentences(text)

            metadata.append({
                "id": tid, "tradition": tradition, "language": lang, "type": ftype,
                "url": url, "date_downloaded": datetime.utcnow().isoformat(),
                "md5": h, "path": str(filename.resolve()),
                "char_count": char_count, "word_count": word_count, "sentence_count": sentence_count
            })

            catalog.add_to_catalog(tid, tradition, lang, ftype, url, True, word_count, sentence_count, "")

            logger.info(
                f"Успешно сохранено: {tid}.txt (символов: {char_count}, слов: {word_count}, предложений: {sentence_count})")

            processed_urls.add(url)

        except Exception as e:
            logger.exception(f"{tid}: Неизвестная ошибка при обработке: {e}")
            catalog.add_to_catalog(tid, tradition, lang, ftype, url, False, 0, 0, str(e))
            continue

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "tradition", "language", "type", "url", "availability",
            "word_count", "sentence_count", "description"
        ])
        writer.writerows(catalog.catalog_rows)

    with open(PROCESSED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_urls), f, ensure_ascii=False, indent=2)

    logger.info("Сборка корпуса завершена.")
    logger.info(f"Всего записей в каталоге: {len(catalog.catalog_rows)}")
    logger.info(f"Доступных: {sum(1 for row in catalog.catalog_rows if row[5])}")
    logger.info(f"Недоступных: {len(catalog.catalog_rows) - sum(1 for row in catalog.catalog_rows if row[5])}")
    total_words = 0
    total_sentences = 0
    for row in catalog.catalog_rows:
        if row[5]:
            total_words += row[6]
            total_sentences += row[7]
    logger.info(f"\nОбщая статистика по доступным текстам:")
    logger.info(f"  Всего слов: {total_words}")
    logger.info(f"  Всего предложений: {total_sentences}")
    if len([r for r in catalog.catalog_rows if r[5]]) > 0:
        avg_words = total_words / len([r for r in catalog.catalog_rows if r[5]])
        avg_sentences = total_sentences / len([r for r in catalog.catalog_rows if r[5]])
        logger.info(f"  Среднее слов на текст: {avg_words:.1f}")
        logger.info(f"  Среднее предложений на текст: {avg_sentences:.1f}")