import re
import argparse
from pathlib import Path
from typing import Optional

try:
    from corpus_builder import logger
    from corpus_builder.config import CORPUS_DIR
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    CORPUS_DIR = Path("corpus")


def clean_gutenberg_text(text: str, filename: Optional[str] = None) -> str:
    if not text:
        return text

    original_length = len(text)
    debug_info = filename if filename else "текст"

    start_patterns = [
        r'\*\*\* START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK[^*]*\*\*\*',
        r'\*\*\* START OF THIS PROJECT GUTENBERG EBOOK[^*]*\*\*\*',
        r'\*\*\*THE PROJECT GUTENBERG EBOOK[^*]*\*\*\*',
        r'Produced by .*?\n{2,}',
    ]

    end_patterns = [
        r'\*\*\* END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK[^*]*\*\*\*',
        r'\*\*\* END OF THIS PROJECT GUTENBERG EBOOK[^*]*\*\*\*',
        r'End of (?:the )?Project Gutenberg[^\n]*',
    ]

    start_pos = 0
    for pattern in start_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            start_pos = match.end()
            while start_pos < len(text) and text[start_pos] in '\n\r':
                start_pos += 1
            logger.debug(f"{debug_info}: Найден маркер начала текста")
            break

    end_pos = len(text)
    for pattern in end_patterns:
        match = re.search(pattern, text[start_pos:], re.IGNORECASE | re.MULTILINE)
        if match:
            end_pos = start_pos + match.start()
            logger.debug(f"{debug_info}: Найден маркер конца текста")
            break

    cleaned_text = text[start_pos:end_pos].strip()

    if not cleaned_text:
        logger.warning(f"{debug_info}: Не удалось извлечь текст, возвращаем оригинал")
        return text

    cleaned_text = _remove_gutenberg_footer_notes(cleaned_text)
    cleaned_text = _normalize_gutenberg_whitespace(cleaned_text)
    cleaned_text = _remove_header_metadata(cleaned_text)

    logger.debug(f"{debug_info}: Очистка текста: {original_length} -> {len(cleaned_text)} символов")
    return cleaned_text


def _remove_gutenberg_footer_notes(text: str) -> str:
    footnote_patterns = [
        r'\n\nFOOTNOTES:\n.*?(?=\n\n\*\*\* END|\Z)',
        r'\n\n\*\s*FOOTNOTES?\s*\*\n.*?(?=\n\n\*\*\* END|\Z)',
        r'\n\n\[?\d+\] .*?(?=\n\n\*\*\* END|\Z)',
    ]

    for pattern in footnote_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    return text


