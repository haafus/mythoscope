import argparse
import logging

from settings import setup_logging

from .builder import build_corpus


def build_and_save_corpus():
    setup_logging(log_filename="corpus.log", clear_handlers=True)
    logger = logging.getLogger(__name__)
    logger.info("Starting corpus build...")

    parser = argparse.ArgumentParser(description="Build a text corpus from a URL list with cleanup")
    parser.add_argument(
        "--type",
        type=str,
        choices=["translation", "original", "all"],
        default="all",
        help="Filter by type (translation, original, or all)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.type == "all":
        filter_type = {"translation", "original"}
    else:
        filter_type = {args.type}

    try:
        build_corpus(filter_type=filter_type, force=args.force)
        logger.info("Corpus build completed successfully.")
    except Exception as e:
        logger.error(f"Critical corpus build error: {e}")
        raise
