"""Admixture-graph back-migration (mockup 36, roadmap M36) — direction, not just span.

Tests alt-hypothesis #6 ("Africa is a sink"): for a motif shared between **Africa and West
Eurasia**, is it a **deep out-of-Africa** inheritance or a **recent back-into-Africa** flow?
A tree cannot tell (both give Africa+Eurasia co-occurrence). The admixture graph adds the
documented **Eurasian → Africa back-migration edges**; direction then comes from the motif's
*within-Africa* footprint:

  * **deep OoA** — reaches the deep, un-admixed African reservoir (West / Central / Southern
    Africa, San), so it predates the back-flow;
  * **back-migration** — its African presence sits **only in the Eurasian-admixed corridor**
    (North Africa, Horn of Africa, the Sahel) that received the documented gene flow.

The admixture "edges" here are the *settled* back-migration geography (Hellenthal 2014,
Pagani, Pickrell — Bronze-Age Eurasian ancestry heavy in the Horn / North Africa), encoded as a
coarse regional classification — no raw SNP needed for a directional test at this resolution.
The genetic counterpart to M35's historical-corridor directionality; builds on M33's genetics.

Run:  python mockups/36-admixture-backmigration/build_data.py
"""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_AFR, MIN_EUR = 2, 2

# deep, un-admixed African reservoir (out-of-Africa substrate)
DEEP = {"BANTU", "WEST AFRICA", "SOUTHWEST AFRICA"}
# the Eurasian-admixed back-migration corridor
ADMIXED = {"NORTH AFRICA", "HORN OF AFRICA", "EASTERN SUDANIC, SAHARAN, ADAMAUA"}
# West-Eurasian macro-regions (the back-migration source)
WEUR_L0 = {"NORTHERN AND EASTERN EUROPE", "WESTERN EUROPE, NORTH AFRICA",
           "SOUTHWEST AND CENTRAL ASIA, ARYAN INDIA"}
TRACK = {"K8aa": "Jonah / swallowed", "A3": "sun & moon", "B4": "fished-out earth"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def role(v):
    ap = v.get("areal_path") or []
    l0 = (ap[0][1].upper() if ap else "")
    l1 = (ap[1][1].upper() if len(ap) > 1 else "")
    if l1 in DEEP:
        return "deep"
    if l1 in ADMIXED:
        return "admixed"
    if l0 in WEUR_L0:
        return "weur"
    return None


def main():
    geo = _load("_geo.py", "geo")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    roles = {t: role(v) for t, v in T.items()}

    def coord(t):
        c = coords.get(t)
        return (float(c[0]), float(c[1])) if isinstance(c, (list, tuple)) and len(c) == 2 else None

    def classify(motif):
        P = [t for t in (motif.get("traditions") or []) if roles.get(t)]
        c = Counter(roles[t] for t in P)
        deep, adm, eur = c["deep"], c["admixed"], c["weur"]
        afr = deep + adm
        admf = adm / afr if afr else None
        return deep, adm, eur, afr, admf

    afr_eur, afr_only = [], []
    rec = {}
    for m in bz["motifs"]:
        deep, adm, eur, afr, admf = classify(m)
        if afr >= MIN_AFR and eur >= MIN_EUR:
            # direction of an Africa<->Eurasia motif
            if admf >= 0.6 and deep <= 1:
                d = "backmig"           # only in the admixed corridor -> recent back-flow
            elif deep >= 2 or admf <= 0.34:
                d = "deep_ooa"          # reaches the deep reservoir -> old African substrate
            else:
                d = "ambiguous"
            r = {"c": m["id"], "n": m.get("name", ""), "deep": deep, "adm": adm, "eur": eur,
                 "admf": round(admf, 2), "dir": d}
            afr_eur.append(r); rec[m["id"]] = r
        elif afr >= 3 and eur == 0:
            afr_only.append(admf)

    n = len(afr_eur)
    dirc = Counter(r["dir"] for r in afr_eur)
    mean_admf_ae = float(np.mean([r["admf"] for r in afr_eur])) if afr_eur else 0.0
    mean_admf_ao = float(np.mean([x for x in afr_only if x is not None])) if afr_only else 0.0
    # examples
    backmig = sorted((r for r in afr_eur if r["dir"] == "backmig"), key=lambda r: (-r["adm"], r["deep"]))[:8]
    deepex = sorted((r for r in afr_eur if r["dir"] == "deep_ooa"), key=lambda r: (-r["deep"], -r["eur"]))[:8]
    tracked = [rec[c] | {"label": lab} for c, lab in TRACK.items() if c in rec]

    # African tradition points for the map, coloured by tier
    pts = []
    for t, rl in roles.items():
        if rl in ("deep", "admixed", "weur"):
            cc = coord(t)
            if cc:
                pts.append({"x": round(cc[1], 1), "y": round(cc[0], 1), "r": rl})

    data = {
        "n_afr_eur": n, "n_afr_only": len(afr_only), "min_afr": MIN_AFR, "min_eur": MIN_EUR,
        "dir": {"backmig": dirc["backmig"], "deep_ooa": dirc["deep_ooa"], "ambiguous": dirc["ambiguous"]},
        "backmig_share": round(dirc["backmig"] / n, 3) if n else 0.0,
        "mean_admf": {"afr_eur": round(mean_admf_ae, 3), "afr_only": round(mean_admf_ao, 3)},
        "hist": [int(x) for x in np.histogram([r["admf"] for r in afr_eur], bins=np.linspace(0, 1, 6))[0]],
        "examples": {"backmig": backmig, "deep": deepex}, "tracked": tracked, "pts": pts,
        "counts": {r: sum(1 for x in roles.values() if x == r) for r in ("deep", "admixed", "weur")},
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"traditions by role: {data['counts']}")
    print(f"Africa<->W.Eurasia motifs: {n}  (Africa-only baseline: {len(afr_only)})")
    print(f"  direction: back-migration {dirc['backmig']} ({data['backmig_share']:.0%}), "
          f"deep-OoA {dirc['deep_ooa']}, ambiguous {dirc['ambiguous']}")
    print(f"  mean admixed-fraction: Africa<->Eurasia {mean_admf_ae:.3f} vs Africa-only {mean_admf_ao:.3f} "
          f"(higher => back-migration signal)")
    for r in tracked:
        print(f"  {r['c']:6} {r['label']:18} deep={r['deep']} adm={r['adm']} eur={r['eur']} admf={r['admf']} -> {r['dir']}")


if __name__ == "__main__":
    main()
