from typing import List, Dict

import chromadb

from .config import CORPUS_METADATA_PATH, CHROMA_PATH
from .utils import load_corpus_metadata, safe_numpy_array


class EmbeddingDataLoader:
    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self.metadata_map = load_corpus_metadata(CORPUS_METADATA_PATH)
        self.data = self._load_embeddings()

    def _load_embeddings(self) -> List[Dict]:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name=self.collection_name)
        results = collection.get(include=["embeddings", "metadatas", "documents"])

        data = []
        for doc_id, emb, meta, doc in zip(
                results["ids"], results["embeddings"], results["metadatas"], results["documents"]
        ):
            text_id = meta.get("text_id", "unknown")
            tradition = self.metadata_map.get(text_id, "unknown")
            chunk_index = meta.get("chunk_index", 0)
            model = meta.get("model", "unknown")

            data.append(
                {
                    "id": text_id,
                    "tradition": tradition,
                    "chunk_index": chunk_index,
                    "embedding": safe_numpy_array(emb),
                    "text": doc,
                    "model": model,
                }
            )
        return data

    def get_data(self) -> List[Dict]:
        return self.data
