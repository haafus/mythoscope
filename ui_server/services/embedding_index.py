from dataclasses import dataclass
import csv
from typing import Dict, List, Optional

import numpy as np

from ui_server.services.models import get_model_output_dir
from ui_server.services.models import key_to_model


MAX_PREVIEW_CHARS = 700


@dataclass
class ModelIndex:
    model_name: str
    items: List[Dict]
    matrix: np.ndarray
    normalized_matrix: np.ndarray
    id_to_index: Dict[str, int]


class EmbeddingIndexService:
    def __init__(self):
        self._indexes: Dict[str, ModelIndex] = {}
        self._point_records: Dict[str, Dict[str, Dict]] = {}
        self._search_models: Dict[str, object] = {}

    def get_index(self, model_key: str) -> ModelIndex:
        model_name = key_to_model(model_key)
        if model_name in self._indexes:
            return self._indexes[model_name]

        index = self._load_index(model_name)
        self._indexes[model_name] = index
        return index

    def get_point(self, model_key: str, point_id: str, chunk_index: Optional[int] = None) -> Dict:
        model_name = key_to_model(model_key)
        item = self._get_point_record(model_name, point_id, chunk_index)
        if item is None:
            index = self.get_index(model_name)
            item_index = index.id_to_index.get(self._point_key(point_id, chunk_index))
            if item_index is None:
                item_index = index.id_to_index.get(str(point_id))
            if item_index is None:
                raise KeyError(point_id)
            item = index.items[item_index]

        if not item:
            raise KeyError(point_id)

        return {
            "id": str(item.get("id")),
            "text": item.get("text", ""),
            "tradition": item.get("tradition", "Unknown"),
            "chunk_index": item.get("chunk_index", 0),
            "book_title": item.get("filename", "") or item.get("id", ""),
            "model": item.get("model", model_name),
            "metadata": {
                "filename": item.get("filename", ""),
                "major_tradition": item.get("major_tradition", ""),
                "doc_type": item.get("doc_type", ""),
                "language": item.get("language", ""),
                "url": item.get("url", ""),
            },
        }

    def get_neighbors(self, model_key: str, point_id: str, n: int = 10, chunk_index: Optional[int] = None) -> List[Dict]:
        index = self.get_index(model_key)
        item_index = index.id_to_index.get(self._point_key(point_id, chunk_index))
        if item_index is None:
            item_index = index.id_to_index.get(str(point_id))
        if item_index is None:
            raise KeyError(point_id)

        query_vector = index.normalized_matrix[item_index]
        similarities = index.normalized_matrix @ query_vector
        similarities[item_index] = -np.inf
        return self._top_results(index, similarities, n)

    def search(self, model_key: str, query: str, top_k: int = 20) -> List[Dict]:
        model_name = key_to_model(model_key)
        index = self.get_index(model_name)
        query_embedding = self._embed_query(model_name, query)
        query_embedding = self._normalize_vector(query_embedding)
        similarities = index.normalized_matrix @ query_embedding
        return self._top_results(index, similarities, top_k)

    def _load_index(self, model_name: str) -> ModelIndex:
        from embedding_analyzer.analyzer import EmbeddingAnalyzer

        analyzer = EmbeddingAnalyzer(model_name=model_name)
        items = analyzer.filter_by_model()
        if not items:
            raise RuntimeError(f"No embedding data found for {model_name}")

        matrix = np.stack([item["embedding"] for item in items]).astype(np.float32)
        normalized_matrix = self._normalize_matrix(matrix)
        id_to_index = {}
        for idx, item in enumerate(items):
            point_id = str(item.get("id"))
            id_to_index.setdefault(point_id, idx)
            id_to_index[self._point_key(point_id, item.get("chunk_index"))] = idx

        return ModelIndex(
            model_name=model_name,
            items=items,
            matrix=matrix,
            normalized_matrix=normalized_matrix,
            id_to_index=id_to_index,
        )

    def _get_point_record(self, model_name: str, point_id: str, chunk_index: Optional[int] = None) -> Optional[Dict]:
        if model_name not in self._point_records:
            self._point_records[model_name] = self._load_point_records(model_name)

        records = self._point_records[model_name]
        item = records.get(self._point_key(point_id, chunk_index))
        if item is not None:
            return item
        return records.get(str(point_id))

    @staticmethod
    def _load_point_records(model_name: str) -> Dict[str, Dict]:
        csv_path = get_model_output_dir(model_name) / "embeddings_data.csv"
        if not csv_path.exists():
            return {}

        records: Dict[str, Dict] = {}
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                point_id = str(row.get("id", ""))
                if point_id:
                    record = {
                        "id": point_id,
                        "text": row.get("text", ""),
                        "tradition": row.get("tradition", "Unknown"),
                        "major_tradition": row.get("major_tradition", ""),
                        "chunk_index": int(row.get("chunk_index") or 0),
                        "model": row.get("model", model_name),
                        "filename": row.get("filename", ""),
                        "doc_type": row.get("doc_type", ""),
                        "language": row.get("language", ""),
                        "url": row.get("url", ""),
                    }
                    records.setdefault(point_id, record)
                    records[EmbeddingIndexService._point_key(point_id, record["chunk_index"])] = record

        return records

    @staticmethod
    def _point_key(point_id: str, chunk_index: Optional[int] = None) -> str:
        if chunk_index is None or chunk_index == "":
            return str(point_id)
        return f"{point_id}::{chunk_index}"

    def _embed_query(self, model_name: str, query: str) -> np.ndarray:
        from sentence_transformers import SentenceTransformer
        from embeddings_builder.models_repository import MODELS

        if model_name not in self._search_models:
            model_path = MODELS.get(model_name, {}).get("path", model_name)
            self._search_models[model_name] = SentenceTransformer(model_path)

        model = self._search_models[model_name]
        embedding = model.encode([query], normalize_embeddings=True)[0]
        return np.asarray(embedding, dtype=np.float32)

    @staticmethod
    def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return matrix / norms

    @staticmethod
    def _normalize_vector(vector: np.ndarray) -> np.ndarray:
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            return vector
        return vector / norm

    @staticmethod
    def _top_results(index: ModelIndex, similarities: np.ndarray, limit: int) -> List[Dict]:
        limit = min(limit, len(index.items))
        if limit <= 0:
            return []

        candidate_indices = np.argpartition(-similarities, limit - 1)[:limit]
        candidate_indices = candidate_indices[np.argsort(-similarities[candidate_indices])]

        results = []
        for idx in candidate_indices:
            similarity = float(similarities[idx])
            if not np.isfinite(similarity):
                continue

            item = index.items[int(idx)]
            text = item.get("text", "") or ""
            preview = text[:MAX_PREVIEW_CHARS]
            if len(text) > MAX_PREVIEW_CHARS:
                preview += "..."

            results.append(
                {
                    "id": str(item.get("id")),
                    "tradition": item.get("tradition", "Unknown"),
                    "major_tradition": item.get("major_tradition", ""),
                    "chunk_index": item.get("chunk_index", 0),
                    "similarity_score": similarity,
                    "distance": 1 - similarity,
                    "text": text,
                    "text_preview": preview,
                    "filename": item.get("filename", ""),
                    "book_title": item.get("filename", "") or item.get("id", ""),
                }
            )

        return results


embedding_index_service = EmbeddingIndexService()
