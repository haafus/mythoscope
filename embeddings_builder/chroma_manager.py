from contextlib import contextmanager
from typing import List, Dict, Any, Optional

import chromadb

def save_to_chroma_collection(
        collection: chromadb.Collection, # Меняем client на collection
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str],
):
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents,
    )

def delete_collection(client: chromadb.PersistentClient, collection_name: str):
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass


def query_chroma_collection(
        collection: chromadb.Collection,
        query_embedding: List[float],
        top_k: int = 5,
) -> List[Dict[str, Any]]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    formatted = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        formatted.append({
            "document": doc,
            "metadata": meta,
            "distance": dist,
        })
    return formatted

@contextmanager
def get_chroma_collection(client: chromadb.PersistentClient, collection_name: str):
    """Context manager for safe collection access"""
    collection = None
    try:
        collection = client.get_or_create_collection(name=collection_name)
        yield collection
    finally:
        # Chroma doesn't require explicit closing, but we keep for future
        pass