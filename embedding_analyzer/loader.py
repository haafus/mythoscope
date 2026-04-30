import os
import json
import numpy as np
from typing import List, Dict, Optional, Any, Generator
import chromadb
from .config import get_analyzer_config
import logging

logger = logging.getLogger(__name__)


class EmbeddingDataLoader:
    def __init__(self, collection_name: str = "corpus", auto_migrate: bool = True):
        self.config = get_analyzer_config()
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.config.chroma_path)
        self._metadata_map: Optional[Dict[str, str]] = None
        self._collection = None

        if auto_migrate:
            self._auto_migrate_all()

    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except Exception as e:
                logger.error(f"Failed to get collection '{self.collection_name}': {e}")
                raise
        return self._collection

    def _load_metadata_map(self) -> Dict[str, str]:
        if self._metadata_map is not None:
            return self._metadata_map

        metadata_path = self.config.corpus_metadata_path
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata file not found: {metadata_path}")
            self._metadata_map = {}
            return self._metadata_map

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            self._metadata_map = {str(item["id"]): item["tradition"] for item in metadata}
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.error(f"Failed to load metadata: {e}")
            self._metadata_map = {}

        return self._metadata_map

    def _auto_migrate_all(self) -> None:
        try:
            collection = self.collection
            count = collection.count()

            if count == 0:
                return

            if not self._needs_migration(collection):
                return

            logger.info("Обнаружены записи без tradition в Chroma. Выполняется миграция...")
            metadata_map = self._load_metadata_map()

            if not metadata_map:
                logger.warning("Нет данных для миграции")
                return

            migrated = self._migrate_records(collection, metadata_map)
            logger.info(f"Миграция завершена. Обновлено {migrated} записей.")

        except Exception as e:
            logger.error(f"Auto-migration failed: {e}")

    def _needs_migration(self, collection) -> bool:
        try:
            sample = collection.get(limit=min(5, collection.count()), include=["metadatas"])
            if not sample["metadatas"]:
                return False

            return any(
                "tradition" not in meta or meta.get("tradition") == "unknown"
                for meta in sample["metadatas"] if meta
            )
        except Exception as e:
            logger.warning(f"Failed to check migration need: {e}")
            return False

    def _migrate_records(self, collection, metadata_map: Dict[str, str]) -> int:
        batch_size = 1000
        offset = 0
        migrated = 0

        while True:
            try:
                results = collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas", "ids"]
                )

                if not results["ids"]:
                    break

                updates = self._prepare_updates(results, metadata_map)

                for doc_id, meta in updates:
                    try:
                        collection.update(ids=[doc_id], metadatas=[meta])
                        migrated += 1
                    except Exception as e:
                        logger.warning(f"Failed to update {doc_id}: {e}")

                offset += batch_size

                if migrated > 0 and offset % (batch_size * 5) == 0:
                    logger.info(f"  Мигрировано {migrated} записей...")

                if len(results["ids"]) < batch_size:
                    break

            except Exception as e:
                logger.error(f"Migration batch failed at offset {offset}: {e}")
                break

        return migrated

    def _prepare_updates(self, results: Dict, metadata_map: Dict[str, str]) -> List[tuple]:
        updates = []
        for doc_id, meta in zip(results["ids"], results["metadatas"]):
            if not meta:
                continue

            if "tradition" not in meta or meta.get("tradition") == "unknown":
                text_id = meta.get("text_id", doc_id)
                tradition = metadata_map.get(str(text_id), "unknown")
                if tradition != "unknown":
                    meta["tradition"] = tradition
                    updates.append((doc_id, meta))

        return updates

    def load_data(
            self,
            model_name: Optional[str] = None,
            batch_size: int = 5000,
            max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        all_data = []
        offset = 0
        where_filter = {"model": model_name} if model_name else None

        while True:
            if max_records and len(all_data) >= max_records:
                logger.info(f"Достигнут лимит записей: {max_records}")
                break

            try:
                results = self.collection.get(
                    where=where_filter,
                    limit=batch_size,
                    offset=offset,
                    include=["embeddings", "metadatas", "documents"]
                )
            except Exception as e:
                logger.error(f"Failed to fetch data at offset {offset}: {e}")
                break

            if not results.get("ids"):
                break

            batch_data = self._process_batch(results)
            all_data.extend(batch_data)

            offset += batch_size

            if len(results["ids"]) < batch_size:
                break

        return all_data

    def _process_batch(self, results: Dict) -> List[Dict[str, Any]]:
        batch_data = []
        ids = results.get("ids", [])
        embeddings = results.get("embeddings", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])

        for i, doc_id in enumerate(ids):
            try:
                if i >= len(embeddings) or embeddings[i] is None:
                    continue

                meta = metadatas[i] if i < len(metadatas) else {}
                doc = documents[i] if i < len(documents) else ""

                embedding = np.array(embeddings[i]) if isinstance(embeddings[i], list) else embeddings[i]

                batch_data.append({
                    "id": meta.get("text_id", doc_id),
                    "tradition": meta.get("tradition", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "embedding": embedding,
                    "text": doc,
                    "model": meta.get("model", "unknown"),
                    "filename": meta.get("filename", "unknown"),
                    "chunking": meta.get("chunking", "unknown"),
                })
            except Exception as e:
                logger.warning(f"Failed to process document {doc_id}: {e}")
                continue

        return batch_data

    def get_available_models(self) -> List[str]:
        try:
            result = self.collection.get(limit=10000, include=["metadatas"])
            metadatas = result.get("metadatas", [])
            models = {m.get("model") for m in metadatas if m and "model" in m}
            return sorted(list(models))
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []

    def close(self):
        if hasattr(self, 'client'):
            self._collection = None
            self.client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()