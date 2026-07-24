#!/usr/bin/env python3
"""Reproduce the cross-index textual-parallel analysis (archival / exploratory).

This is the standalone script that produced the CSVs and report in this folder.
It scans every pair of motif indexes (Berezkin / TMI / ATU), matches titles and
descriptions with a two-signal TF-IDF scheme, subtracts the pairs already linked
in the cross-walk, and writes the residual — look-alike motifs with **no recorded
link** — as CSVs plus a markdown report, both tiered by confidence.

The *productionised* generator that feeds the on-page "Possible parallels" panel
lives in ``src/motifs/parallels.py`` (build step ``[5/5]`` → ``parallels.json``);
it keeps only the high-confidence tier. This script keeps both tiers for review.

Run (from the repo root, after ``mytho build motifs`` has built the indexes)::

    PYTHONPATH=src python3 docs/motifs/crosswalk/find_parallels.py

Requires scikit-learn (a declared project dependency).
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from motifs import store

OUT = Path(__file__).parent
T_TITLE, T_DOC_HIGH, T_TITLE_SOFT, T_DOC_FLOOR, K = 0.50, 0.72, 0.30, 0.35, 8
_WS = re.compile(r"\s+")
_TOK = re.compile(r"[a-z]+")
_STOP = set(ENGLISH_STOP_WORDS) | {"origin", "why", "man", "woman", "animal", "animals"}


def norm(*p):
    return _WS.sub(" ", " ".join(x for x in p if x)).strip()


def content_tokens(title):
    toks = {t[:-1] if t.endswith("s") and len(t) > 3 else t for t in _TOK.findall(title.lower())}
    return {t for t in toks if t not in _STOP and len(t) > 2}


def build_docs(recs, nf, df):
    out = []
    for r in recs:
        title = (r.get(nf) or "").strip()
        if len(title) < 3:
            continue
        out.append({"id": r["id"], "title": title,
                    "doc": norm(title, title, title, (r.get(df) or "").strip()), "ttl": title})
    return out


def main():
    bz, tmi, atu = store.load_index("berezkin"), store.load_index("tmi"), store.load_index("atu")
    cw = store.load_crosswalk()
    DOCS = {"BZ": build_docs(bz["motifs"], "name", "definition"),
            "TMI": build_docs(tmi["motifs"], "name", "definition"),
            "ATU": build_docs(atu["types"], "name", "summary")}

    docV = TfidfVectorizer(stop_words="english", strip_accents="unicode",
                           ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    ttlV = TfidfVectorizer(stop_words="english", strip_accents="unicode",
                           ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    alld = DOCS["BZ"] + DOCS["TMI"] + DOCS["ATU"]
    docV.fit(d["doc"] for d in alld)
    ttlV.fit(d["ttl"] for d in alld)
    Xd = {k: docV.transform(d["doc"] for d in v) for k, v in DOCS.items()}
    Xt = {k: ttlV.transform(d["ttl"] for d in v) for k, v in DOCS.items()}

    def atu_tmi_edges():
        s = set()
        for key in ("atu_to_tmi", "atu_to_tmi_defining", "atu_to_tmi_note", "atu_to_tmi_summary"):
            for a, ms in cw.get(key, {}).items():
                s.update((a, m) for m in ms)
        return s
    EDGES = {("ATU", "TMI"): atu_tmi_edges(),
             ("BZ", "ATU"): ({(b, a) for b, xs in cw.get("berezkin_to_atu", {}).items() for a in xs}
                             | {(b, a) for a, xs in cw.get("atu_to_berezkin", {}).items() for b in xs}),
             ("BZ", "TMI"): {(b, m) for b, xs in cw.get("berezkin_to_tmi", {}).items() for m in xs}}

    def linked(A, B, ida, idb):
        return (ida, idb) in EDGES[(A, B)] if (A, B) in EDGES else (idb, ida) in EDGES[(B, A)]

    def candidates(A, B):
        nn = NearestNeighbors(n_neighbors=min(K, Xd[B].shape[0]), metric="cosine",
                              algorithm="brute").fit(Xd[B])
        dist, idx = nn.kneighbors(Xd[A])
        dsim = 1.0 - dist
        out = {}
        for i in range(len(DOCS[A])):
            for r in range(idx.shape[1]):
                ds = float(dsim[i, r])
                if ds < T_DOC_FLOOR:
                    break
                j = int(idx[i, r])
                ts = float(Xt[A][i].multiply(Xt[B][j]).sum())
                if not (ts >= T_TITLE or (ds >= T_DOC_HIGH and ts >= T_TITLE_SOFT)):
                    continue
                if linked(A, B, DOCS[A][i]["id"], DOCS[B][j]["id"]):
                    continue
                sh = len(content_tokens(DOCS[A][i]["title"]) & content_tokens(DOCS[B][j]["title"]))
                tier = "A" if (sh >= 2 or ds >= 0.75) else "B"
                out[(DOCS[A][i]["id"], DOCS[B][j]["id"])] = (max(ts, ds), ts, ds, i, j, sh, tier)
        return out

    PAIRS = [("ATU", "TMI"), ("BZ", "TMI"), ("BZ", "ATU")]
    results = {p: candidates(*p) for p in PAIRS}
    for A, B in PAIRS:
        rows = sorted(results[(A, B)].items(), key=lambda kv: (kv[1][6], -kv[1][0]))
        with open(OUT / f"parallels_{A}_{B}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["tier", f"{A}_id", f"{A}_title", f"{B}_id", f"{B}_title", "title_sim", "doc_sim", "shared"])
            for (aid, bid), (_sc, ts, ds, i, j, sh, tier) in rows:
                w.writerow([tier, aid, DOCS[A][i]["title"], bid, DOCS[B][j]["title"], f"{ts:.3f}", f"{ds:.3f}", sh])
        nA = sum(1 for v in results[(A, B)].values() if v[6] == "A")
        print(f"{A}~{B}: {len(results[(A, B)])} candidates ({nA} tier-A)")


if __name__ == "__main__":
    main()
