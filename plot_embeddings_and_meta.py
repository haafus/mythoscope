import numpy as np
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# ===== НАСТРОЙКИ =====
EMB_PATH = "embeddings_reduced/chunk_embeddings_umap_2d.npy"
META_PATH = "embeddings/chunk_metadata.json"
MAX_TEXTS = 15          # сколько разных текстов показывать цветами
POINT_SIZE = 10
ALPHA = 0.75
# ====================

X = np.load(EMB_PATH)

with open(META_PATH, encoding="utf-8") as f:
    meta = json.load(f)

labels = [m["text_id"].split(os.sep)[0] for m in meta]

# ограничим число цветов
unique = list(dict.fromkeys(labels))[:MAX_TEXTS]
label_to_idx = {l: i for i, l in enumerate(unique)}

colors = [
    label_to_idx.get(l, -1)
    for l in labels
]

plt.figure(figsize=(12, 9))
scatter = plt.scatter(
    X[:, 0],
    X[:, 1],
    c=colors,
    s=POINT_SIZE,
    alpha=ALPHA,
    cmap="tab20"
)

plt.title("Chunk Embeddings by Text / Tradition")
plt.xlabel("Dim 1")
plt.ylabel("Dim 2")

plt.colorbar(scatter, label="Text group")
plt.grid(True)
plt.tight_layout()
plt.show()
