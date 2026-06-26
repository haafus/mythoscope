import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar

from .rate_limiter import DailyLimitReached

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


def map_concurrent(
    items: Iterable[T],
    fn: Callable[[T], R],
    concurrency: int,
    on_result: Callable[[T, R], None] | None = None,
) -> bool:
    """Run ``fn(item)`` over ``items`` with bounded concurrency.

    ``on_result(item, result)`` is invoked in the calling thread as each task
    finishes, so callers can persist results (e.g. append to a cache) without
    locking. Returns True if every item completed, or False if the run stopped
    early because ``fn`` raised :class:`DailyLimitReached`. Any other exception
    (including KeyboardInterrupt) propagates to the caller.

    On any early exit, not-yet-started work is cancelled and we don't block on
    the queue, so Ctrl+C / errors stop promptly (in-flight calls still finish —
    threads can't be killed).
    """
    items = list(items)
    if not items:
        return True

    completed = True
    pool = ThreadPoolExecutor(max_workers=max(1, concurrency))
    try:
        futures = {pool.submit(fn, item): item for item in items}
        for fut in as_completed(futures):
            try:
                result = fut.result()
            except DailyLimitReached:
                completed = False
                break
            if on_result is not None:
                on_result(futures[fut], result)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return completed
