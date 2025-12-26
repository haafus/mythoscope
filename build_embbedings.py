import os
import json
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import nltk

# ================== НАСТРОЙКИ ==================
CORPUS_DIR = "corpus"
OUT_DIR = "embeddings"

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

CHUNK_SIZE = 5        # предложений в чанке
CHUNK_OVERLAP = 2     # overlap предложений

MIN_SENT_LEN = 20     # фильтр мусора
# =================================================

nltk.download("punkt")
from nltk.tokenize import sent_tokenize

os.makedirs(OUT_DIR, exist_ok=True)

model = SentenceTransformer(MODEL_NAME)

sentence_texts = []
sentence_meta = []

chunk_texts = []
chunk_meta = []

print("📚 Reading corpus...")

for root, _, files in os.walk(CORPUS_DIR):
    for fname in files:
        if not fname.endswith(".txt"):
            continue

        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, CORPUS_DIR)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        sentences = [
            s.strip() for s in sent_tokenize(text)
            if len(s.strip()) >= MIN_SENT_LEN
        ]

        # ---------- sentence embeddings ----------
        for i, s in enumerate(sentences):
            sentence_texts.append(s)
            sentence_meta.append({
                "text_id": rel_path,
                "sentence_id": i,
                "text": s
            })

        # ---------- chunk embeddings ----------
        step = CHUNK_SIZE - CHUNK_OVERLAP
        for i in range(0, len(sentences) - CHUNK_SIZE + 1, step):
            chunk = sentences[i:i + CHUNK_SIZE]
            chunk_text = " ".join(chunk)

            chunk_texts.append(chunk_text)
            chunk_meta.append({
                "text_id": rel_path,
                "chunk_id": i // step,
                "start_sentence": i,
                "end_sentence": i + CHUNK_SIZE - 1,
                "text": chunk_text
            })

print(f"🔢 Sentences: {len(sentence_texts)}")
print(f"🔢 Chunks: {len(chunk_texts)}")

# ================== ЭМБЕДДИНГИ ==================
print("🧠 Encoding sentences...")
sentence_embeddings = model.encode(
    sentence_texts,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

print("🧠 Encoding chunks...")
chunk_embeddings = model.encode(
    chunk_texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

# ================== СОХРАНЕНИЕ ==================
np.save(os.path.join(OUT_DIR, "sentence_embeddings.npy"), sentence_embeddings)
np.save(os.path.join(OUT_DIR, "chunk_embeddings.npy"), chunk_embeddings)

with open(os.path.join(OUT_DIR, "sentence_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(sentence_meta, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT_DIR, "chunk_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(chunk_meta, f, ensure_ascii=False, indent=2)

print("✅ Done")
print(f"Sentence embeddings shape: {sentence_embeddings.shape}")
print(f"Chunk embeddings shape: {chunk_embeddings.shape}")
