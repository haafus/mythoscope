"""Narrative stratum (mockup 44) — theme × depth on the data-driven taxonomy.

The original motivation for re-deriving themes: Berezkin's giant catch-alls "Adventures" (1243)
and "Tricks" (620) average over motifs of very different antiquity, so a theme×depth analysis on
the hand scheme is blunt. This runs depth on mockup 41's **narrative taxonomy** instead, and shows
the gradient the catch-alls hid — the swallowing-monster / body-cosmology complex sits deep, the
Eurasian märchen complexes (ogre-dupe, revenge, magic-wife) sit shallow.

Depth proxy = **cross-continental reach** (mega-set span 0–3: does the motif touch the New-World /
Old-World / Sahul continental sets?) — the disjunction proxy that best tracks deep time (widespread
*across oceans* ≈ old), reported alongside mean breadth. Honest limit: a breadth/span proxy conflates
deep descent with wide diffusion (as in mockups 17, 39).

Run:  python mockups/44-narrative-stratum/build_data.py
"""
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"

NW = {"Northern & Western N. America", "Eastern North America", "Mesoamerica & Andes", "South America"}
OLD = {"Europe", "Near East & N. Africa", "Iran, C. & S. Asia", "East & SE Asia",
       "Siberia & Beringia", "Sub-Saharan Africa"}
SAH = {"Austronesia & Oceania", "Aboriginal Australia"}
CATCHALL = {6, 7, 10, 11}          # Berezkin group_num that are genre catch-alls (Culture, Flora, Adv, Tricks)
GEN = {1: "Sun/Moon", 2: "Stars", 3: "Cosmogony", 4: "Death", 5: "Humans", 6: "Culture",
       7: "Flora/fauna", 8: "Monsters", 9: "Identif.", 10: "Adventures", 11: "Tricks",
       12: "Names", 13: "Formulae", 0: "?"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    bz = json.loads((ROOT / "outputs/motifs/berezkin.json").read_text("utf-8"))
    T, motifs = bz["traditions"], bz["motifs"]
    tax = json.loads((MOCKS / "41-theme-rederivation/narrative_taxonomy.json").read_text("utf-8"))
    NT = tax["motifs"]
    subbase, acc = {}, 0
    for c in sorted(tax["clusters"], key=lambda c: c["l1"]):
        subbase[c["l1"]] = acc; acc += len(c["subs"])
    L1NAME = {c["l1"]: c["name"] for c in tax["clusters"]}
    SUBNAME, SUBL1 = {}, {}
    for c in tax["clusters"]:
        for j, s in enumerate(c["subs"]):
            gid = subbase[c["l1"]] + j
            SUBNAME[gid] = s["name"]; SUBL1[gid] = c["l1"]

    # per-motif depth features
    feats = {}
    for r in motifs:
        trs = r.get("traditions") or []
        areas = {m21.area_of(T[t].get("areal_path") or []) for t in trs if t in T}
        areas.discard(None)
        span = int(bool(areas & NW) + bool(areas & OLD) + bool(areas & SAH))
        feats[r["id"]] = {"b": len(trs), "macro": len(areas), "span": span,
                          "g": int(r.get("motif_group_num") or 0)}

    def agg(ids):
        b = np.array([feats[i]["b"] for i in ids]); sp = np.array([feats[i]["span"] for i in ids])
        mc = np.array([feats[i]["macro"] for i in ids]); gg = [feats[i]["g"] for i in ids]
        catch = np.mean([1 if g in CATCHALL else 0 for g in gg])
        return {"n": len(ids), "span": round(float(sp.mean()), 3), "b": round(float(b.mean()), 1),
                "macro": round(float(mc.mean()), 2), "tri": round(float((sp == 3).mean()), 3),
                "catchall": round(float(catch), 3)}

    by_l1 = defaultdict(list); by_sub = defaultdict(list)
    for mid, nt in NT.items():
        by_l1[nt["l1"]].append(mid)
        by_sub[subbase[nt["l1"]] + nt["l2"]].append(mid)

    clusters = []
    for l1, ids in by_l1.items():
        a = agg(ids); a.update({"l1": l1, "name": L1NAME[l1]}); clusters.append(a)
    clusters.sort(key=lambda c: -c["span"])
    subs = []
    for gid, ids in by_sub.items():
        if len(ids) < 4:
            continue
        a = agg(ids); a.update({"gid": gid, "name": SUBNAME[gid], "l1": SUBL1[gid],
                                "l1_name": L1NAME[SUBL1[gid]]}); subs.append(a)

    # the catch-all decomposition: how the old flat "Adventures"/"Tricks" now spread across
    # narrative clusters of different depth
    catch_decomp = []
    for g, label in [(10, "Приключения"), (11, "Трюки")]:
        ids = [r["id"] for r in motifs if int(r.get("motif_group_num") or 0) == g and r["id"] in NT]
        whole = agg(ids)
        dist = defaultdict(list)
        for i in ids:
            dist[NT[i]["l1"]].append(i)
        parts = sorted(({"l1": l1, "name": L1NAME[l1], **agg(v)} for l1, v in dist.items() if len(v) >= 8),
                       key=lambda p: -p["span"])
        catch_decomp.append({"g": g, "label": label, "n": len(ids), "span": whole["span"],
                             "parts": parts})

    deep_subs = sorted([s for s in subs if s["n"] >= 8], key=lambda s: -s["span"])[:10]
    shallow_subs = sorted([s for s in subs if s["n"] >= 8], key=lambda s: s["span"])[:10]

    data = {"n_motif": len(NT), "clusters": clusters, "subs": subs,
            "catch_decomp": catch_decomp, "deep_subs": deep_subs, "shallow_subs": shallow_subs,
            "span_lo": min(c["span"] for c in clusters), "span_hi": max(c["span"] for c in clusters)}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(NT)} motifs · {len(clusters)} narrative clusters · depth = cross-continental span")
    print("  narrative clusters by depth (mega-set span · breadth · catch-all origin %):")
    for c in clusters:
        print(f"    {c['span']:.2f}  b={c['b']:5.1f}  catch {c['catchall']*100:3.0f}%  {c['name']}")
    for cd in catch_decomp:
        span_range = f"{cd['parts'][-1]['span']:.2f}–{cd['parts'][0]['span']:.2f}"
        print(f"  old '{cd['label']}' (n={cd['n']}, flat span {cd['span']:.2f}) now spans clusters {span_range}")


if __name__ == "__main__":
    main()
