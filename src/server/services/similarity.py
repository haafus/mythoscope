import logging
import threading

import numpy as np

from corpus.utils import chunk_id

logger = logging.getLogger(__name__)


class SimilarityService:
    def __init__(self):
        self._encoder = None
        # Serialize the load+encode path so a background warmup and a real
        # search don't race into a double model load on a cold process.
        self._encode_lock = threading.Lock()

    def get_point(self, model_key: str, text_id: str, chunk_index: int,
                  top_k: int = 1, cross_tradition: bool = False) -> list[dict]:
        collection = self._get_collection(model_key)
        cid = chunk_id(text_id, chunk_index)
        point = collection.get(ids=[cid], include=["embeddings", "metadatas", "documents"])
        if not point["ids"]:
            return []
        embedding = point["embeddings"][0]
        if not cross_tradition:
            return self._query(collection, embedding, top_k)
        # Keep the clicked chunk as the head; pull neighbors only from other
        # traditions so the list surfaces cross-cultural parallels.
        meta = dict(point["metadatas"][0])
        tradition = meta.get("tradition")
        head = {**meta, "id": meta.pop("text_id"), "text": point["documents"][0],
                "similarity_score": 1.0}
        where = {"tradition": {"$ne": tradition}} if tradition else None
        return [head, *self._query(collection, embedding, top_k, where=where)]

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
            {**meta, "id": meta.pop("text_id"), "text": doc,
             "similarity_score": round(1 - dist, 6)}
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
