import json
import os
from typing import Dict

import numpy as np
import umap


def load_corpus_metadata(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        print(f"{path} не найден, 'tradition' будет 'unknown'")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return {item["id"]: item["tradition"] for item in metadata}


def _reduce_dimensions(embeddings: np.ndarray, n_components: int = 2) -> np.ndarray:
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42,
        n_jobs=-1
    )
    return reducer.fit_transform(embeddings)

def safe_numpy_array(emb) -> "np.ndarray":
    return np.array(emb) if isinstance(emb, list) else emb
