"""Shared stores — the level-2 GC backends (:class:`~pipeline.stage.Store`).

A store is the backend several fan-out stages write into; it answers "which artifact ids do
you hold?" so the driver can reap the ones no live stage claims (a dropped model / plot)."""

from __future__ import annotations

import shutil
from pathlib import Path

from embeddings import chroma_manager


class ChromaStore:
    """The Chroma DB: one collection per embeddings variant, named by the variant key."""

    label = "ChromaStore"   # unique level-2-report key (a singleton — only one Chroma)

    def ids(self) -> set[str]:
        return set(chroma_manager.get_available_models())

    def delete(self, id: str) -> None:
        chroma_manager.delete_collection(id)


class FileStore:
    """A directory whose immediate subdirs are the fan-out artifacts (one per model), each
    named by the id that owns it — e.g. ``projections/<model>/``."""

    def __init__(self, root: Path):
        self._root = root

    @property
    def label(self) -> str:
        # keyed by dir so two FileStores never collide in the driver's level-2 report
        return f"FileStore({self._root.name})"

    def ids(self) -> set[str]:
        return {d.name for d in self._root.iterdir() if d.is_dir()} if self._root.exists() else set()

    def delete(self, id: str) -> None:
        shutil.rmtree(self._root / id, ignore_errors=True)
