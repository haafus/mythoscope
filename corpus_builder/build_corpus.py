import argparse

from .builder import build_corpus


def build_and_save_corpus():
    parser = argparse.ArgumentParser(description="Сбор корпуса текстов из списка URL с очисткой")
    parser.add_argument("--type", type=str, help="Фильтровать по типу (sutra, commentary и т.д.)")
    parser.add_argument("--force", action="store_true", help="Перезаписать существующие файлы")
    args = parser.parse_args()

    build_corpus(
        filter_type=args.type,
        force=args.force
    )