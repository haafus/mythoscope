"""Build LSA (TF-IDF + truncated SVD) embeddings of motif text across the three
indexes, so the mockup can do live semantic nearest-neighbour search *and* free-text
query — entirely in the browser, offline.

This is a stand-in for real transformer embeddings (sentence-transformers / an API):
same UX and cross-index behaviour, swap the vectoriser when a model is available.

Ships (base64-packed, int8-quantised): per-motif vectors, the SVD projection matrix,
the TF-IDF vocabulary/idf/stopwords (so the browser can embed a typed query), and the
set of confirmed cross-walk pairs (to tag a suggestion as already-known vs novel).

Run from repo root:  python mockups/02-semantic-parallels/build_data.py
"""
import base64
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"
DIM, MAXF = 128, 6000


def load(name):
    return json.load(open(ROOT / "outputs" / "motifs" / name, encoding="utf-8"))


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode()


def collect():
    docs = []
    for r in load("tmi.json")["motifs"]:
        d = (r.get("definition") or "").strip()
        if not d:
            continue                      # keep TMI to the ~8k defined motifs (quality + size)
        docs.append(("tmi", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {d}"))
    for r in load("atu.json")["types"]:
        t = (r.get("summary") or "").strip()
        docs.append(("atu", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {t}"))
    for r in load("berezkin.json")["motifs"]:
        d = (r.get("definition") or "").strip()
        docs.append(("brz", r["id"], r.get("name") or r["id"], f"{r.get('name','')}. {d}"))
    return docs


def confirmed_pairs(id_to_i):
    cw = load("crosswalk.json")
    fwd = [("atu", "tmi", "atu_to_tmi"), ("atu", "tmi", "atu_to_tmi_defining"),
           ("atu", "tmi", "atu_to_tmi_note"), ("atu", "tmi", "atu_to_tmi_summary"),
           ("brz", "atu", "berezkin_to_atu"), ("brz", "tmi", "berezkin_to_tmi")]
    pairs = set()
    for left, right, m in fwd:
        for lid, rids in (cw.get(m) or {}).items():
            i = id_to_i.get(f"{left}:{lid}")
            if i is None:
                continue
            for rid in rids:
                j = id_to_i.get(f"{right}:{rid}")
                if j is not None:
                    pairs.add((min(i, j), max(i, j)))
    return pairs


def main():
    docs = collect()
    texts = [d[3] for d in docs]
    vec = TfidfVectorizer(stop_words="english", max_features=MAXF,
                          sublinear_tf=True, ngram_range=(1, 2), min_df=3)
    X = vec.fit_transform(texts)
    svd = TruncatedSVD(n_components=DIM, random_state=0)
    V = svd.fit_transform(X)                     # (N, DIM), not unit norm
    V = normalize(V).astype(np.float32)          # L2 for cosine

    # int8 quantisation (per whole matrix) — cosine survives fine.
    vscale = float(np.abs(V).max()) / 127.0
    Vq = np.round(V / vscale).clip(-127, 127).astype(np.int8)
    comp = svd.components_.astype(np.float32)     # (DIM, n_features)
    cscale = float(np.abs(comp).max()) / 127.0
    compq = np.round(comp / cscale).clip(-127, 127).astype(np.int8)

    id_to_i = {f"{x}:{c}": i for i, (x, c, _, _) in enumerate(docs)}
    pairs = confirmed_pairs(id_to_i)

    vocab = vec.get_feature_names_out().tolist()
    idf = vec.idf_.astype(np.float32)

    data = {
        "dim": DIM, "n": len(docs),
        "docs": [{"x": x, "c": c, "n": name,
                  "s": (txt[len(name) + 2:] if txt.startswith(name) else txt)[:150]}
                 for (x, c, name, txt) in docs],
        "vscale": vscale, "vecs": b64(Vq),                    # (N, DIM) int8
        "cscale": cscale, "comp": b64(compq), "nfeat": comp.shape[1],  # (DIM, nfeat) int8
        "vocab": vocab, "idf": [round(float(v), 4) for v in idf],
        "stop": sorted(ENGLISH_STOP_WORDS),
        "pairs": sorted([a, b] for a, b in pairs),
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    by = {}
    for x, *_ in docs:
        by[x] = by.get(x, 0) + 1
    print(f"docs={len(docs)} {by}  vocab={len(vocab)} dim={DIM}  confirmed-pairs={len(pairs)}")
    print(f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
