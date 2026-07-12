"""Mockup 61 · Hard geographic layers across all three catalogues.

The GEOGRAPHY half of mockup 45 (its "hard layers" — the coverage-corrected recursive peel of
units by their full attestation FOOTPRINT, not by theme) ported to every catalogue, so the three
are comparable:

  * Berezkin — units = traditions, features = motif incidence (this reproduces 45's geography tab);
  * ATU      — units = attested peoples, features = tale-type incidence;
  * TMI      — units = cited cultures, features = motif incidence.

Each catalogue: build the unit×feature 0/1 matrix, coverage-correct it (L1 row-norm × idf, so a
densely-catalogued unit does not dominate), then recursively split with Ward clustering — the same
hard peel as 45. Blocks are named GEOGRAPHICALLY from their continent composition (New/Old World,
regional leaves); each node reports its continent mix, its most over-represented core features, and
a breadth-based depth register (core features spanning many continents = deep/near-global).

Honest limit: only Berezkin has real per-tradition coordinates; ATU/TMI continents come from
attestation region labels / a gazetteer and are Euro-/literary-biased — the peel of those two is as
much a map of collection effort as of culture history. Deterministic; writes data.js.
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import gaz_coord  # noqa: E402

PAL = ["#4f7096","#c9873f","#6f9a5a","#b45c4b","#9c6a94","#bd9a43","#3f9e93","#8a6bbf",
       "#c0728f","#5b9bd5","#d08b4f","#7fa86b"]


def cont_ll(c):
    if not c: return "?"
    lon, lat = c
    if lon <= -30: return "Americas"
    if (lon >= 110 and lat <= 5) or lon <= -140: return "Oceania"
    if -20 <= lon <= 52 and -38 <= lat <= 17: return "Africa"
    return "Eurasia"


def cont_region_atu(region):
    r = (region or "").lower()
    if "africa" in r: return "Africa"
    if "oceania" in r: return "Oceania"
    if any(w in r for w in ("america", "caribbean")): return "Americas"
    return "Eurasia"


def ward_route(V, min_node, min_child):
    active = np.arange(len(V))
    for _ in range(6):
        lab = AgglomerativeClustering(n_clusters=2, linkage="ward").fit(V[active]).labels_
        sz = Counter(lab); sm = min(sz, key=sz.get)
        if sz[sm] >= min_child or len(active) <= min_node:
            full = np.full(len(V), -1); full[active] = lab; return full
        active = active[lab != sm]
    full = np.full(len(V), -1); full[active] = 0; return full


def peel_geo(Xb, cont_of, macro_of, short, uname, uweight, feat_name, feat_grp,
             min_node=30, min_child=6, depth=3, svd_dims=None):
    """Coverage-corrected recursive hard peel of units by their attestation footprint.
    Returns a flat list of geographic-block nodes. ``svd_dims`` reduces the (row-normed × idf)
    footprint to that many SVD components before clustering — needed for the high-dimensional,
    sparse ATU/TMI matrices where raw Ward otherwise just peels off single outliers; Berezkin
    (denser) clusters on the raw corrected matrix, as in mockup 45."""
    N, F = Xb.shape
    idf = np.log((N + 1) / (Xb.sum(0) + 1)) + 1.0
    def correct(sub): return (sub / (sub.sum(1, keepdims=True) + 1e-9)) * idf
    OVER = Xb.mean(0)
    Xc = correct(Xb)
    if svd_dims:
        E = StandardScaler().fit_transform(
            TruncatedSVD(n_components=min(svd_dims, N - 1, F - 1), random_state=0).fit_transform(Xc))
    else:
        E = Xc
    # per-feature continent breadth (for the depth register)
    feat_conts = [set() for _ in range(F)]
    rows, cols = np.nonzero(Xb)
    for i, j in zip(rows, cols):
        c = cont_of[i]
        if c != "?": feat_conts[j].add(c)
    feat_breadth = np.array([len(s) for s in feat_conts], float)

    def core(idx, topn=8):
        prev = Xb[idx].mean(0); lift = prev / (OVER + 1e-9)
        cand = sorted([j for j in range(F) if prev[j] >= 0.30], key=lambda j: -lift[j])[:topn]
        return [{"id": feat_name[j][0], "name": feat_name[j][1], "grp": feat_grp[j] if feat_grp else None,
                 "lift": round(float(lift[j]), 1), "breadth": int(feat_breadth[j])} for j in cand]

    def depth_of(idx):
        prev = Xb[idx].mean(0); lift = prev / (OVER + 1e-9)
        cand = sorted([j for j in range(F) if prev[j] >= 0.30], key=lambda j: -lift[j])[:12]
        if not cand: return 0.0, "regional / shallow"
        b = float(np.mean([feat_breadth[j] for j in cand]))
        lbl = "deep / near-global" if b >= 3.5 else "broad / inter-regional" if b >= 2.2 else "regional / shallow"
        return round(b, 2), lbl

    def name_of(idx, level, is_leaf):
        c = Counter(cont_of[i] for i in idx); frac = lambda k: c.get(k, 0) / len(idx)
        top = [k for k, _ in c.most_common(2)]
        if level == 0: return "All units"
        if is_leaf:
            mac = Counter(macro_of[i] for i in idx).most_common(1)[0][0]
            return short.get(mac, mac)
        if level == 1: return "New World" if frac("Americas") > 0.5 else "Old World"
        if frac("Oceania") > 0.25: return "Indo-Pacific"
        if frac("Americas") > 0.7: return "American"
        if frac("Americas") > 0.25 and frac("Eurasia") > 0.25: return "Circum-Pacific bridge"
        if frac("Africa") > 0.25 and frac("Eurasia") > 0.4: return "W-Eurasian + N-African belt"
        if frac("Eurasia") > 0.6: return "Eurasian core"
        return " + ".join(top)

    nodes = []; leaf = {}
    def rec(idx, nid, parent, level):
        n = len(idx); V = E[idx]; lab = ward_route(V, min_node, min_child); m = lab >= 0
        sil = float(silhouette_score(V[m], lab[m])) if 1 < len(set(lab[m])) < m.sum() else 0.0
        is_leaf = (n < min_node) or (level >= depth) or (len(set(lab[m])) < 2)
        di, dl = depth_of(idx)
        macs = [a2 for a2, _ in Counter(macro_of[i] for i in idx).most_common(6)]
        reps = [uname[i] for i in sorted(idx, key=lambda i: -uweight[i])[:8]]
        nodes.append({"id": nid, "parent": parent, "level": level, "name": name_of(idx, level, is_leaf),
            "n": n, "sil": round(sil, 3), "leaf": is_leaf,
            "cont": dict(Counter(cont_of[i] for i in idx).most_common()),
            "macros": [{"name": a2, "n": v} for a2, v in Counter(macro_of[i] for i in idx).most_common(6)],
            "core": core(idx, 8), "reps": reps, "depth_index": di, "depth_label": dl,
            "_disc": [Counter(cont_of[i] for i in idx).most_common(1)[0][0] if idx else None,
                      short.get(macs[0], macs[0]) if macs else None,
                      short.get(macs[1], macs[1]) if len(macs) > 1 else None]})
        if is_leaf:
            for i in idx: leaf[i] = nid
            return
        gs = sorted([[idx[i] for i in range(n) if lab[i] == c] for c in sorted(set(lab[m]))], key=len)
        for gj, g in enumerate(gs): rec(g, f"{nid}.{gj}", nid, level + 1)
    rec(list(range(N)), "0", None, 0)

    # dedup collided block names on the first discriminating dimension
    for _ in range(4):
        groups = {}
        for nd in nodes:
            if nd["level"] > 0: groups.setdefault(nd["name"], []).append(nd)
        if all(len(g) < 2 for g in groups.values()): break
        for name, g in groups.items():
            if len(g) < 2: continue
            for dim in range(max(len(nd["_disc"]) for nd in g)):
                vals = [(nd["_disc"][dim] if dim < len(nd["_disc"]) else None) for nd in g]
                if len({v for v in vals if v}) > 1:
                    for nd, v in zip(g, vals):
                        if v: nd["name"] += f" · {v}"
                    break
            else:
                for i, nd in enumerate(g): nd["name"] += f" · {i+1}"
    for nd in nodes: nd.pop("_disc", None)
    lv = [nd for nd in nodes if nd["leaf"]]
    for i, nd in enumerate(lv): nd["color"] = PAL[i % len(PAL)]
    return nodes


def verdict(nodes, N):
    """Does this catalogue actually stratify into geographic layers, or collapse to one blob?"""
    leaves = [nd for nd in nodes if nd["leaf"]]
    biggest = max((nd["n"] for nd in leaves), default=N)
    root = next((nd for nd in nodes if nd["level"] == 0), None)
    top_sil = root["sil"] if root else 0.0
    pct = biggest / N
    v = ("stratifies" if pct <= 0.55 else "weakly stratifies" if pct <= 0.80 else "does not stratify")
    return {"n_leaves": len(leaves), "largest_leaf_pct": round(100 * pct), "top_sil": top_sil, "verdict": v}


# ============================ BEREZKIN ============================
def build_berezkin():
    bz = json.load(open(ROOT / "outputs" / "motifs" / "berezkin.json"))
    TR, MOT = bz["traditions"], bz["motifs"]
    SHORT = {"North America: North And West": "N American", "Plains And Southeast": "Plains / SE",
             "Mexico – Central Andes": "Meso / Andean", "Eastern South America": "Amazonian",
             "Southern South America": "Southern Cone", "Sub-Saharan Africa": "Sub-Saharan Africa",
             "Western Europe, North Africa": "W-Europe / N-Africa", "Northern And Eastern Europe": "N & E Europe",
             "Southwest And Central Asia, Aryan India": "SW & C Asia / India",
             "Tibet, Non-Aryan South Asia, Southeast Asia": "Tibet / SE Asia", "East Asia": "East Asia",
             "Siberia – Mongolia": "Siberia–Mongolia", "Oceania": "Oceania", "Beringia": "Beringia",
             "Australia": "Australia"}
    def macro(t):
        ap = t.get("areal_path") or []; return ap[0][1].title() if ap and ap[0] else "?"
    def cont(a):
        a = a.lower()
        if "africa" in a: return "Africa"
        if "australia" in a or "oceania" in a: return "Oceania"
        if any(w in a for w in ("america", "andes", "mexico", "amazon")): return "Americas"
        return "Eurasia"
    tset = defaultdict(set)
    for j, m in enumerate(MOT):
        for tid in m.get("traditions", []): tset[tid].add(j)
    keep = [tid for tid in TR if len(tset[tid]) >= 15]
    N = len(keep)
    Xb = np.zeros((N, len(MOT)), np.float32)
    cont_of, macro_of, uname, w = [], [], [], np.zeros(N)
    for i, tid in enumerate(keep):
        for j in tset[tid]: Xb[i, j] = 1
        cont_of.append(cont(macro(TR[tid]))); macro_of.append(macro(TR[tid]))
        uname.append(TR[tid]["name"]); w[i] = len(tset[tid])
    feat_name = [(m["id"], m.get("name", m["id"])) for m in MOT]
    feat_grp = [m.get("motif_group_num") for m in MOT]
    nodes = peel_geo(Xb, cont_of, macro_of, SHORT, uname, w, feat_name, feat_grp, 40, 8, 3)
    return {"nodes": nodes, "n_unit": N, "unit": "traditions", "n_feat": len(MOT),
            "features": "motif attestation", "real_coords": True, **verdict(nodes, N)}


# ============================ ATU ============================
def build_atu():
    atu = json.load(open(ROOT / "outputs" / "motifs" / "atu.json"))
    types = atu["types"]
    tid_idx = {t["id"]: j for j, t in enumerate(types)}
    p_types = defaultdict(set); p_reg = defaultdict(Counter); p_w = Counter()
    for t in types:
        for r in (t.get("attestations_grouped") or {}).get("regions", []):
            reg = r.get("region")
            for e in r.get("entries", []):
                pe = e.get("people")
                if not pe: continue
                p_types[pe].add(t["id"]); p_w[pe] += 1
                if reg: p_reg[pe][reg] += 1
    peoples = [p for p in p_types if p_w[p] >= 12]
    N = len(peoples)
    Xb = np.zeros((N, len(types)), np.float32)
    for i, p in enumerate(peoples):
        for tid in p_types[p]:
            if tid in tid_idx: Xb[i, tid_idx[tid]] = 1
    macro_of = [(p_reg[p].most_common(1)[0][0] if p_reg[p] else "?") for p in peoples]
    cont_of = [cont_region_atu(m) for m in macro_of]
    w = np.array([p_w[p] for p in peoples])
    feat_name = [(t["id"], t.get("name", t["id"])) for t in types]
    nodes = peel_geo(Xb, cont_of, macro_of, {}, peoples, w, feat_name, None, 12, 2, 2, svd_dims=40)
    return {"nodes": nodes, "n_unit": N, "unit": "peoples", "n_feat": len(types),
            "features": "tale-type attestation", "real_coords": False, **verdict(nodes, N)}


# ============================ TMI ============================
def build_tmi():
    tmi = json.load(open(ROOT / "outputs" / "motifs" / "tmi.json"))
    MOT = tmi["motifs"]
    ccont = {}
    def cont_of_cult(lab):
        if lab not in ccont: ccont[lab] = cont_ll(gaz_coord(lab))
        return ccont[lab]
    c_mot = defaultdict(list); c_w = Counter(); c_cont = defaultdict(Counter)
    for j, m in enumerate(MOT):
        for x in (m.get("cultures") or {}):
            c_mot[x].append(j); c_w[x] += 1
            cc = cont_of_cult(x)
            if cc and cc != "?": c_cont[x][cc] += 1
    cults = [c for c in c_mot if c_w[c] >= 40]
    N = len(cults)
    Xb = np.zeros((N, len(MOT)), np.float32)
    for i, c in enumerate(cults):
        Xb[i, c_mot[c]] = 1
    cont_of = [(c_cont[c].most_common(1)[0][0] if c_cont[c] else "?") for c in cults]
    macro_of = list(cont_of)
    w = np.array([c_w[c] for c in cults])
    feat_name = [(m["id"], m.get("name", m["id"])) for m in MOT]
    feat_grp = [m.get("chapter") for m in MOT]
    nodes = peel_geo(Xb, cont_of, macro_of, {}, cults, w, feat_name, feat_grp, 12, 2, 2, svd_dims=40)
    return {"nodes": nodes, "n_unit": N, "unit": "cultures", "n_feat": len(MOT),
            "features": "motif attestation", "real_coords": False, **verdict(nodes, N)}


data = {"catalogues": {"brz": build_berezkin(), "atu": build_atu(), "tmi": build_tmi()},
        "note": "The hard geographic layers of mockup 45, ported to each catalogue: units peeled by their full "
                "attestation footprint (coverage-corrected L1×idf, Ward), blocks named by continent composition. "
                "Only Berezkin has real per-tradition coordinates (this reproduces 45's geography tab); ATU/TMI "
                "continents come from attestation regions / a gazetteer and are Euro-/literary-biased, so those two "
                "peels are as much a map of cataloguing effort as of culture history."}
out = Path(__file__).parent / "data.js"
out.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
for k, c in data["catalogues"].items():
    leaves = sum(1 for nd in c["nodes"] if nd["leaf"])
    print(f"[{k}] {c['n_unit']} {c['unit']} × {c['n_feat']} feats · {len(c['nodes'])} nodes ({leaves} leaves)")
print(f"data.js ~{out.stat().st_size // 1024}KB")
