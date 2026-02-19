import argparse
import csv
import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import chardet
import requests
import unicodedata
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DOWNLOAD_LIST_FILE = "download_list.json"
CORPUS_DIR = Path("corpus")
METADATA_FILE = CORPUS_DIR / "corpus_metadata.json"
CATALOG_FILE = CORPUS_DIR / "corpus_catalog.csv"
PROCESSED_URLS_FILE = CORPUS_DIR / "processed_urls.json"

REASON_OPTIONS = {
    "available": "Файл успешно загружен и содержит валидный текст",
    "empty_text": "Текст после обработки оказался пустым",
    "download_failed": "Не удалось загрузить файл по URL",
    "encoding_failed": "Не удалось декодировать содержимое",
    "html_to_text_failed": "HTML не удалось преобразовать в читаемый текст",
    "skipped_exists": "Файл уже существует и не перезаписан (force=False)",
    "skipped_duplicate": "URL дублируется — пропущен",
    "skipped_processed": "URL уже успешно обработан ранее — пропущен",
}


def load_download_list(filter_type: Optional[str] = None) -> List[Dict]:
    with open(DOWNLOAD_LIST_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    if filter_type:
        items = [item for item in items if item["type"] == filter_type]

    processed_urls = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, "r", encoding="utf-8") as f:
            processed_urls = set(json.load(f))
        logger.info(f"Загружено {len(processed_urls)} ранее обработанных URL из {PROCESSED_URLS_FILE}")

    seen_urls = set()
    filtered = []
    for item in items:
        url = item["url"]
        if url in seen_urls:
            logger.warning(f"Дубликат URL: {url}, пропускаем")
            add_to_catalog(
                tid=item["id"],
                tradition=item["tradition"],
                lang=item["language"],
                ftype=item["type"],
                url=url,
                availability=False,
                reason="skipped_duplicate",
                word_count=0,
                sentence_count=0
            )
            continue
        if url in processed_urls:
            logger.info(f"URL уже обработан ранее: {url}, пропускаем")
            add_to_catalog(
                tid=item["id"],
                tradition=item["tradition"],
                lang=item["language"],
                ftype=item["type"],
                url=url,
                availability=True,
                reason="skipped_processed",
                word_count=0,
                sentence_count=0
            )
            continue
        seen_urls.add(url)
        filtered.append(item)
    return filtered


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def download_file(url: str) -> bytes:
    logger.info(f"Загрузка: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.content


def html_to_text(html_content: bytes) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def count_words(text: str) -> int:
    if not text:
        return 0
    return len([word for word in text.split() if word.strip()])


def count_sentences(text: str) -> int:
    if not text:
        return 0
    sentences = re.split(r'[.!?]+\s*', text.strip())
    return len([s for s in sentences if s.strip()])


catalog_rows = []


def add_to_catalog(
        tid: str,
        tradition: str,
        lang: str,
        ftype: str,
        url: str,
        availability: bool,
        reason: str,
        word_count: int,
        sentence_count: int
) -> None:
    if reason not in REASON_OPTIONS:
        logger.warning(f"Неизвестный reason: {reason}, используем 'unknown'")
        reason = "unknown"

    for row in catalog_rows:
        if row[4] == url:
            logger.warning(f"Повторная попытка добавить URL в каталог: {url}. Пропускаем.")
            return

    catalog_rows.append([
        tid, tradition, lang, ftype, url, availability, reason, word_count, sentence_count
    ])

    status_str = "доступен" if availability else "недоступен"
    logger.info(f"{tid}: {status_str} → {REASON_OPTIONS[reason]} (слова: {word_count}, предложения: {sentence_count})")


def build_corpus(filter_type: Optional[str] = None, force: bool = False):
    ensure_dir(CORPUS_DIR)
    global catalog_rows
    catalog_rows = []
    metadata = []

    download_list = load_download_list(filter_type)

    processed_urls = set()
    if PROCESSED_URLS_FILE.exists():
        with open(PROCESSED_URLS_FILE, "r", encoding="utf-8") as f:
            processed_urls = set(json.load(f))

    for item in download_list:
        tid = item["id"]
        tradition = item["tradition"]
        lang = item["language"]
        ftype = item["type"]
        url = item["url"]

        tradition_path = tradition.replace('/', '_').replace(' ', '_')
        folder = CORPUS_DIR / tradition_path / tid
        filename = folder / f"{tid}.txt"

        if filename.exists() and not force:
            logger.info(f"{tid}: Файл уже существует, пропускаем (force=False).")
            existing_data = filename.read_bytes()
            h = md5(existing_data)
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

            add_to_catalog(
                tid=tid,
                tradition=tradition,
                lang=lang,
                ftype=ftype,
                url=url,
                availability=True,
                reason="skipped_exists",
                word_count=word_count,
                sentence_count=sentence_count
            )
            continue

        if url in processed_urls:
            logger.info(f"URL уже успешно обработан ранее: {url}, пропускаем")
            add_to_catalog(
                tid=tid,
                tradition=tradition,
                lang=lang,
                ftype=ftype,
                url=url,
                availability=True,
                reason="skipped_processed",
                word_count=0,
                sentence_count=0
            )
            continue

        try:
            data = download_file(url)

            if b"<html" in data[:150].lower():
                logger.debug(f"{tid}: Обнаружен HTML, преобразуем в текст")
                text = html_to_text(data)
                text = normalize_text(text)
                if not text.strip():
                    logger.warning(f"{tid}: HTML преобразован в пустой текст. Пропуск.")
                    add_to_catalog(
                        tid=tid,
                        tradition=tradition,
                        lang=lang,
                        ftype=ftype,
                        url=url,
                        availability=False,
                        reason="empty_text",
                        word_count=0,
                        sentence_count=0
                    )
                    continue
                data = text.encode("utf-8")
            else:
                detected = chardet.detect(data)
                encoding = detected['encoding'] or 'utf-8'
                if detected['confidence'] < 0.7:
                    logger.warning(
                        f"{tid}: Низкая уверенность в кодировке ({detected['confidence']:.2f}), используем utf-8 с заменой")
                try:
                    text = data.decode(encoding, errors="replace")
                except Exception as decode_err:
                    logger.exception(f"{tid}: Ошибка декодирования: {decode_err}")
                    add_to_catalog(
                        tid=tid,
                        tradition=tradition,
                        lang=lang,
                        ftype=ftype,
                        url=url,
                        availability=False,
                        reason="encoding_failed",
                        word_count=0,
                        sentence_count=0
                    )
                    continue
                text = normalize_text(text)
                data = text.encode("utf-8")

            for old_file in filename.parent.glob(f"{tid}.*"):
                if old_file != filename:
                    logger.info(f"Удаление старого файла: {old_file.name}")
                    try:
                        old_file.unlink()
                    except Exception as e:
                        logger.warning(f"Не удалось удалить {old_file}: {e}")

            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_bytes(data)

            h = md5(data)
            char_count = len(text)
            word_count = count_words(text)
            sentence_count = count_sentences(text)

            metadata.append({
                "id": tid, "tradition": tradition, "language": lang, "type": ftype,
                "url": url, "date_downloaded": datetime.utcnow().isoformat(),
                "md5": h, "path": str(filename.resolve()),
                "char_count": char_count, "word_count": word_count, "sentence_count": sentence_count
            })

            add_to_catalog(
                tid=tid,
                tradition=tradition,
                lang=lang,
                ftype=ftype,
                url=url,
                availability=True,
                reason="available",
                word_count=word_count,
                sentence_count=sentence_count
            )

            logger.info(
                f"Успешно сохранено: {tid}.txt (символов: {char_count}, слов: {word_count}, предложений: {sentence_count})")

            processed_urls.add(url)

        except requests.exceptions.RequestException as e:
            logger.exception(f"{tid}: Ошибка загрузки: {e}")
            add_to_catalog(
                tid=tid,
                tradition=tradition,
                lang=lang,
                ftype=ftype,
                url=url,
                availability=False,
                reason="download_failed",
                word_count=0,
                sentence_count=0
            )
        except Exception as e:
            logger.exception(f"{tid}: Неизвестная ошибка при обработке: {e}")
            add_to_catalog(
                tid=tid,
                tradition=tradition,
                lang=lang,
                ftype=ftype,
                url=url,
                availability=False,
                reason="unknown",
                word_count=0,
                sentence_count=0
            )
            continue

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "tradition", "language", "type", "url", "availability", "reason", "word_count", "sentence_count"
        ])
        writer.writerows(catalog_rows)

    with open(PROCESSED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed_urls), f, ensure_ascii=False, indent=2)

    logger.info("Сборка корпуса завершена.")
    logger.info(f"Всего записей в каталоге: {len(catalog_rows)}")
    logger.info(f"Доступных: {sum(1 for row in catalog_rows if row[5])}")
    logger.info(f"Недоступных: {len(catalog_rows) - sum(1 for row in catalog_rows if row[5])}")

    reason_counts = {}
    total_words = 0
    total_sentences = 0
    for row in catalog_rows:
        reason = row[6]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if row[5]:
            total_words += row[7]
            total_sentences += row[8]

    logger.info("\nСтатистика по причинам недоступности:")
    for reason, count in sorted(reason_counts.items()):
        if reason != "available":
            desc = REASON_OPTIONS.get(reason, "Неизвестно")
            logger.info(f"  {reason:<20}: {count} ({desc})")

    logger.info(f"\nОбщая статистика по доступным текстам:")
    logger.info(f"  Всего слов: {total_words}")
    logger.info(f"  Всего предложений: {total_sentences}")
    if len([r for r in catalog_rows if r[5]]) > 0:
        avg_words = total_words / len([r for r in catalog_rows if r[5]])
        avg_sentences = total_sentences / len([r for r in catalog_rows if r[5]])
        logger.info(f"  Среднее слов на текст: {avg_words:.1f}")
        logger.info(f"  Среднее предложений на текст: {avg_sentences:.1f}")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def build_and_save_corpus():
    parser = argparse.ArgumentParser(description="Сбор корпуса текстов из списка URL")
    parser.add_argument("--type", type=str, help="Фильтровать по типу (sutra, commentary и т.д.)")
    parser.add_argument("--force", action="store_true", help="Перезаписать существующие файлы")
    args = parser.parse_args()
    build_corpus(filter_type=args.type, force=args.force)