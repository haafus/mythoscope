"""Dated-phylogeny wiring (mockup 30, roadmap M30) — ordinal stratum -> calendar age.

The Tier-3 capability step: turn a descent motif's *ordinal* clade depth (mockup 18/19) into
an approximate **calendar age**. Two external ingredients:

  1. Glottolog (CC-BY) — each Berezkin tradition joined to its nearest Glottolog language, so
     every tradition carries a standard **family** (+ glottocode, for the full dated-tree ASR
     of M31). Cached in glottolog_join.json.
  2. A curated table of published **family expansion / time-depth** estimates (FAMILY_DATES).

A motif that is phylogenetically **clustered** (high phylo-signal — inherited, not areal) and
**concentrated in one family** is dated to that family's expansion: if it rode the family's
spread, that is roughly its age. This dates only the descent minority; the areal majority is
dated by geography (mockup 19), not here.

Honest limits: family-resolution (not node-level Bayesian dates — that's M31); the dates are
literature point-estimates with wide ranges; the coordinate join is ~52 km median but can jump
a family boundary. Ages are ranges, not claims.

Run:  python mockups/30-dated-phylogeny/build_data.py
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_TRAD = 6
N_SHUFFLE = 8
SIG_DESCENT = 0.4          # phylo-signal: inherited vs areal
CONC = 0.55                # min share of attesting traditions in the dominant family
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K57": "Cinderella", "M182": "tar-baby", "K27z2": "jātaka incest", "M29B": "trickster"}

# published family expansion / time-depth estimates (years BP), keyed by Glottolog family.
# point + rough range + note; consensus-ish from comparative linguistics (Bouckaert, Gray,
# Grollemund, Heggarty, Bowern, Kitchen…). These are *estimates with wide uncertainty*.
FAMILY_DATES = {
    "Afro-Asiatic": (9000, (8000, 12000), "deep; Africa/Near East"),
    "Nuclear Trans New Guinea": (9000, (6000, 10000), "highland NG Neolithic"),
    "Sino-Tibetan": (6500, (5500, 7500), "millet farmers, N China"),
    "Atlantic-Congo": (6000, (5000, 7000), "Niger-Congo; Bantu sub-expansion ~4000"),
    "North Caucasian": (6000, (5000, 8000), "—"),
    "Indo-European": (5500, (4500, 6500), "Steppe ~5000 / Anatolian ~8000 — debated"),
    "Austronesian": (5200, (4800, 5500), "out of Taiwan"),
    "Uto-Aztecan": (5000, (4500, 5500), "maize dispersal"),
    "Arawakan": (5000, (4000, 5500), "Amazonian expansion"),
    "Pama-Nyungan": (5000, (4000, 6000), "Australian late-Holocene spread"),
    "Tupian": (5000, (3000, 5000), "Amazonian"),
    "Dravidian": (4500, (4000, 5000), "S Asia"),
    "Uralic": (4500, (4000, 5000), "—"),
    "Austroasiatic": (4500, (4000, 5000), "SE-Asian rice farmers"),
    "Mayan": (4200, (3800, 4500), "Mesoamerica"),
    "Cariban": (3500, (3000, 4500), "Amazonian/Guiana"),
    "Algic": (3000, (2500, 4000), "Algonquian ~3000; Algic deeper"),
    "Tai-Kadai": (3000, (2500, 4000), "—"),
    "Athabaskan-Eyak-Tlingit": (2500, (2000, 5000), "Athabaskan spread ~2000; Na-Dene deeper"),
    "Turkic": (2200, (2000, 2500), "steppe expansion"),
    "Eskimo-Aleut": (2000, (2000, 4000), "Inuit-Yupik ~2000; family ~4000"),
    "Quechuan": (1500, (1000, 2000), "Andes"),
    "Mongolic-Khitan": (1000, (800, 1500), "—"),
}


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    join = json.loads((HERE / "glottolog_join.json").read_text(encoding="utf-8"))
    gfam = {t: j["gfam"] for t, j in join.items()}

    # language classification tree + Fitch (as mockup 18/27) for phylo-signal
    children, node_of, depth, leaf_of = [[]], {(): 0}, [0], {}
    for tid, v in T.items():
        path, parent = (), 0
        for lvl in (v.get("language") or ["(unknown)"]):
            path = path + (lvl,); nid = node_of.get(path)
            if nid is None:
                nid = len(children); children.append([]); depth.append(depth[parent] + 1)
                node_of[path] = nid; children[parent].append(nid)
            parent = nid
        leaf = len(children); children.append([]); depth.append(depth[parent] + 1)
        children[parent].append(leaf); leaf_of[tid] = leaf
    nN = len(children); is_leaf = [len(c) == 0 for c in children]
    order, stack, seen = [], [0], [False] * nN
    while stack:
        x = stack[-1]
        if not seen[x]:
            seen[x] = True; stack.extend(children[x])
        else:
            order.append(stack.pop())
    leaves = [i for i in range(nN) if is_leaf[i]]
    st = [0] * nN

    def fitch(pres):
        ch = 0
        for n in order:
            if is_leaf[n]:
                st[n] = 2 if n in pres else 1
            else:
                inter, uni = 3, 0
                for c in children[n]:
                    inter &= st[c]; uni |= st[c]
                st[n] = inter if inter else uni
                ch += 0 if inter else 1
        return ch

    import random
    rng = random.Random(0)
    recs, idx_track = [], {}
    for r in bz["motifs"]:
        P = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(P) < MIN_TRAD:
            continue
        pres = {leaf_of[t] for t in P}
        obs = fitch(pres)
        rand = np.mean([fitch(set(rng.sample(leaves, len(pres)))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))
        fams = Counter(gfam.get(t) for t in P if gfam.get(t))
        if not fams:
            continue
        dom, dn = fams.most_common(1)[0]
        conc = dn / len(P)
        dated = bool(signal >= SIG_DESCENT) and conc >= CONC and dom in FAMILY_DATES
        rec = {"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
               "np": len(P), "sig": round(float(signal), 2), "fam": dom, "conc": round(conc, 2),
               "age": FAMILY_DATES[dom][0] if dated else None,
               "lo": FAMILY_DATES[dom][1][0] if dated else None,
               "hi": FAMILY_DATES[dom][1][1] if dated else None, "dated": dated}
        recs.append(rec)
        if r["id"] in TRACK:
            idx_track[r["id"]] = rec

    dated = [r for r in recs if r["dated"]]
    by_fam = Counter(r["fam"] for r in dated)
    # timeline: dated motifs bucketed by millennium BP
    buckets = {}
    for r in dated:
        b = int(r["age"] // 1000) * 1000
        buckets[b] = buckets.get(b, 0) + 1
    timeline = [{"bp": b, "n": n} for b, n in sorted(buckets.items())]
    tracked = [{**idx_track[c], "label": lab} for c, lab in TRACK.items() if c in idx_track]
    fam_rows = [{"fam": f, "n": by_fam[f], "age": FAMILY_DATES[f][0],
                 "lo": FAMILY_DATES[f][1][0], "hi": FAMILY_DATES[f][1][1], "note": FAMILY_DATES[f][2]}
                for f in sorted(by_fam, key=lambda f: -FAMILY_DATES[f][0])]
    oldest = sorted(dated, key=lambda r: -r["age"])[:10]
    kms = [j["km"] for j in join.values()]

    data = {"n_motif": len(recs), "n_dated": len(dated), "min_trad": MIN_TRAD,
            "sig_descent": SIG_DESCENT, "conc": CONC,
            "join": {"n": len(join), "med_km": int(np.median(kms)), "p90_km": int(np.percentile(kms, 90)),
                     "families": len(set(gfam.values()))},
            "timeline": timeline, "fam_rows": fam_rows, "tracked": tracked, "oldest": oldest,
            "n_families_dated": len(FAMILY_DATES)}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs (>= {MIN_TRAD} trad) · descent+family-concentrated & dated: {len(dated)}")
    print(f"  Glottolog join: {len(join)} traditions, median {int(np.median(kms))} km, {len(set(gfam.values()))} families")
    print("  dated motifs by family:", dict(by_fam.most_common()))
    for t in tracked:
        age = f"{t['age']} BP ({t['lo']}–{t['hi']})" if t["dated"] else "areal / not family-dated"
        print(f"  {t['c']:5} {t['label']:16} sig={t['sig']} fam={t['fam']:20} conc={t['conc']} -> {age}")


if __name__ == "__main__":
    main()
