import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from settings import settings


def setup_logging(
    log_filename: str = "app.log",
    log_dir: Path | str | None = None,
    level: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    clear_handlers: bool = False,
) -> None:
    log_path = Path(log_dir or settings.logs_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    requested = getattr(logging, (level or settings.log_level).upper(), logging.INFO)
    root_logger = logging.getLogger()

    if clear_handlers:
        root_logger.handlers.clear()

    current = root_logger.level
    log_level = min(requested, current) if current != logging.NOTSET else requested
    root_logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    log_file = str((log_path / log_filename).resolve())
    if not any(
        isinstance(h, RotatingFileHandler) and str(h.baseFilename) == log_file for h in root_logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
