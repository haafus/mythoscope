"""Corpus overview dashboard — data builder.

Isolated from the pipeline: reads only the source list in ``config/corpus.json``
and the tradition tree in ``config/traditions.json``, downloads the 28 raw
Project Gutenberg texts into a gitignored ``cache/`` (following redirects), and
computes everything the overview page shows straight from those files:

  * headline totals (texts / traditions / macro-areas / words / sentences),
  * composition by macro-area,
  * a per-text catalogue with word / sentence counts,
  * a **text-similarity heatmap** — TF-IDF cosine between texts and between
    traditions, reordered by hierarchical clustering (seriation) so related
    rows sit together.

The heatmap is a *lexical* (TF-IDF) stand-in for the pipeline's BGE-M3 semantic
distances — deterministic and model-free, so the mock rebuilds anywhere. The
page labels it as such.

Run from the repo root:  python mockups/13-corpus-overview/build_data.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
OUT = HERE / "data.js"

# a stable categorical palette for the 12 macro-areas (fixed order, never cycled)
AREA_PALETTE = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
                "#3a6ea5", "#b5651d", "#7d8b3a", "#a3457e", "#4f7096", "#6b7280"]

START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)


def gutenberg_id(url: str) -> str:
    m = (re.search(r"/(\d+)/pg\d+\.txt", url) or re.search(r"epub/(\d+)", url)
         or re.search(r"/ebooks/(\d+)", url))
    return m.group(1) if m else re.sub(r"\W+", "", url)[-6:]


def fetch(url: str) -> str | None:
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"pg{gutenberg_id(url)}.txt"
    if not dest.exists() or dest.stat().st_size < 1000:
        print(f"  download {url}")
        r = subprocess.run(
            ["curl", "-sS", "-L", "--fail", "--max-time", "90", "-o", str(dest), url],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"  ! failed: {r.stderr.strip()[:120]}")
            return None
    return dest.read_text(encoding="utf-8", errors="replace")


def strip_boilerplate(text: str) -> str:
    s = START.search(text)
    body = text[s.end():] if s else text
    e = END.search(body)
    if e:
        body = body[: e.start()]
    return body.strip("\n")


def count_words(t: str) -> int:
    return len(re.findall(r"\b[^\W\d_][\w'-]*\b", t))


def count_sentences(t: str) -> int:
    return len(re.findall(r"[.!?]+(?=\s|$)", t)) or 1


# --------------------------------------------------------------------------- #
# tradition tree: tradition -> {major, color}
# --------------------------------------------------------------------------- #
def flatten_traditions(tree: dict) -> dict:
    out = {}

    def walk(node):
        if not isinstance(node, dict):
            return
        for key, val in node.items():
            if isinstance(val, dict) and "traditions" in val:
                for trad, info in val["traditions"].items():
                    out[trad] = {"major": key, "color": info.get("color", "#6b7280")}
            elif isinstance(val, dict):
                walk(val)

    walk(tree)
    return out


def seriate(sim: np.ndarray) -> list[int]:
    """Leaf order from average-linkage clustering of the distance (1 - sim)."""
    n = sim.shape[0]
    if n < 3:
        return list(range(n))
    d = 1.0 - sim
    np.fill_diagonal(d, 0.0)
    d = (d + d.T) / 2
    z = linkage(squareform(d, checks=False), method="average")
    return [int(i) for i in leaves_list(z)]


def heatmap(labels, colors, vectors, extra=None):
    sim = cosine_similarity(vectors)
    np.clip(sim, 0.0, 1.0, out=sim)
    order = seriate(sim)
    block = {
        "labels": labels,
        "colors": colors,
        "order": order,
        "sim": [[round(float(x), 3) for x in row] for row in sim],
    }
    if extra:
        block.update(extra)
    return block


def main():
    books_cfg = json.loads((ROOT / "config" / "corpus.json").read_text(encoding="utf-8"))
    tinfo = flatten_traditions(json.loads((ROOT / "config" / "traditions.json").read_text(encoding="utf-8")))

    books, corpus_texts = [], []
    print(f"corpus: {len(books_cfg)} texts")
    for b in books_cfg:
        raw = fetch(b["url"])
        if raw is None:
            print(f"[skip] {b['title']}")
            continue
        body = strip_boilerplate(raw)
        ti = tinfo.get(b["tradition"], {"major": "Other", "color": "#6b7280"})
        books.append({
            "title": b["title"], "tradition": b["tradition"], "major": ti["major"],
            "color": ti["color"], "desc": b.get("description", ""),
            "words": count_words(body), "sentences": count_sentences(body), "chars": len(body),
        })
        corpus_texts.append(body)

    # ---- headline + composition ------------------------------------------- #
    areas_order = sorted({b["major"] for b in books})
    area_color = {a: AREA_PALETTE[i % len(AREA_PALETTE)] for i, a in enumerate(areas_order)}
    # traditions carry no colour in config; colour every text by its macro-area so
    # the size bars and heatmap ticks read as regional groups (matches composition).
    for b in books:
        b["color"] = area_color[b["major"]]
    areas = []
    for a in areas_order:
        rows = [b for b in books if b["major"] == a]
        areas.append({"name": a, "color": area_color[a],
                      "texts": len(rows), "words": sum(r["words"] for r in rows)})
    areas.sort(key=lambda x: -x["words"])

    stats = {
        "texts": len(books),
        "traditions": len({b["tradition"] for b in books}),
        "areas": len(areas_order),
        "words": sum(b["words"] for b in books),
        "sentences": sum(b["sentences"] for b in books),
        "chars": sum(b["chars"] for b in books),
    }

    # ---- TF-IDF similarity: text x text and tradition x tradition ---------- #
    tfidf = TfidfVectorizer(stop_words="english", max_features=40000,
                            sublinear_tf=True, min_df=1)
    X = tfidf.fit_transform(corpus_texts)          # 28 x V

    text_heat = heatmap(
        [b["title"] for b in books],
        [b["color"] for b in books],
        X,
        extra={"traditions": [b["tradition"] for b in books]},
    )

    trad_names = sorted({b["tradition"] for b in books})
    Xd = X.toarray()
    trad_vecs = np.vstack([Xd[[i for i, b in enumerate(books) if b["tradition"] == t]].mean(axis=0)
                           for t in trad_names])
    trad_color = {b["tradition"]: b["color"] for b in books}
    trad_heat = heatmap(trad_names, [trad_color[t] for t in trad_names], trad_vecs)

    books.sort(key=lambda b: (b["major"], b["tradition"], b["title"]))
    data = {"stats": stats, "areas": areas, "books": books,
            "heat": {"tradition": trad_heat, "text": text_heat}}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")

    print(f"\n{stats['texts']} texts · {stats['traditions']} traditions · {stats['areas']} areas · "
          f"{stats['words']:,} words")
    print(f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    sys.exit(main())
