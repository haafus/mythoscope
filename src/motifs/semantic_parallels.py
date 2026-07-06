"""Semantic-parallel suggestion layer built on BGE-M3 embeddings.

A second *suggestion* layer beside the lexical ``parallels.py`` and the curated
cross-walk: it embeds each motif's title + description with a transformer
(``BAAI/bge-m3``) and surfaces the nearest look-alikes in the *other* indexes that
carry **no recorded cross-walk link** — the parallels that share meaning but not
words, which the lexical matcher misses.

Kept deliberately out of the normal ``mytho motifs`` build (the model is ~2 GB and
CPU inference is slow). It is precomputed offline by ``scripts/build_semantic_parallels.py``
into the committed ``src/motifs/data/semantic_parallels.json``; ``store`` copies that
into ``outputs/motifs/`` on first read, so the running app needs neither the model nor
``sentence-transformers``. Embeddings are cached to ``outputs/motifs/raw/bge_m3.npy``
so re-runs of the precompute are instant.

Output ``semantic_parallels.json`` mirrors ``parallels.json``::

    {"params": {...}, "counts": {...},
     "adjacency": {index: {id: [{index, id, sim, also_lexical}]}}}
"""

from __future__ import annotations

import logging

from . import store

logger = logging.getLogger(__name__)

MODEL = "BAAI/bge-m3"
MAX_SEQ = 256
THRESH = 0.65        # minimum cosine for a suggestion
TOPK = 6             # neighbours examined per index side
CAP = 8              # suggestions kept per motif


def _collect() -> list[tuple[str, str, str, str]]:
    """(index, id, name, text) per motif — TMI needs a definition, ATU/Berezkin all.

    Order is fixed (TMI, ATU, Berezkin) so the embedding cache stays valid."""
    docs = []
    for r in store.load_index("tmi").get("motifs", []):
        d = (r.get("definition") or "").strip()
        if d:
            docs.append(("tmi", r["id"], r.get("name") or r["id"], f"{r.get('name', '')}. {d}"))
    for r in store.load_index("atu").get("types", []):
        t = (r.get("summary") or "").strip()
        docs.append(("atu", r["id"], r.get("name") or r["id"], f"{r.get('name', '')}. {t}"))
    for r in store.load_index("berezkin").get("motifs", []):
        d = (r.get("definition") or "").strip()
        docs.append(("berezkin", r["id"], r.get("name") or r["id"], f"{r.get('name', '')}. {d}"))
    return docs


def _confirmed_pairs(id2i: dict) -> set:
    cw = store.load_crosswalk()
    fwd = [("atu", "tmi", "atu_to_tmi"), ("atu", "tmi", "atu_to_tmi_note"),
           ("atu", "tmi", "atu_to_tmi_summary"), ("atu", "tmi", "atu_to_tmi_defining"),
           ("berezkin", "atu", "berezkin_to_atu"), ("berezkin", "tmi", "berezkin_to_tmi")]
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


def _lexical_pairs(id2i: dict) -> set:
    pairs = set()
    adj = store.load_parallels().get("adjacency", {})
    for src, by in adj.items():
        for mid, lst in by.items():
            i = id2i.get(f"{src}:{mid}")
            if i is None:
                continue
            for e in lst:
                j = id2i.get(f"{e['index']}:{e['id']}")
                if j is not None:
                    pairs.add((min(i, j), max(i, j)))
    return pairs


def _embed(texts: list[str], cache):
    import numpy as np
    if cache and cache.exists():
        E = np.load(cache)
        if len(E) == len(texts):
            logger.info("      reusing cached embeddings %s", tuple(E.shape))
            return E
    from sentence_transformers import SentenceTransformer
    logger.info("      encoding %d motifs with %s (this is the slow part)…", len(texts), MODEL)
    m = SentenceTransformer(MODEL)
    m.max_seq_length = MAX_SEQ
    E = m.encode(texts, batch_size=32, normalize_embeddings=True,
                 convert_to_numpy=True).astype(np.float32)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache, E)
    return E


def build() -> dict | None:
    """Compute the semantic-parallel adjacency, or ``None`` if BGE-M3 is unavailable."""
    try:
        import numpy as np  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError:
        logger.info("      sentence-transformers not installed — skipping semantic layer")
        return None
    import numpy as np

    docs = _collect()
    if not docs:
        return None
    idx = np.array([d[0] for d in docs])
    id2i = {f"{x}:{c}": i for i, (x, c, _, _) in enumerate(docs)}
    byidx = {x: np.where(idx == x)[0] for x in ("tmi", "atu", "berezkin")}

    E = _embed([d[3] for d in docs], store.raw_dir() / "bge_m3.npy")
    confirmed = _confirmed_pairs(id2i)
    lexical = _lexical_pairs(id2i)

    # top-K neighbours in each *other* index, above threshold, not already linked
    pairs = {}   # (i,j) -> sim
    for i in range(len(docs)):
        xi = idx[i]
        for tx in ("tmi", "atu", "berezkin"):
            if tx == xi:
                continue
            cand = byidx[tx]
            sims = E[cand] @ E[i]
            for r in np.argsort(-sims)[:TOPK]:
                s = float(sims[r])
                if s < THRESH:
                    break
                j = int(cand[r])
                key = (min(i, j), max(i, j))
                if key not in confirmed:
                    pairs[key] = max(pairs.get(key, 0.0), s)

    adjacency = {"tmi": {}, "atu": {}, "berezkin": {}}
    for (i, j), s in pairs.items():
        al = (i, j) in lexical
        for a, b in ((i, j), (j, i)):
            xa, ca, _, _ = docs[a]
            xb, cb, _, _ = docs[b]
            adjacency[xa].setdefault(ca, []).append(
                {"index": xb, "id": cb, "sim": round(s, 3), "also_lexical": al})
    for by in adjacency.values():
        for lst in by.values():
            lst.sort(key=lambda e: -e["sim"])
            del lst[CAP:]

    npair = len(pairs)
    counts = {
        "pairs": npair,
        "also_lexical": sum(1 for k in pairs if k in lexical),
        "novel_only": sum(1 for k in pairs if k not in lexical),
    }
    logger.info("      semantic parallels: %d pairs (%d new beyond lexical)",
                npair, counts["novel_only"])
    return {"params": {"model": MODEL, "threshold": THRESH, "topk": TOPK, "cap": CAP},
            "counts": counts, "adjacency": adjacency}
