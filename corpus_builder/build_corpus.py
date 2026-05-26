import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .builder import build_corpus


def setup_logging(log_file_path: str = "logs/corpus.log"):

    log_file = Path(log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)


    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)


    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)


    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)


    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)


    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger


def build_and_save_corpus():
    logger = setup_logging()
    logger.info("Starting corpus build...")

    parser = argparse.ArgumentParser(description="Build a text corpus from a URL list with cleanup")
    parser.add_argument(
        "--type",
        type=str,
        choices=["translation", "original", "all"],
        default="all",
        help="Filter by type (translation, original, or all)"
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.type == "all":
        filter_type = {"translation", "original"}
    else:
        filter_type = {args.type}

    try:
        build_corpus(
            filter_type=filter_type,
            force=args.force
        )
        logger.info("Corpus build completed successfully.")
    except Exception as e:
        logger.error(f"Critical corpus build error: {e}")
        raise