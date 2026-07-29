import logging
import threading

import numpy as np

from corpus.utils import chunk_id

logger = logging.getLogger(__name__)


def _hit(meta: dict, text: str, score: float) -> dict:
    """A search hit: chunk data + the document reference only (B1). tradition/region/url/
    colour are resolved on the front from the reference — never carried on the hit (§3)."""
    return {
        "document_id": meta.get("document_id", ""),
        "chunk_index": meta.get("chunk_index", 0),
        "text": text,
        "source_text": meta.get("source_text", ""),
        "similarity_score": score,
    }


class SimilarityService:
    def __init__(self):
        self._encoder = None
        # Serialize the load+encode path so a background warmup and a real
        # search don't race into a double model load on a cold process.
        self._encode_lock = threading.Lock()

    def get_point(self, model_key: str, document_id: str, chunk_index: int,
                  top_k: int = 1, cross_tradition: bool = False) -> list[dict]:
        collection = self._get_collection(model_key)
        cid = chunk_id(document_id, chunk_index)
        point = collection.get(ids=[cid], include=["embeddings", "metadatas", "documents"])
        if not point["ids"]:
            return []
        embedding = point["embeddings"][0]

        # The head is ALWAYS the clicked chunk, fetched here by id — never `query[0]`. The HNSW
        # search graph is approximate and can drift from the store (a degraded graph may not even
        # return a chunk for its own vector), so trusting the top query hit to be the clicked point
        # is the bug that showed a foreign fragment. `get`-by-id is deterministic; `_query` is used
        # only to find neighbours (see docs/proposals/chroma-hnsw-index-integrity.md).
        head = _hit(dict(point["metadatas"][0]), point["documents"][0], 1.0)

        # Cross-tradition: pull neighbours only from OTHER traditions so the list surfaces
        # cross-cultural parallels. With no tradition on the chunk (B1), resolve it from
        # document_id and exclude that tradition's documents by id (§5 step 4).
        where = None
        if cross_tradition:
            from server.services.corpus import document_ids_for_tradition, tradition_of_document
            tradition = tradition_of_document(document_id)
            exclude = sorted(document_ids_for_tradition(tradition)) if tradition else []
            where = {"document_id": {"$nin": exclude}} if exclude else None

        # Over-fetch by one, then drop the clicked chunk itself by id (not by rank — a degraded
        # graph may not rank it first, or at all), so it never appears twice.
        neighbors = [
            n for n in self._query(collection, embedding, top_k + 1, where=where)
            if not (n["document_id"] == document_id and n["chunk_index"] == chunk_index)
        ]
        return [head, *neighbors[:top_k]]

    def search(self, model_key: str, query: str, top_k: int = 20) -> list[dict]:
        collection = self._get_collection(model_key)
        embedding = self._encode_query(model_key, query)
        return self._query(collection, embedding.tolist(), top_k)

    def warmup(self, model_key: str) -> None:
        """Pay the first-search cold-start cost up front: import torch, load
        the model, run one encode, and warm the collection's HNSW index, so the
        user's first real text search hits warm caches.

        Raises ImportError in the viewer build (no embedding deps); callers map
        that to 503 just like search().
        """
        collection = self._get_collection(model_key)
        embedding = self._encode_query(model_key, "warmup")
        self._query(collection, embedding.tolist(), 1)

    def _get_collection(self, model_key: str):
        from embeddings import chroma_manager
        return chroma_manager.get_collection(model_key)

    def _query(self, collection, embedding, top_k: int, where=None) -> list[dict]:
        raw = collection.query(
            query_embeddings=[embedding], n_results=top_k,
            include=["metadatas", "documents", "distances"],
            **({"where": where} if where else {}),
        )
        return [
            _hit(meta, doc, round(1 - dist, 6))
            for meta, doc, dist in zip(
                raw["metadatas"][0], raw["documents"][0],
                raw["distances"][0], strict=True,
            )
        ]

    def _encode_query(self, model_key: str, query: str) -> np.ndarray:
        # Lazy import keeps the viewer build torch-free; raises ImportError
        # there, which the API maps to 503.
        from embeddings.model_manager import EmbeddingEncoder
        with self._encode_lock:
            if self._encoder is None:
                self._encoder = EmbeddingEncoder()
            self._encoder.load(model_key)
            prefix = self._encoder.config["query_prefix"]
            raw = self._encoder.encode(
                [prefix + query],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        return np.asarray(raw[0], dtype=np.float32)


similarity_service = SimilarityService()
