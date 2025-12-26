import faiss
import numpy as np
import json
import os

EMB_DIR = "embeddings"
OUT_DIR = "faiss"

os.makedirs(OUT_DIR, exist_ok=True)

# Загружаем чанки
X = np.load(os.path.join(EMB_DIR, "chunk_embeddings.npy"))
with open(os.path.join(EMB_DIR, "chunk_metadata.json"), encoding="utf-8") as f:
    meta = json.load(f)

dim = X.shape[1]

index = faiss.IndexFlatIP(dim)  # cosine similarity (embeddings нормализованы)
index.add(X)

faiss.write_index(index, os.path.join(OUT_DIR, "mythology.index"))

with open(os.path.join(OUT_DIR, "chunk_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print("✅ FAISS index built")
print("Vectors:", index.ntotal)
