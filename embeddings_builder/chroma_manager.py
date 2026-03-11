from typing import List, Dict, Any, Optional

import chromadb

def save_to_chroma_collection(
        client: chromadb.PersistentClient,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str],
):
    collection = client.get_or_create_collection(name=collection_name)
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
    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append(
            {
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return formatted