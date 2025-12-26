import numpy as np
import umap
import os

# ===== НАСТРОЙКИ =====
EMB_PATH = "embeddings/chunk_embeddings.npy"
OUT_DIR = "embeddings_reduced"

N_COMPONENTS = 2
N_NEIGHBORS = 15
MIN_DIST = 0.1
# ====================

os.makedirs(OUT_DIR, exist_ok=True)

X = np.load(EMB_PATH)

reducer = umap.UMAP(
    n_components=N_COMPONENTS,
    n_neighbors=N_NEIGHBORS,
    min_dist=MIN_DIST,
    metric="cosine",
    random_state=42
)

X_umap = reducer.fit_transform(X)

np.save(
    os.path.join(OUT_DIR, "chunk_embeddings_umap_2d.npy"),
    X_umap
)

print("UMAP shape:", X_umap.shape)
