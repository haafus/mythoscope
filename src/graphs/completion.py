"""Lightweight helper for graph-output completeness (no heavy deps).

A book is complete only when all three graphs were written; the skip check and
status both rely on this so they agree on what "done" means.
"""

from pathlib import Path

GRAPH_FILES = ("beings.json", "realms.json", "ages.json")


def is_book_complete(book_dir: Path) -> bool:
    return all((book_dir / name).exists() for name in GRAPH_FILES)
