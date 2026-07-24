"""The embeddings stage — one per variant in ``models.json``. Key = ``document_id``.

fp-native already: every chunk's Chroma metadata carries ``fingerprint =
chunk_fingerprint(doc_fingerprint, transform_version)`` (all of a doc's chunks share it), so
``actual()`` reads it back and ``desired()`` recomputes it by folding the corpus stage's
output fingerprint. The whole variant is one collection → one ``ChromaStore`` id for L2 GC.
"""

from __future__ import annotations

from embeddings import chroma_manager
from embeddings.build_embeddings import build_embeddings
from embeddings.transform import chunk_fingerprint, transform_version
from model_registry import embedding_config
from settings import settings

from ..stage import Stage, Store
from .corpus import CorpusStage


class EmbeddingsStage(Stage):
    def __init__(self, variant: str, corpus: CorpusStage, store: Store):
        self.variant = variant
        self.name = f"embeddings:{variant}"
        self.store = store
        self.id = variant  # its collection name in the ChromaStore
        self._corpus = corpus

    def inputs(self) -> list[Stage]:
        return [self._corpus]

    def desired(self) -> dict[str, str]:
        """Fold each document's corpus output fingerprint into this variant's transform key."""
        cfg = embedding_config(self.variant)
        emb = settings.embedding
        tv = transform_version(cfg, emb.chunk_size, emb.chunk_overlap)
        return {
            doc: chunk_fingerprint(content_fp, tv)
            for doc, content_fp in self._corpus.doc_fingerprints().items()
        }

    def actual(self) -> dict[str, str]:
        """Per document, its stored chunk fingerprint (shared by all its chunks)."""
        metas = self._metadatas()
        out: dict[str, str] = {}
        for meta in metas:
            did, fp = (meta or {}).get("document_id"), (meta or {}).get("fingerprint")
            if did and fp:
                out[did] = fp
        return out

    def build(self, keys: set[str]) -> None:
        build_embeddings(model_name=self.variant, rebuild=set(keys))

    def delete(self, keys: set[str]) -> None:
        """Level-1: drop these documents' chunks from this variant's collection."""
        try:
            col = chroma_manager.get_collection(self.variant)
        except Exception:
            return
        res = col.get(include=["metadatas"])
        ids = [
            cid
            for cid, meta in zip(res.get("ids") or [], res.get("metadatas") or [], strict=True)
            if (meta or {}).get("document_id") in keys
        ]
        if ids:
            col.delete(ids=ids)

    def _metadatas(self) -> list[dict]:
        try:
            col = chroma_manager.get_collection(self.variant)
        except Exception:
            return []  # collection not created yet → nothing built
        return col.get(include=["metadatas"]).get("metadatas") or []
