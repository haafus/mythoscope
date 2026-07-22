import logging
from typing import Any

import chromadb
import numpy as np

from settings import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.embeddings_dir))
    return _client


class ChromaCollection:
    def __init__(self, collection: chromadb.Collection):
        self._collection = collection

    @property
    def name(self) -> str:
        return self._collection.name

    @property
    def metadata(self) -> dict:
        return self._collection.metadata or {}

    def count(self) -> int:
        return self._collection.count()

    def get(self, **kwargs) -> dict:
        return self._collection.get(**kwargs)

    def upsert(
        self,
        ids: list[str],
        embeddings: np.ndarray | list[list[float]],
        metadatas: list[dict[str, Any]],
        documents: list[str],
    ) -> None:
        self._collection.upsert(
            ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents,
        )

    def modify(self, metadata: dict) -> None:
        self._collection.modify(metadata=metadata)

    def query(self, **kwargs) -> dict:
        return self._collection.query(**kwargs)

    def delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)

    def load_data(self) -> tuple[list[dict[str, Any]], np.ndarray]:
        results = self._collection.get(include=["embeddings", "metadatas", "documents"])

        # Rename text_id -> id without mutating the metadata dicts Chroma returned,
        # and without raising if a record lacks text_id (foreign/older collection).
        records = [
            {
                **{k: v for k, v in (meta or {}).items() if k != "text_id"},
                "id": (meta or {}).get("text_id", ""),
                "text": doc,
            }
            for meta, doc in zip(results["metadatas"], results["documents"], strict=True)
        ]
        embeddings = np.array(results["embeddings"], dtype=np.float32) if records else np.empty((0, 0), dtype=np.float32)
        return records, embeddings


def get_or_create_collection(key: str, **kwargs) -> ChromaCollection:
    return ChromaCollection(
        _get_client().get_or_create_collection(name=key, **kwargs)
    )


def get_collection(key: str) -> ChromaCollection:
    return ChromaCollection(
        _get_client().get_collection(name=key)
    )


def list_collections() -> list[ChromaCollection]:
    return [ChromaCollection(col) for col in _get_client().list_collections()]


def get_available_models() -> list[str]:
    return sorted(col.name for col in _get_client().list_collections())


def delete_collection(key: str) -> bool:
    try:
        _get_client().delete_collection(name=key)
        return True
    except Exception as e:
        code = getattr(e, "status_code", None) or getattr(e, "code", None)
        message = getattr(e, "message", None) or str(e)
        logger.error(f"Failed to delete collection {key!r} (code={code}): {message}")
        return False
