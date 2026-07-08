#!/usr/bin/env python
"""Grid experiment: how should we embed motifs to match them against source texts?

Gold set = Ashliman's folktale pages, each ``type{N}.html`` a set of real tales that
instantiate ATU type N (label leakage — "Aarne-Thompson type N", editor boilerplate —
is stripped). For every tale we rank *all* ATU types by embedding similarity and score
whether the true type lands near the top (recall@k, MRR).

Two axes (the questions from the design discussion):
  A. what goes in the MOTIF embedding — name / +summary / +hierarchy path
  B. how the TEXT is represented — whole tale (one vector) / passage chunks (max-sim)

Optional third axis (--llm): decompose each tale into scene statements with an LLM and
match those; off by default (needs an API key + the project's LLM config).

    PYTHONPATH=src .venv/bin/python mockups/motif-text-embedding-eval/run.py \
        --model BAAI/bge-m3 --max-tales 400

Relative ordering is the deliverable; swap --model to compare backbones. Writes
results.json + report.html next to this file.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from motifs import store  # noqa: E402

HERE = Path(__file__).resolve().parent
KS = (1, 5, 10)

# ---------------------------------------------------------------- gold set ----
_TAG = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
_LEAK = re.compile(r"(?im)^.*(aarne|thompson|uther|\bAT[U]?\b|\btype\s+\d).*$")
_BOILER = re.compile(r"(?i)(return to|back to|revised:|edited by|d\. l\. ashliman|copyright|professor emeritus).*")


def _strip_html(s: str) -> str:
    s = _TAG.sub(" ", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", s).strip()


def _clean_tale(t: str) -> str:
    t = _LEAK.sub("", t)
    t = _BOILER.sub("", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _fid(name: str) -> str | None:
    m = re.match(r"type0*([0-9]+[A-Za-z*]*)\.html$", name)
    return m.group(1) if m else None


def load_gold(type_ids: set[str]) -> list[tuple[str, str]]:
    """(atu_id, tale_text) for every anchor-delimited tale on a cached type page."""
    root = Path(store.raw_dir()) / "ashliman"
    gold: list[tuple[str, str]] = []
    for p in sorted(root.glob("type*.html")):
        aid = _fid(p.name)
        if aid is None or aid not in type_ids:
            continue
        parts = re.split(r'(?i)<a\s+name="([^"]+)"', p.read_text(errors="ignore"))
        for i in range(1, len(parts) - 1, 2):
            anchor, seg = parts[i].lower(), parts[i + 1]
            if anchor in ("contents", "top", "nav"):
                continue
            text = _clean_tale(_strip_html(seg))
            if len(text) >= 300:
                gold.append((aid, text))
    return gold


# ------------------------------------------------------ representations ----
def motif_texts(types: list[dict], variant: str) -> list[str]:
    out = []
    for t in types:
        name = t.get("name", "") or t["id"]
        summ = (t.get("summary") or "")[:600]
        path = " · ".join(x for x in (t.get("chapter"), t.get("division"), t.get("sub_division")) if x)
        if variant == "name":
            out.append(name)
        elif variant == "name+summary":
            out.append(f"{name}. {summ}".strip())
        else:  # name+summary+hierarchy
            out.append(f"{path} — {name}. {summ}".strip(" —"))
    return out


def chunk(text: str, words: int = 70, stride: int = 50) -> list[str]:
    """Passages: paragraphs, windowed if long. Keeps each chunk aligned with fewer motifs."""
    chunks: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        w = para.split()
        if len(w) <= words:
            if len(w) >= 8:
                chunks.append(para.strip())
        else:
            for i in range(0, len(w), stride):
                seg = " ".join(w[i:i + words])
                if len(seg.split()) >= 8:
                    chunks.append(seg)
    return chunks[:16] or [text[:600]]


# ----------------------------------------------------------------- eval ----
def _norm(m: np.ndarray) -> np.ndarray:
    return m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)


def cap_candidates(types, gold, max_candidates):
    """Keep every gold type, then fill up to max_candidates with deterministic
    distractors — lets a heavy model finish while staying a real retrieval task."""
    if not max_candidates or len(types) <= max_candidates:
        return types
    gold_ids = {a for a, _ in gold}
    keep = [t for t in types if t["id"] in gold_ids]
    others = [t for t in types if t["id"] not in gold_ids]
    room = max(0, max_candidates - len(keep))
    step = max(1, len(others) // room) if room else 1
    return keep + others[::step][:room]


def score_grid(model, types, gold, max_tales):
    ids = [t["id"] for t in types]
    id_pos = {tid: i for i, tid in enumerate(ids)}
    if max_tales and len(gold) > max_tales:  # deterministic stride subsample
        gold = gold[:: max(1, len(gold) // max_tales)][:max_tales]

    def enc(xs):
        return _norm(np.asarray(model.encode(xs, batch_size=64, show_progress_bar=False)))

    # candidate (motif) embeddings, once per variant
    cand = {v: enc(motif_texts(types, v)) for v in ("name", "name+summary", "name+summary+hierarchy")}

    # tale reps, once
    whole = enc([t for _, t in gold])
    tale_chunks = [chunk(t) for _, t in gold]
    flat, spans = [], []
    for ch in tale_chunks:
        spans.append((len(flat), len(flat) + len(ch)))
        flat.extend(ch)
    chunk_emb = enc(flat)

    results = {}
    for mv, C in cand.items():
        for tv in ("whole", "chunks"):
            ranks = []
            for gi, (aid, _) in enumerate(gold):
                if tv == "whole":
                    sims = C @ whole[gi]
                else:
                    a, b = spans[gi]
                    sims = (C @ chunk_emb[a:b].T).max(axis=1)
                order = np.argsort(-sims)
                rank = int(np.where(order == id_pos[aid])[0][0]) + 1
                ranks.append(rank)
            ranks = np.asarray(ranks)
            results[f"{mv} × {tv}"] = {
                "mrr": round(float(np.mean(1.0 / ranks)), 4),
                **{f"recall@{k}": round(float(np.mean(ranks <= k)), 4) for k in KS},
                "median_rank": int(np.median(ranks)),
            }
    return results, len(gold), len(ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--max-tales", type=int, default=400)
    ap.add_argument("--max-candidates", type=int, default=None,
                    help="Cap distractor types (keeps all gold) so a heavy model finishes.")
    args = ap.parse_args()

    types_all = (store.load_index("atu") or {}).get("types", [])
    gold = load_gold({t["id"] for t in types_all})
    types = cap_candidates(types_all, gold, args.max_candidates)
    if len(types) < len(types_all):
        print(f"[note] candidates capped {len(types_all)} → {len(types)} (all gold kept + distractor sample)")
    print(f"gold: {len(gold)} tales / {len({a for a, _ in gold})} ATU types; candidates: {len(types)} types")
    print(f"loading model {args.model} …")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)

    results, n_tales, n_cand = score_grid(model, types, gold, args.max_tales)

    hdr = ["config", "recall@1", "recall@5", "recall@10", "MRR", "med.rank"]
    rows = [[cfg, r["recall@1"], r["recall@5"], r["recall@10"], r["mrr"], r["median_rank"]]
            for cfg, r in sorted(results.items(), key=lambda kv: -kv[1]["recall@5"])]
    w = [max(len(str(x)) for x in [h] + [row[i] for row in rows]) for i, h in enumerate(hdr)]

    def line(vals):
        return "  ".join(str(v).ljust(w[i]) for i, v in enumerate(vals))

    print(f"\nModel {args.model} · {n_tales} tales · {n_cand} candidate types\n")
    print(line(hdr)); print(line(["-" * x for x in w]))
    for row in rows:
        print(line(row))

    out = {"model": args.model, "tales": n_tales, "candidates": n_cand, "results": results}
    (HERE / "results.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {HERE / 'results.json'}")


if __name__ == "__main__":
    main()
