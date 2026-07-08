"""Extract the confirmed cross-walk graph into a compact data.js for the mockup.

Nodes are motifs/types across the three indexes (id namespaced by index), edges
carry the linking *method* (constituent / defining / note / summary / berezkin /
inferred). Only nodes that take part in at least one edge are emitted.

Run from the repo root:  python mockups/01-crosswalk-graph/build_data.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"


def load(name):
    return json.load(open(ROOT / "outputs" / "motifs" / name, encoding="utf-8"))


def main():
    cw = load("crosswalk.json")
    names = {}
    for idx, fname, key in (("tmi", "tmi.json", "motifs"),
                            ("atu", "atu.json", "types"),
                            ("brz", "berezkin.json", "motifs")):
        for r in load(fname).get(key, []):
            names[f"{idx}:{r['id']}"] = r.get("name") or r.get("id")

    # Forward maps only (reverse maps are literal mirrors), tagged by method.
    # `rev` flips the stored arrow so it points along the *semantic* direction of
    # the link (who references / contains whom), matching the legend's ⇒ marks:
    #   constituent/defining/summary : ATU → TMI   (a type points to its motifs)
    #   note                         : TMI → ATU   (a TMI note cites the type)
    #   berezkin                     : Berezkin → ATU/TMI (its citation)
    FORWARD = [
        ("atu", "tmi", "atu_to_tmi", "constituent", False),
        ("atu", "tmi", "atu_to_tmi_defining", "defining", False),
        ("atu", "tmi", "atu_to_tmi_note", "note", True),
        ("atu", "tmi", "atu_to_tmi_summary", "summary", False),
        ("brz", "atu", "berezkin_to_atu", "berezkin", False),
        ("brz", "tmi", "berezkin_to_tmi", "berezkin", False),
    ]
    edges = {}  # frozenset(a,b) -> {method: (src, tgt)}  (directed per method)

    def add(src, tgt, method):
        if src == tgt:
            return
        edges.setdefault(frozenset((src, tgt)), {})[method] = (src, tgt)

    for left, right, mapname, method, rev in FORWARD:
        for lid, rids in (cw.get(mapname) or {}).items():
            a = f"{left}:{lid}"
            for rid in rids:
                b = f"{right}:{rid}"
                add(b, a, method) if rev else add(a, b, method)

    # Transitive-closure ("inferred") edges: symmetric triangle closure, undirected.
    IDX = {"tmi": "tmi", "atu": "atu", "berezkin": "brz"}
    for side, byid in (cw.get("inferred") or {}).items():
        for lid, links in byid.items():
            a = f"{IDX[side]}:{lid}"
            for e in links:
                add(a, f"{IDX[e['index']]}:{e['id']}", "inferred")

    used = set()
    edge_list = []
    # Pick the single "strongest" method for colouring + direction (confirmed over inferred).
    order = ["constituent", "defining", "note", "summary", "berezkin", "inferred"]
    for methmap in edges.values():
        m = min(methmap, key=order.index)
        src, tgt = methmap[m]
        used.add(src); used.add(tgt)
        # `d` = directed: inferred (symmetric) draws no arrow, the rest point src→tgt.
        edge_list.append({"s": src, "t": tgt, "m": m, "d": m != "inferred"})

    # Every node that takes part in at least one cross-walk edge — the complete
    # connected set across all three indexes, not a sample.
    node_list = [{"id": n, "x": n.split(":", 1)[0], "c": n.split(":", 1)[1],
                  "n": names.get(n, n.split(":", 1)[1])}
                 for n in sorted(used)]

    data = {"nodes": node_list, "edges": edge_list}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    deg = {}
    for e in edge_list:
        deg[e["s"]] = deg.get(e["s"], 0) + 1
        deg[e["t"]] = deg.get(e["t"], 0) + 1
    top = sorted(deg.items(), key=lambda kv: -kv[1])[:5]
    print(f"nodes={len(node_list)} edges={len(edge_list)}  ~{OUT.stat().st_size//1024}KB"
          if OUT.exists() else "")
    print("busiest hubs:", [(n, d, names.get(n, "")[:24]) for n, d in top])


if __name__ == "__main__":
    main()