def _normalize_gutenberg_whitespace(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^[\s*_\-=]{10,}$', line):
            continue
        cleaned_lines.append(line.rstrip())

    return '\n'.join(cleaned_lines).strip()


def _remove_header_metadata(text: str) -> str:
    lines = text.split('\n')

    metadata_patterns = [
        r'^Translated by ',
        r'^Edited by ',
        r'^With an Introduction by ',
        r'^A Prolegomenon by ',
        r'^Preface by ',
        r'^\[Transcriber['' ]s Note:',
    ]

    for i, line in enumerate(lines[:20]):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        is_metadata = False
        for pattern in metadata_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                is_metadata = True
                break

        if re.match(r'^©|^Copyright|^\[\d{4}\]|^\d{4}\.', line_stripped, re.IGNORECASE):
            is_metadata = True

        if not is_metadata:
            return '\n'.join(lines[i:])

    return text


def is_gutenberg_text(text: str) -> bool:
    patterns = [
        r'Project Gutenberg',
        r'www\.gutenberg\.org',
        r'\*\*\* START OF (?:THE |THIS )?PROJECT GUTENBERG',
        r'End of (?:the )?Project Gutenberg',
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def process_gutenberg_file(filepath: Path, backup: bool = False) -> bool:
    try:
        content = filepath.read_text(encoding='utf-8')

        if not is_gutenberg_text(content):
            logger.info(f"Файл {filepath} не содержит лицензий Gutenberg, пропускаем")
            return False

        cleaned = clean_gutenberg_text(content, str(filepath))

        if cleaned == content:
            logger.info(f"Файл {filepath} не требует изменений")
            return False

        if backup:
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            counter = 1
            while backup_path.exists():
                backup_path = filepath.with_suffix(filepath.suffix + f'.bak{counter}')
                counter += 1

            filepath.rename(backup_path)
            logger.info(f"Создана резервная копия: {backup_path}")

        filepath.write_text(cleaned, encoding='utf-8')
        logger.info(f"Файл очищен: {filepath}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {filepath}: {e}")
        return False


def batch_clean_gutenberg_files(directory: Path, pattern: str = "*.txt", backup: bool = False, recursive: bool = True) -> int:
    if not directory.exists():
        logger.error(f"Директория не найдена: {directory}")
        return 0

    count = 0

    if recursive:
        for filepath in directory.rglob(pattern):
            if process_gutenberg_file(filepath, backup):
                count += 1
    else:
        for filepath in directory.glob(pattern):
            if process_gutenberg_file(filepath, backup):
                count += 1

    return count


def clean_gutenberg_in_builder(original_text: str, url: str = "", tid: str = "") -> str:
    if not original_text:
        return original_text

    if url and ('gutenberg.org' in url or 'gutenberg' in url.lower()):
        logger.debug(f"{tid}: Обнаружен URL Project Gutenberg, применяем очистку")
        return clean_gutenberg_text(original_text, tid or url)

    if is_gutenberg_text(original_text):
        logger.debug(f"{tid}: Обнаружен текст Project Gutenberg, применяем очистку")
        return clean_gutenberg_text(original_text, tid or "неизвестный файл")

    return original_text


def preview_gutenberg_files(directory: Path, pattern: str = "*.txt", recursive: bool = True) -> list:
    if not directory.exists():
        return []

    gutenberg_files = []

    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))

    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')[:1000]
            if is_gutenberg_text(content):
                gutenberg_files.append(filepath)
        except Exception as e:
            logger.debug(f"Не удалось прочитать {filepath}: {e}")

    return gutenberg_files


def main():
    parser = argparse.ArgumentParser(description="Очистка корпуса от лицензий Project Gutenberg")
    parser.add_argument("--dir", type=str, default=str(CORPUS_DIR),
                        help="Директория с файлами корпуса")
    parser.add_argument("--pattern", type=str, default="*.txt",
                        help="Паттерн для поиска файлов")
    parser.add_argument("--backup", action="store_true",
                        help="Создавать резервные копии оригиналов")
    parser.add_argument("--file", type=str, help="Очистить конкретный файл (переопределяет --dir и --pattern)")
    parser.add_argument("--no-recursive", action="store_true",
                        help="Не искать в подпапках (только в указанной директории)")
    parser.add_argument("--preview", action="store_true",
                        help="Показать список файлов для обработки без очистки")

    args = parser.parse_args()

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error(f"Файл не найден: {filepath}")
            return

        if process_gutenberg_file(filepath, args.backup):
            logger.info(f"Файл успешно очищен: {filepath}")
        else:
            logger.info(f"Файл не требует очистки: {filepath}")

    elif args.preview:
        directory = Path(args.dir)
        files = preview_gutenberg_files(directory, args.pattern, not args.no_recursive)

        if files:
            print(f"\nНайдено файлов Project Gutenberg: {len(files)}")
            print("Список файлов:")
            for f in files:
                print(f"  - {f}")
        else:
            print("Файлы Project Gutenberg не найдены")

    else:
        directory = Path(args.dir)

        if not directory.exists():
            logger.error(f"Директория не найдена: {directory}")
            logger.info("Убедитесь, что директория существует или укажите правильный путь через --dir")
            return

        count = batch_clean_gutenberg_files(
            directory,
            args.pattern,
            args.backup,
            recursive=not args.no_recursive
        )
        logger.info(f"Очистка завершена. Обработано файлов: {count}")


if __name__ == "__main__":
    main()