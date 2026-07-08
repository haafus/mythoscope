"""Combined tradition → motif biclustering: mockups 05 and 06 in one view.

The "All" view is the cross-cutting co-clustering over *all three* indexes at
once (mockup 05); the Berezkin / Thompson / ATU views are each catalogue's own
motif × tradition table co-clustered on its own (mockup 06). One data.js, keyed
by view, drives a single page where "All" is the first tab in the index row.

Run from repo root:  python mockups/07-tradition-motif-combined/build_data.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOCKS = ROOT / "mockups"
OUT = Path(__file__).resolve().parent / "data.js"

sys.path.insert(0, str(ROOT / "src"))
from motifs.sources.culture_dict import canonical  # noqa: E402

# Normalise TMI's free-text culture labels via the curated pipeline dictionary
# (merges Icel.->Icelandic, China->Chinese, strips "(sub-area)"/"Cf." etc.) for
# the "all" and "tmi" views. Berezkin/ATU labels are left untouched.
def tmi_norm(label):
    return canonical(label)[0]


def load_mod(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    m05 = load_mod("05-tradition-motif-mapping/build_data.py", "m05_build")
    m06 = load_mod("06-per-index-biclusters/build_data.py", "m06_build")

    data = {"all": m05.build(tmi_norm=tmi_norm)}
    for ix in ("brz", "tmi", "atu"):
        data[ix] = m06.bicluster(ix, tmi_norm=tmi_norm if ix == "tmi" else None)

    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")

    a = data["all"]
    print(f"[all] motifs={a['n_motifs_total']} traditions={a['n_traditions']} "
          f"clusters={len(a['clusters'])} by_index={a['by_index_total']}")
    for ix in ("brz", "tmi", "atu"):
        d = data[ix]
        print(f"[{ix}] motifs={d['n_motifs']} traditions={d['n_traditions']} clusters={len(d['clusters'])}")
    print(f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
