"""Heuristic textual parallels between the three motif indexes.

A *suggestion* layer, deliberately kept apart from the curated cross-walk
(`crosswalk.py`): it lexically matches motif titles and descriptions across
Berezkin / TMI / ATU and surfaces the pairs that look parallel but carry **no
recorded link**. These are hints for a human to confirm, not asserted edges.

Method — two TF-IDF signals in one shared space:

- **title** similarity (cosine) is the precision gate — near-identical labels;
- **doc** similarity (title ×3 + description) adds recall.

A pair is a candidate when its title similarity clears a high bar, or its doc
similarity is very high with a softer title floor. Every pair already present in
the cross-walk (constituent / defining / note / summary for ATU↔TMI, ``atu_refs``
for Berezkin↔ATU, ``tmi_refs`` for Berezkin↔TMI) is subtracted. Only the
high-confidence tier (≥2 shared content words in the title, or a very strong doc
match) reaches the page layer; the fuller list lives in ``docs/motifs/crosswalk/``.

Depends on scikit-learn (a declared project dependency); if it is somehow absent
the build logs a skip and no ``parallels.json`` is written — the pages then simply
omit the section.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Gate thresholds (see module docstring); tuned on the built indexes.
T_TITLE = 0.50       # near-identical title
T_DOC_HIGH = 0.72    # very strong combined match even if the title is softer
T_TITLE_SOFT = 0.30
T_DOC_FLOOR = 0.35   # below this a neighbour is never considered
K_NEIGHBOURS = 8     # nearest neighbours examined per query record
MAX_PER_MOTIF = 12   # cap suggestions shown on a single page

_WS = re.compile(r"\s+")
_TOK = re.compile(r"[a-z]+")


def _norm(*parts: str) -> str:
    return _WS.sub(" ", " ".join(p for p in parts if p)).strip()


def _records(recs: list[dict], name_f: str, def_f: str) -> list[dict]:
    out = []
    for r in recs:
        title = (r.get(name_f) or "").strip()
        if len(title) < 3:
            continue
        desc = (r.get(def_f) or "").strip()
        out.append({"id": r["id"], "title": title,
                    "doc": _norm(title, title, title, desc), "ttl": title})
    return out


def build(berezkin_motifs: list[dict], tmi_motifs: list[dict],
          atu_types: list[dict], crosswalk: dict) -> dict | None:
    """Return the textual-parallels artifact, or ``None`` if sklearn is missing."""
    try:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
        from sklearn.neighbors import NearestNeighbors
    except ImportError as exc:  # pragma: no cover - sklearn is a declared dep
        logger.warning("      textual parallels SKIPPED (scikit-learn unavailable: %s)", exc)
        return None

    docs = {
        "berezkin": _records(berezkin_motifs, "name", "definition"),
        "tmi": _records(tmi_motifs, "name", "definition"),
        "atu": _records(atu_types, "name", "summary"),
    }
    if not (docs["tmi"] and docs["atu"]):
        return None

    stop = set(ENGLISH_STOP_WORDS) | {"origin", "why", "man", "woman", "animal", "animals"}

    def content_tokens(title: str) -> set[str]:
        toks = {t[:-1] if t.endswith("s") and len(t) > 3 else t for t in _TOK.findall(title.lower())}
        return {t for t in toks if t not in stop and len(t) > 2}

    docV = TfidfVectorizer(stop_words="english", strip_accents="unicode",
                           ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    ttlV = TfidfVectorizer(stop_words="english", strip_accents="unicode",
                           ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    all_docs = docs["berezkin"] + docs["tmi"] + docs["atu"]
    docV.fit(d["doc"] for d in all_docs)
    ttlV.fit(d["ttl"] for d in all_docs)
    Xd = {k: docV.transform(d["doc"] for d in v) for k, v in docs.items()}
    Xt = {k: ttlV.transform(d["ttl"] for d in v) for k, v in docs.items()}

    # existing cross-walk edges, so we only surface the *unlinked* parallels
    def atu_tmi_edges() -> set[tuple[str, str]]:
        s: set[tuple[str, str]] = set()
        for key in ("atu_to_tmi", "atu_to_tmi_defining", "atu_to_tmi_note", "atu_to_tmi_summary"):
            for a, ms in crosswalk.get(key, {}).items():
                s.update((a, m) for m in ms)
        return s

    edges = {
        ("atu", "tmi"): atu_tmi_edges(),
        ("berezkin", "atu"): ({(b, a) for b, xs in crosswalk.get("berezkin_to_atu", {}).items() for a in xs}
                              | {(b, a) for a, xs in crosswalk.get("atu_to_berezkin", {}).items() for b in xs}),
        ("berezkin", "tmi"): {(b, m) for b, xs in crosswalk.get("berezkin_to_tmi", {}).items() for m in xs},
    }

    def linked(a_side: str, b_side: str, a_id: str, b_id: str) -> bool:
        if (a_side, b_side) in edges:
            return (a_id, b_id) in edges[(a_side, b_side)]
        return (b_id, a_id) in edges[(b_side, a_side)]

    def candidates(a_side: str, b_side: str) -> dict[tuple[str, str], dict]:
        """Query ``a_side`` records into ``b_side``; keep unlinked tier-A parallels."""
        A, B = docs[a_side], docs[b_side]
        k = min(K_NEIGHBOURS, len(B))
        nn = NearestNeighbors(n_neighbors=k, metric="cosine", algorithm="brute").fit(Xd[b_side])
        dist, idx = nn.kneighbors(Xd[a_side])
        dsim = 1.0 - dist
        out: dict[tuple[str, str], dict] = {}
        for i in range(len(A)):
            for r in range(idx.shape[1]):
                ds = float(dsim[i, r])
                if ds < T_DOC_FLOOR:
                    break
                j = int(idx[i, r])
                ts = float(Xt[a_side][i].multiply(Xt[b_side][j]).sum())
                if not (ts >= T_TITLE or (ds >= T_DOC_HIGH and ts >= T_TITLE_SOFT)):
                    continue
                sh = len(content_tokens(A[i]["title"]) & content_tokens(B[j]["title"]))
                if not (sh >= 2 or ds >= 0.75):  # tier A only
                    continue
                if linked(a_side, b_side, A[i]["id"], B[j]["id"]):
                    continue
                out[(A[i]["id"], B[j]["id"])] = {
                    "a": A[i]["id"], "b": B[j]["id"],
                    "title_sim": round(ts, 3), "doc_sim": round(ds, 3), "shared": sh,
                    "score": round(max(ts, ds), 3)}
        return out

    pairs = {("atu", "tmi"): candidates("atu", "tmi"),
             ("berezkin", "tmi"): candidates("berezkin", "tmi"),
             ("berezkin", "atu"): candidates("berezkin", "atu")}

    # bidirectional adjacency: motif id -> [{index, id, sims}], capped and sorted
    adjacency: dict[str, dict[str, list]] = {"berezkin": {}, "tmi": {}, "atu": {}}

    def add(side: str, mid: str, other_side: str, oid: str, c: dict) -> None:
        adjacency[side].setdefault(mid, []).append(
            {"index": other_side, "id": oid, "title_sim": c["title_sim"],
             "doc_sim": c["doc_sim"], "shared": c["shared"], "score": c["score"]})

    for (a_side, b_side), cs in pairs.items():
        for c in cs.values():
            add(a_side, c["a"], b_side, c["b"], c)
            add(b_side, c["b"], a_side, c["a"], c)
    for byid in adjacency.values():
        for lst in byid.values():
            lst.sort(key=lambda e: -e["score"])
            del lst[MAX_PER_MOTIF:]

    # triangles: a Berezkin ↔ TMI ↔ ATU triple all pairwise parallel
    idx_of = {s: {d["id"]: n for n, d in enumerate(docs[s])} for s in docs}
    tmi_by_bz: dict[str, list[str]] = {}
    atu_by_bz: dict[str, list[str]] = {}
    for (b, m) in pairs[("berezkin", "tmi")]:
        tmi_by_bz.setdefault(b, []).append(m)
    for (b, a) in pairs[("berezkin", "atu")]:
        atu_by_bz.setdefault(b, []).append(a)
    triangles = []
    for b in set(tmi_by_bz) & set(atu_by_bz):
        for m in tmi_by_bz[b]:
            for a in atu_by_bz[b]:
                ai, mi = idx_of["atu"][a], idx_of["tmi"][m]
                ts = float(Xt["atu"][ai].multiply(Xt["tmi"][mi]).sum())
                ds = float(Xd["atu"][ai].multiply(Xd["tmi"][mi]).sum())
                if ts >= 0.4 or ds >= 0.6:
                    missing = [lbl for lbl, ln in (
                        ("berezkin-tmi", linked("berezkin", "tmi", b, m)),
                        ("berezkin-atu", linked("berezkin", "atu", b, a)),
                        ("atu-tmi", linked("atu", "tmi", a, m))) if not ln]
                    triangles.append({"berezkin": b, "tmi": m, "atu": a, "missing": missing,
                                      "score": round(max(ts, ds), 3)})
    triangles.sort(key=lambda t: -t["score"])

    return {
        "params": {"title_gate": T_TITLE, "doc_high": T_DOC_HIGH, "cap_per_motif": MAX_PER_MOTIF},
        "counts": {f"{a}_{b}": len(cs) for (a, b), cs in pairs.items()} | {"triangles": len(triangles)},
        "adjacency": adjacency,
        "triangles": triangles,
    }
