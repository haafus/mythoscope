"""Shared stores — the level-2 GC backends (:class:`~pipeline.stage.Store`).

A store is the backend several fan-out stages write into; it answers "which artifact ids do
you hold?" so the driver can reap the ones no live stage claims (a dropped model / plot)."""

from __future__ import annotations

from embeddings import chroma_manager


class ChromaStore:
    """The Chroma DB: one collection per embeddings variant, named by the variant key."""

    def ids(self) -> set[str]:
        return set(chroma_manager.get_available_models())

    def delete(self, id: str) -> None:
        chroma_manager.delete_collection(id)
