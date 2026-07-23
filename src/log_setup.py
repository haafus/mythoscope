import logging
import os
from datetime import datetime
from pathlib import Path

from settings import settings

logger = logging.getLogger(__name__)

# Per-run files are named app-<sortable-timestamp>-<pid>.log so the glob below
# matches only our own logs and lexicographic order equals chronological order.
_LOG_GLOB = "app-*.log"


def setup_logging() -> None:
    log_dir = settings.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # PID disambiguates two runs that start within the same second.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_dir / f"app-{stamp}-{os.getpid()}.log"

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # httpx/httpcore emit one INFO line per HTTP request, so a 429 logs twice — their
    # request line plus our own WARNING in llm.client. Quiet them to WARNING so each 429 is
    # a single message (and successful calls stop logging a line each). Kept verbose at DEBUG,
    # where the raw request/response lines are actually wanted.
    if level > logging.DEBUG:
        for noisy in ("httpx", "httpcore"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    _prune_old_logs(log_dir, settings.logs_max_files)


def _prune_old_logs(log_dir: Path, keep: int) -> None:
    """Delete all but the ``keep`` newest per-run logs. Runs at startup so a run
    that crashed without cleaning up is still bounded; never raises."""
    if keep <= 0:
        return
    try:
        existing = sorted(log_dir.glob(_LOG_GLOB))  # chronological by filename
        for old in existing[:-keep]:
            old.unlink(missing_ok=True)  # idempotent if a concurrent run beat us to it
    except Exception as exc:
        logger.debug("log prune failed: %s", exc)
