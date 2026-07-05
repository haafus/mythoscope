"""Semantic parallels built on BGE-M3 (real transformer embeddings), with the LSA
(TF-IDF+SVD) version alongside for a direct A/B. Same motif corpus as prototype 02.

Because a browser can't run BGE-M3, cross-index nearest neighbours are precomputed
here (per motif, top-K in each other index, tagged known vs novel) for both methods,
plus recall@k of the confirmed cross-walk links so the two are comparable in numbers.

BGE embeddings are cached to bge_emb.npy (encoding on CPU is the slow part).

Run from repo root:  python mockups/04-semantic-parallels-bge/build_data.py
"""
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "data.js"
CACHE = HERE / "bge_emb.npy"
MODEL, TOPK = "BAAI/bge-m3", 6


def load(n):
    with open(ROOT / "outputs" / "motifs" / n, encoding="utf-8") as f:
        return json.load(f)


def collect():
    docs = []
    for r in load("tmi.json")["motifs"]:
        d = (r.get("definition") or "").strip()
        if d:
            docs.append(("tmi", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {d}"))
    for r in load("atu.json")["types"]:
        t = (r.get("summary") or "").strip()
        docs.append(("atu", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {t}"))
    for r in load("berezkin.json")["motifs"]:
        d = (r.get("definition") or "").strip()
        docs.append(("brz", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {d}"))
    return docs


def bge_embed(texts):
    if CACHE.exists():
        E = np.load(CACHE)
        if len(E) == len(texts):
            print(f"loaded cached BGE embeddings {E.shape}")
            return E
    from sentence_transformers import SentenceTransformer
    print(f"encoding {len(texts)} docs with {MODEL} (CPU)…")
    m = SentenceTransformer(MODEL)
    m.max_seq_length = 256
    E = m.encode(texts, batch_size=32, normalize_embeddings=True,
                 show_progress_bar=True, convert_to_numpy=True).astype(np.float32)
    np.save(CACHE, E)
    return E


def lsa_embed(texts):
    X = TfidfVectorizer(stop_words="english", max_features=6000, sublinear_tf=True,
                        ngram_range=(1, 2), min_df=3).fit_transform(texts)
    return normalize(TruncatedSVD(128, random_state=0).fit_transform(X)).astype(np.float32)


def confirmed(id2i):
    cw = load("crosswalk.json")
    fwd = [("atu", "tmi", "atu_to_tmi"), ("atu", "tmi", "atu_to_tmi_note"),
           ("atu", "tmi", "atu_to_tmi_summary"), ("atu", "tmi", "atu_to_tmi_defining"),
           ("brz", "atu", "berezkin_to_atu"), ("brz", "tmi", "berezkin_to_tmi")]
    pairs = set()
    for left, right, m in fwd:
        for lid, rids in (cw.get(m) or {}).items():
            i = id2i.get(f"{left}:{lid}")
            if i is None:
                continue
            for rid in rids:
                j = id2i.get(f"{right}:{rid}")
                if j is not None:
                    pairs.add((min(i, j), max(i, j)))
    return pairs


def recall_at(E, idx, pairs, byidx, ks=(1, 5, 10, 20), sample=1500, seed=0):
    rng = np.random.default_rng(seed)
    P = list(pairs)
    sel = [P[i] for i in rng.choice(len(P), min(sample, len(P)), replace=False)]
    hit = {k: 0 for k in ks}
    for a, b in sel:
        # rank b among target-index docs by similarity to a (b may be either endpoint)
        for src, tgt in ((a, b), (b, a)):
            cand = byidx[idx[tgt]]
            sims = E[cand] @ E[src]
            order = cand[np.argsort(-sims)]
            rank = int(np.where(order == tgt)[0][0]) + 1
            for k in ks:
                hit[k] += rank <= k
    n = len(sel) * 2
    return {f"@{k}": round(hit[k] / n, 4) for k in ks}


def neighbours(E, idx, byidx, known):
    tbl = []
    for i in range(len(E)):
        row = {}
        for tx in ("tmi", "atu", "brz"):
            if tx == idx[i]:
                continue
            cand = byidx[tx]
            sims = E[cand] @ E[i]
            top = cand[np.argsort(-sims)[:TOPK]]
            row[tx] = [[int(j), round(float(E[j] @ E[i]), 3),
                        1 if (min(i, j), max(i, j)) in known else 0] for j in top]
        tbl.append(row)
    return tbl


def main():
    docs = collect()
    texts = [d[3] for d in docs]
    idx = np.array([d[0] for d in docs])
    id2i = {f"{x}:{c}": i for i, (x, c, _, _) in enumerate(docs)}
    byidx = {x: np.where(idx == x)[0] for x in ("tmi", "atu", "brz")}

    Ebge = bge_embed(texts)
    Elsa = lsa_embed(texts)
    pairs = confirmed(id2i)

    rec_bge = recall_at(Ebge, idx, pairs, byidx)
    rec_lsa = recall_at(Elsa, idx, pairs, byidx)
    print("recall@k  BGE-M3:", rec_bge)
    print("recall@k  LSA   :", rec_lsa)

    data = {
        "n": len(docs), "topk": TOPK,
        "docs": [{"x": x, "c": c, "n": name,
                  "s": (txt[len(name) + 2:] if txt.startswith(name) else txt)[:150]}
                 for (x, c, name, txt) in docs],
        "bge": neighbours(Ebge, idx, byidx, pairs),
        "lsa": neighbours(Elsa, idx, byidx, pairs),
        "eval": {"bge": rec_bge, "lsa": rec_lsa, "n_pairs": len(pairs)},
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"docs={len(docs)}  data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
