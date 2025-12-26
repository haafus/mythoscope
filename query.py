import faiss
import json
import numpy as np

# ================= НАСТРОЙКИ =================
TOP_K = 6
MAX_CONTEXT_TOKENS = 3000
# =============================================

# загрузка индекса
index = faiss.read_index("faiss/mythology.index")
with open("faiss/chunk_metadata.json", encoding="utf-8") as f:
    chunk_meta = json.load(f)

def retrieve(query, top_k=TOP_K):
    q_emb = model.encode([query], normalize_embeddings=True)
    scores, ids = index.search(q_emb, top_k)

    results = []
    for idx in ids[0]:
        results.append(chunk_meta[idx])

    return results

def build_prompt(query, chunks):
    context = "\n\n".join(
        f"[{c['text_id']}]\n{c['text']}"
        for c in chunks
    )

    prompt = f"""
You are a scholar of comparative mythology and religious studies.

Use ONLY the following sources to answer.

Sources:
{context}

Question:
{query}

Answer with references to traditions and texts.
"""
    return prompt.strip()

def generate_answer(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(llm.device)

    out = llm.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
        temperature=0.0
    )

    return tokenizer.decode(out[0], skip_special_tokens=True)

# =================== RUN ======================
query = input("Mythology question: ")

chunks = retrieve(query)
prompt = build_prompt(query, chunks)
answer = generate_answer(prompt)

print("\n=== ANSWER ===\n")
print(answer)
