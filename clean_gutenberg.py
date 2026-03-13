import re
import argparse
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

try:
    from corpus_builder import logger
    from corpus_builder.config import CORPUS_DIR
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    CORPUS_DIR = Path("corpus")

BACKUP_DIR = Path("sources_backup")
CHANGELOG_FILE = BACKUP_DIR / "changelog.txt"


def setup_storage_dirs() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    logger.debug(f"Директория для бэкапов: {BACKUP_DIR.absolute()}")

    if not CHANGELOG_FILE.exists():
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            f.write("=== CHANGELOG: Очистка файлов Project Gutenberg ===\n")
            f.write(f"Создан: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Директория хранения оригиналов: {BACKUP_DIR.absolute()}\n")
            f.write("=" * 60 + "\n\n")
        logger.info(f"Создан файл изменений: {CHANGELOG_FILE}")


def save_original_file(filepath: Path, content: str) -> Path:
    try:
        if CORPUS_DIR in filepath.parents:
            relative_dir = filepath.parent.relative_to(CORPUS_DIR)
            backup_dir = BACKUP_DIR / relative_dir
        else:
            backup_dir = BACKUP_DIR / "external"
    except ValueError:
        backup_dir = BACKUP_DIR / "misc"

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
    backup_path = backup_dir / backup_filename

    backup_path.write_text(content, encoding='utf-8')
    logger.debug(f"Оригинал сохранен: {backup_path}")

    return backup_path


