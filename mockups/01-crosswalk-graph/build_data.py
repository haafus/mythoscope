"""Extract the cross-walk graph + all suggestion layers into a compact data.js.

Nodes are motifs/types across the three indexes (id namespaced by index). Edges
carry a linking *method* across two tiers:

- **confirmed cross-walk** — constituent / defining / note / summary / berezkin,
  drawn directed (source → target along the citation/containment direction);
- **suggestions / parallels** — near-identical + lexical (from `parallels.json`),
  reasoned (the curated mytheme groups), semantic (BGE-M3, `semantic_parallels.json`)
  and inferred (transitive triangle closure) — drawn undirected.

Each edge keeps a single strongest method for one drawn line. The front colours
edges by their **source** index and finds **dense clusters** with Louvain
community detection over the confirmed graph (each node gets a cluster id).

Run from the repo root:  python mockups/01-crosswalk-graph/build_data.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"
sys.path.insert(0, str(ROOT / "src"))

import networkx as nx  # noqa: E402
from networkx.algorithms.community import louvain_communities  # noqa: E402

# adjacency / reasoned use full index names; node ids use short prefixes
PFX = {"berezkin": "brz", "tmi": "tmi", "atu": "atu"}
NEAR_TITLE = 0.9  # title-similarity band that reads as "near-identical"
# "confirmed" = asserted links (cross-index cross-walk + intra-index references);
# drawn solid with an arrow, no confidence weight. Intra-index refs split by kind:
# seealso (TMI cf/ref + Berezkin see-also), combo (ATU), subtype (ATU hierarchy).
CONFIRMED = {"constituent", "defining", "note", "summary", "berezkin",
             "seealso", "combo", "subtype"}
# the confirmed clustering excludes subtypes (hierarchical, off by default on the front)
CL_CONFIRMED = CONFIRMED - {"subtype"}
# strongest → weakest, for picking the one method a shared pair is drawn as
ORDER = ["constituent", "defining", "note", "summary", "berezkin",
         "seealso", "combo", "subtype",
         "near", "reasoned", "lexical", "semantic", "inferred"]


def load(name):
    return json.load(open(ROOT / "outputs" / "motifs" / name, encoding="utf-8"))


def main():
    cw = load("crosswalk.json")
    names, idx_rows, valid = {}, {}, {}
    for idx, fname, key in (("tmi", "tmi.json", "motifs"),
                            ("atu", "atu.json", "types"),
                            ("brz", "berezkin.json", "motifs")):
        rows = load(fname).get(key, [])
        idx_rows[idx] = rows
        valid[idx] = {r["id"] for r in rows}
        for r in rows:
            names[f"{idx}:{r['id']}"] = r.get("name") or r.get("id")

    edges = {}  # frozenset(a,b) -> {method: (src, tgt, conf)}  (directed + confidence)

    def add(src, tgt, method, conf=1.0):
        if src != tgt:
            edges.setdefault(frozenset((src, tgt)), {})[method] = (src, tgt, conf)

    # 1) confirmed cross-walk. `rev` flips the arrow to the semantic direction
    #    (constituent/defining/summary ATU→TMI, note TMI→ATU, berezkin Berezkin→other).
    FORWARD = [
        ("atu", "tmi", "atu_to_tmi", "constituent", False),
        ("atu", "tmi", "atu_to_tmi_defining", "defining", False),
        ("atu", "tmi", "atu_to_tmi_note", "note", True),
        ("atu", "tmi", "atu_to_tmi_summary", "summary", False),
        ("brz", "atu", "berezkin_to_atu", "berezkin", False),
        ("brz", "tmi", "berezkin_to_tmi", "berezkin", False),
    ]
    for left, right, mapname, method, rev in FORWARD:
        for lid, rids in (cw.get(mapname) or {}).items():
            a = f"{left}:{lid}"
            for rid in rids:
                b = f"{right}:{rid}"
                add(b, a, method) if rev else add(a, b, method)

    # Each suggestion edge carries a confidence in [0,1] (front maps it to opacity).
    # 2) inferred (symmetric triangle closure) — structural, no numeric score
    for side, byid in (cw.get("inferred") or {}).items():
        for lid, links in byid.items():
            a = f"{PFX[side]}:{lid}"
            for e in links:
                add(a, f"{PFX[e['index']]}:{e['id']}", "inferred", 0.5)

    # 3) lexical parallels — near-identical (title-overlap band) + broader lexical
    for sidx, byid in load("parallels.json")["adjacency"].items():
        for sid, lst in byid.items():
            a = f"{PFX[sidx]}:{sid}"
            for e in lst:
                m = "near" if e.get("title_sim", 0) >= NEAR_TITLE else "lexical"
                add(a, f"{PFX[e['index']]}:{e['id']}", m, e.get("score", e.get("title_sim", 0.5)))

    # 4) semantic parallels (BGE-M3) — cosine similarity as the score
    for sidx, byid in load("semantic_parallels.json")["adjacency"].items():
        for sid, lst in byid.items():
            a = f"{PFX[sidx]}:{sid}"
            for e in lst:
                add(a, f"{PFX[e['index']]}:{e['id']}", "semantic", e.get("sim", 0.7))

    # 5) reasoned parallels — each curated group is a clique; confidence from the group
    from motifs.reasoned_parallels import GROUPS  # noqa: E402
    for g in GROUPS:
        conf = 0.9 if g.get("confidence") == "high" else 0.7
        mem = [f"{PFX[i]}:{d}" for i, d in g["members"]]
        for i in range(len(mem)):
            for j in range(i + 1, len(mem)):
                add(mem[i], mem[j], "reasoned", conf)

    # 6) intra-index references — asserted links *inside* one index (not cross-walk),
    #    each its own toggleable type: see-also (TMI cf/ref + Berezkin), ATU
    #    combinations, ATU subtypes (hierarchy).
    for r in idx_rows["tmi"]:
        sa = r.get("see_also") or {}
        for tid in (sa.get("ref") or []) + (sa.get("cf") or []):
            if tid in valid["tmi"]:
                add(f"tmi:{r['id']}", f"tmi:{tid}", "seealso")
    for r in idx_rows["brz"]:
        for sid in (r.get("see_also") or []):
            if sid in valid["brz"]:
                add(f"brz:{r['id']}", f"brz:{sid}", "seealso")
    for r in idx_rows["atu"]:
        for cid in (r.get("combos") or []):
            if cid in valid["atu"]:
                add(f"atu:{r['id']}", f"atu:{cid}", "combo")
        for sid in (r.get("subtypes") or []):
            if sid in valid["atu"]:
                add(f"atu:{r['id']}", f"atu:{sid}", "subtype")

    used, edge_list = set(), []
    for methmap in edges.values():
        m = min(methmap, key=ORDER.index)
        src, tgt, conf = methmap[m]
        used.add(src); used.add(tgt)
        e = {"s": src, "t": tgt, "m": m, "d": m in CONFIRMED}
        if m not in CONFIRMED:
            e["w"] = round(conf, 2)     # confidence → edge opacity on the front
        edge_list.append(e)

    # ---- dense clusters: Louvain, computed two ways ----
    #   cl  : over the confirmed cross-walk graph only (the asserted structure)
    #   cl2 : over confirmed + all suggestion/parallel edges (looser, meaning-based)
    def cluster(edge_filter):
        G = nx.Graph()
        for e in edge_list:
            if edge_filter(e["m"]):
                G.add_edge(e["s"], e["t"])
        comms = sorted((c for c in louvain_communities(G, seed=0) if len(c) >= 2),
                       key=len, reverse=True)
        deg = dict(G.degree())
        node_cl, out = {}, []
        for cid, c in enumerate(comms):
            by = {"tmi": 0, "atu": 0, "brz": 0}
            for n in c:
                node_cl[n] = cid
                by[n.split(":", 1)[0]] += 1
            top = sorted(c, key=lambda n: -deg.get(n, 0))[:3]
            out.append({"id": cid, "size": len(c), "by_index": by,
                        "top": [{"id": n, "x": n.split(":", 1)[0], "c": n.split(":", 1)[1]}
                                for n in top]})
        return node_cl, out

    cl_conf, clusters = cluster(lambda m: m in CL_CONFIRMED)
    cl_all, clusters2 = cluster(lambda m: True)

    node_list = [{"id": n, "x": n.split(":", 1)[0], "c": n.split(":", 1)[1],
                  "n": names.get(n, n.split(":", 1)[1]),
                  "cl": cl_conf.get(n, -1), "cl2": cl_all.get(n, -1)}
                 for n in sorted(used)]

    data = {"nodes": node_list, "edges": edge_list,
            "clusters": clusters, "clusters2": clusters2}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")

    by_method = {}
    for e in edge_list:
        by_method[e["m"]] = by_method.get(e["m"], 0) + 1
    print(f"nodes={len(node_list)} edges={len(edge_list)} "
          f"clusters(confirmed)={len(clusters)} clusters(all)={len(clusters2)} "
          f"~{OUT.stat().st_size // 1024}KB")
    print("edges by method:", by_method)
    print("biggest confirmed clusters:", [(c["size"], c["by_index"]) for c in clusters[:5]])
    print("biggest all-links clusters:", [(c["size"], c["by_index"]) for c in clusters2[:5]])


if __name__ == "__main__":
    main()
