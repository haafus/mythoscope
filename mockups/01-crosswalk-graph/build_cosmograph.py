"""Export the whole cross-walk graph to Cosmograph CSV format (the full graph,
not an ego neighbourhood — Cosmograph's WebGL engine handles 20k+ nodes easily).

Reads the already-built data.js (run build_data.py first) and writes two CSVs
that cosmograph.app consumes directly:

- cosmograph-links.csv : source, target, type, confidence
- cosmograph-nodes.csv : id, label, name, index, cluster, degree

Open in Cosmograph either by uploading both files at https://cosmograph.app/run/
or, if the CSVs are hosted at public URLs, via a query-string link:
  https://cosmograph.app/run/?data=<LINKS_URL>&meta=<NODES_URL>
      &source=source&target=target&nodeColor=index&nodeSize=degree

Run from repo root:  python mockups/01-crosswalk-graph/build_cosmograph.py
"""
import csv
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.js"


def main():
    txt = DATA.read_text(encoding="utf-8")
    d = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    nodes, edges = d["nodes"], d["edges"]

    deg = Counter()
    for e in edges:
        deg[e["s"]] += 1
        deg[e["t"]] += 1

    with open(HERE / "cosmograph-links.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "type", "confidence"])
        for e in edges:
            w.writerow([e["s"], e["t"], e["m"], e.get("w", 1)])

    with open(HERE / "cosmograph-nodes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "label", "name", "index", "cluster", "degree"])
        for n in nodes:
            cl = n.get("cl") or []
            w.writerow([n["id"], n["c"], n.get("n", n["c"]), n["x"],
                        cl[0] if cl else -1, deg.get(n["id"], 0)])

    print(f"cosmograph-links.csv : {len(edges)} links")
    print(f"cosmograph-nodes.csv : {len(nodes)} nodes")
    for name in ("cosmograph-links.csv", "cosmograph-nodes.csv"):
        print(f"  {name}  ~{(HERE / name).stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