def log_changes(filepath: Path, original_content: str, cleaned_content: str,
                backup_path: Path, changes: Dict[str, any]) -> None:
    with open(CHANGELOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Изменения: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Файл: {filepath.absolute()}\n")
        f.write(f"Оригинал сохранен в: {backup_path.absolute()}\n")
        f.write(f"Относительный путь в бэкапе: {backup_path.relative_to(BACKUP_DIR)}\n")

        orig_lines = len(original_content.splitlines())
        clean_lines = len(cleaned_content.splitlines())
        chars_removed = len(original_content) - len(cleaned_content)

        f.write(f"Статистика:\n")
        f.write(f"  - Исходный размер: {len(original_content)} символов, {orig_lines} строк\n")
        f.write(f"  - Очищенный размер: {len(cleaned_content)} символов, {clean_lines} строк\n")
        f.write(f"  - Удалено: {chars_removed} символов\n")
        f.write(f"  - Удалено в %: {chars_removed/len(original_content)*100:.1f}%\n")

        if changes.get('start_marker'):
            f.write(f"  - Найден маркер начала: {changes['start_marker']}\n")
        if changes.get('end_marker'):
            f.write(f"  - Найден маркер конца: {changes['end_marker']}\n")
        if changes.get('footnotes_removed', 0) > 0:
            f.write(f"  - Удалено сносок: {changes['footnotes_removed']}\n")

        f.write("-" * 40 + "\n")


def get_backup_info() -> Dict:
    info = {
        'backup_dir': BACKUP_DIR,
        'changelog': CHANGELOG_FILE,
        'backup_dir_exists': BACKUP_DIR.exists(),
        'changelog_exists': CHANGELOG_FILE.exists(),
        'backup_files_count': 0,
        'changelog_size': 0,
        'changelog_entries': 0
    }

    if BACKUP_DIR.exists():
        info['backup_files_count'] = len(list(BACKUP_DIR.rglob('*')))
        info['backup_dir_size'] = sum(f.stat().st_size for f in BACKUP_DIR.rglob('*') if f.is_file())

    if CHANGELOG_FILE.exists():
        info['changelog_size'] = CHANGELOG_FILE.stat().st_size
        content = CHANGELOG_FILE.read_text(encoding='utf-8')
        info['changelog_entries'] = content.count("--- Изменения:")

    return info


def show_backup_stats():
    info = get_backup_info()

    print("\n=== Статистика хранения исходников ===")
    print(f"Директория бэкапов: {info['backup_dir'].absolute()}")
    print(f"Файл изменений: {info['changelog'].absolute()}")
    print(f"\nСтатистика:")
    print(f"  - Директория существует: {info['backup_dir_exists']}")
    if info['backup_dir_exists']:
        print(f"  - Файлов в бэкапе: {info['backup_files_count']}")
        print(f"  - Размер бэкапов: {info.get('backup_dir_size', 0) / 1024:.1f} KB")
    print(f"  - Файл изменений существует: {info['changelog_exists']}")
    if info['changelog_exists']:
        print(f"  - Размер changelog.txt: {info['changelog_size']} байт")
        print(f"  - Записей изменений: {info['changelog_entries']}")
    print("=" * 40)


def clean_gutenberg_text(text: str, filename: Optional[str] = None) -> str:
    if not text:
        return text

    original_length = len(text)
    debug_info = filename if filename else "текст"

    changes = {
        'start_marker': None,
        'end_marker': None,
        'footnotes_removed': 0
    }

    start_patterns = [
        (r'\*\*\* START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK[^*]*\*\*\*', "START OF PROJECT GUTENBERG"),
        (r'\*\*\* START OF THIS PROJECT GUTENBERG EBOOK[^*]*\*\*\*', "START OF THIS PROJECT GUTENBERG"),
        (r'\*\*\*THE PROJECT GUTENBERG EBOOK[^*]*\*\*\*', "THE PROJECT GUTENBERG EBOOK"),
        (r'Produced by .*?\n{2,}', "Produced by"),
    ]

    end_patterns = [
        (r'\*\*\* END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK[^*]*\*\*\*', "END OF PROJECT GUTENBERG"),
        (r'\*\*\* END OF THIS PROJECT GUTENBERG EBOOK[^*]*\*\*\*', "END OF THIS PROJECT GUTENBERG"),
        (r'End of (?:the )?Project Gutenberg[^\n]*', "End of Project Gutenberg"),
    ]

    start_pos = 0
    for pattern, description in start_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            start_pos = match.end()
            while start_pos < len(text) and text[start_pos] in '\n\r':
                start_pos += 1
            changes['start_marker'] = description
            logger.debug(f"{debug_info}: Найден маркер начала текста: {description}")
            break

    end_pos = len(text)
    for pattern, description in end_patterns:
        match = re.search(pattern, text[start_pos:], re.IGNORECASE | re.MULTILINE)
        if match:
            end_pos = start_pos + match.start()
            changes['end_marker'] = description
            logger.debug(f"{debug_info}: Найден маркер конца текста: {description}")
            break

    cleaned_text = text[start_pos:end_pos].strip()

    if not cleaned_text:
        logger.warning(f"{debug_info}: Не удалось извлечь текст, возвращаем оригинал")
        return text

    cleaned_text, footnote_count = _remove_gutenberg_footer_notes_with_count(cleaned_text)
    changes['footnotes_removed'] = footnote_count

    cleaned_text = _normalize_gutenberg_whitespace(cleaned_text)
    cleaned_text = _remove_header_metadata(cleaned_text)

    logger.debug(f"{debug_info}: Очистка текста: {original_length} -> {len(cleaned_text)} символов")

    global _last_changes
    _last_changes = changes

    return cleaned_text


def _remove_gutenberg_footer_notes_with_count(text: str) -> tuple[str, int]:
    footnote_count = 0

    footnote_patterns = [
        (r'\n\nFOOTNOTES:\n.*?(?=\n\n\*\*\* END|\Z)', "FOOTNOTES section"),
        (r'\n\n\*\s*FOOTNOTES?\s*\*\n.*?(?=\n\n\*\*\* END|\Z)', "FOOTNOTES with asterisks"),
        (r'\n\n\[?\d+\] .*?(?=\n\n\*\*\* END|\Z)', "numbered footnotes"),
    ]

    for pattern, description in footnote_patterns:
        matches = re.findall(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if matches:
            footnote_count += len(matches)
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
            logger.debug(f"Удалено {len(matches)} сносок типа '{description}'")

    return text, footnote_count


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


def process_gutenberg_file(filepath: Path, backup: bool = False, save_sources: bool = True) -> bool:
    global _last_changes
    _last_changes = {}

    try:
        content = filepath.read_text(encoding='utf-8')

        if not is_gutenberg_text(content):
            logger.info(f"Файл {filepath} не содержит лицензий Gutenberg, пропускаем")
            return False

        cleaned = clean_gutenberg_text(content, str(filepath))

        if cleaned == content:
            logger.info(f"Файл {filepath} не требует изменений")
            return False

        if save_sources:
            setup_storage_dirs()
            backup_path = save_original_file(filepath, content)
            log_changes(filepath, content, cleaned, backup_path, _last_changes)
            logger.info(f"Оригинал сохранен в: {backup_path}")

        if backup:
            backup_path_local = filepath.with_suffix(filepath.suffix + '.bak')
            counter = 1
            while backup_path_local.exists():
                backup_path_local = filepath.with_suffix(filepath.suffix + f'.bak{counter}')
                counter += 1

            filepath.rename(backup_path_local)
            logger.info(f"Создана локальная резервная копия: {backup_path_local}")

        filepath.write_text(cleaned, encoding='utf-8')
        logger.info(f"Файл очищен: {filepath}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {filepath}: {e}")
        return False


def batch_clean_gutenberg_files(directory: Path, pattern: str = "*.txt", backup: bool = False,
                                recursive: bool = True, save_sources: bool = True) -> int:
    if not directory.exists():
        logger.error(f"Директория не найдена: {directory}")
        return 0

    if save_sources:
        setup_storage_dirs()

    count = 0

    if recursive:
        for filepath in directory.rglob(pattern):
            if process_gutenberg_file(filepath, backup, save_sources):
                count += 1
    else:
        for filepath in directory.glob(pattern):
            if process_gutenberg_file(filepath, backup, save_sources):
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


def preview_gutenberg_files(directory: Path, pattern: str = "*.txt", recursive: bool = True) -> List[Path]:
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


def show_changelog():
    if CHANGELOG_FILE.exists():
        print(f"\nСодержимое {CHANGELOG_FILE.absolute()}:")
        print("=" * 60)
        with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"Файл изменений не найден: {CHANGELOG_FILE.absolute()}")


def main():
    parser = argparse.ArgumentParser(description="Очистка корпуса от лицензий Project Gutenberg")
    parser.add_argument("--dir", type=str, default=str(CORPUS_DIR),
                        help="Директория с файлами корпуса")
    parser.add_argument("--pattern", type=str, default="*.txt",
                        help="Паттерн для поиска файлов")
    parser.add_argument("--backup", action="store_true",
                        help="Создавать резервные копии оригиналов (локально)")
    parser.add_argument("--file", type=str, help="Очистить конкретный файл (переопределяет --dir и --pattern)")
    parser.add_argument("--no-recursive", action="store_true",
                        help="Не искать в подпапках (только в указанной директории)")
    parser.add_argument("--preview", action="store_true",
                        help="Показать список файлов для обработки без очистки")
    parser.add_argument("--no-save-sources", action="store_true",
                        help="Не сохранять исходники в папку sources_backup (по умолчанию сохраняются)")
    parser.add_argument("--show-changelog", action="store_true",
                        help="Показать содержимое файла изменений")
    parser.add_argument("--backup-stats", action="store_true",
                        help="Показать статистику по сохраненным бэкапам")

    args = parser.parse_args()

    if args.show_changelog:
        show_changelog()
        return

    if args.backup_stats:
        show_backup_stats()
        return

    save_sources = not args.no_save_sources

    if save_sources:
        logger.info(f"Исходники будут сохраняться в: {BACKUP_DIR.absolute()}")
        logger.info(f"Лог изменений: {CHANGELOG_FILE.absolute()}")

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            logger.error(f"Файл не найден: {filepath}")
            return

        if process_gutenberg_file(filepath, args.backup, save_sources):
            logger.info(f"Файл успешно очищен: {filepath}")
            if save_sources:
                logger.info(f"Оригинал сохранен в папку {BACKUP_DIR}/")
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
            recursive=not args.no_recursive,
            save_sources=save_sources
        )

        logger.info(f"Очистка завершена. Обработано файлов: {count}")

        if save_sources and count > 0:
            logger.info(f"Исходники сохранены в папку: {BACKUP_DIR}/")
            logger.info(f"Лог изменений: {CHANGELOG_FILE}")


_last_changes = {}

if __name__ == "__main__":
    main()