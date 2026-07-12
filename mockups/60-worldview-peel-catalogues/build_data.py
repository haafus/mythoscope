"""Mockup 60 · Worldview stratigraphic peel across all three catalogues.

Mockup 45 peeled Berezkin traditions in two genre-profile spaces. This ports the *worldview*
half of that idea to every catalogue in its OWN authored taxonomy, so the three are directly
comparable:

  * Berezkin — 13 etiological theme groups (motif_group_num), units = traditions;
  * ATU      — 7 top tale-type chapters (Animal / Magic / Religious / Realistic / Ogre /
               Anecdotes / Formula), units = attested peoples;
  * TMI      — 23 letter-chapters (A Myths … Z Misc), units = cited cultures.

Each tab is a coverage-aware recursive CLR peel of that catalogue's units by their profile over
its native categories. Node names combine a depth REGISTER (Deep / Young, from the share of the
catalogue's archaic/mythic categories) with a SIGNATURE category (the one most over-represented
vs the parent block), then a dedup pass. A per-node depth index = mean cross-continent BREADTH of
the categories the block emphasises (broad = old), the same "breadth → age" proxy as 45.

Honest limit: ATU and TMI have no per-tradition coordinates and are heavily Euro-/literary-biased,
so their "deep" layer is as much the over-catalogued European core as any real antiquity — the
continent-composition bar on every node is there to keep that visible. Deterministic; writes data.js.
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import gaz_coord  # noqa: E402

MIN_NODE, MIN_CHILD, DEPTH = 30, 6, 3
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


# ---- generic recursive worldview peel (self-contained, catalogue-agnostic) --------------
def ward_route(V):
    active = np.arange(len(V)); routed = []
    for _ in range(6):
        lab = AgglomerativeClustering(n_clusters=2, linkage="ward").fit(V[active]).labels_
        sz = Counter(lab); sm = min(sz, key=sz.get)
        if sz[sm] >= MIN_CHILD or len(active) <= MIN_NODE:
            full = np.full(len(V), -1); full[active] = lab; return full
        routed += list(active[lab == sm]); active = active[lab != sm]
    full = np.full(len(V), -1); full[active] = 0; return full


def peel_catalogue(prof, cont_of, macro_of, uname, uweight, udepth,
                   theme_short, theme_sig, deep_cols, thi, tlo):
    """Return list of nodes for one catalogue. prof: n×K L1-normalised profiles."""
    clr = np.log(prof + 1e-3); clr = clr - clr.mean(1, keepdims=True)
    K = prof.shape[1]
    over = prof.mean(0)

    def a_share(idx): return float(sum(prof[idx].mean(0)[k] for k in deep_cols))
    def sig_order(mp, pp):
        cand = [k for k in range(K) if mp[k] >= 0.03] or list(range(K))
        return sorted(cand, key=lambda k: mp[k] / (pp[k] + 1e-6), reverse=True)
    def pick_sig(order, psig):
        if psig is None: return order[0]
        for k in order:
            if k != psig: return k
        return order[0]
    def wv_name(level, a, k):
        if level == 0: return "All traditions"
        reg = "Deep " if a >= thi else ("Young " if a <= tlo else "")
        return reg + theme_sig[k]

    nodes = []; leaf = {}
    def rec(idx, nid, parent, level, pp, psig):
        n = len(idx); V = clr[idx]; lab = ward_route(V); m = lab >= 0
        sil = float(silhouette_score(V[m], lab[m])) if len(set(lab[m])) > 1 else 0.0
        is_leaf = (n < MIN_NODE) or (level >= DEPTH) or (len(set(lab[m])) < 2)
        mp = prof[idx].mean(0); a = a_share(idx); order = sig_order(mp, pp)
        mysig = pick_sig(order, psig)
        md = round(float(np.mean([udepth[i] for i in idx])), 1)
        macs = [a2 for a2, _ in Counter(macro_of[i] for i in idx).most_common(6)]
        reps = [uname[i] for i in sorted(idx, key=lambda i: -uweight[i])[:8]]
        nodes.append({"id": nid, "parent": parent, "level": level, "name": wv_name(level, a, mysig),
            "n": n, "sil": round(sil, 3), "leaf": is_leaf, "a_share": round(a, 2),
            "cont": dict(Counter(cont_of[i] for i in idx).most_common()),
            "macros": [{"name": a2, "n": v} for a2, v in Counter(macro_of[i] for i in idx).most_common(6)],
            "themes": [{"k": theme_short[k], "n": round(100 * float(mp[k]))}
                       for k in sorted(range(K), key=lambda k: -mp[k])[:6]],
            "reps": reps, "depth_index": md,
            "depth_label": ("deep / near-global" if md >= 62 else "intermediate" if md >= 45 else "shallow / regional"),
            "_disc": [next(iter(Counter(cont_of[i] for i in idx)), None),
                      macs[0] if macs else None] + [theme_short[k] for k in order if k != mysig][:3]})
        if is_leaf:
            for i in idx: leaf[i] = nid
            return
        gs = sorted([[idx[i] for i in range(n) if lab[i] == c] for c in sorted(set(lab[m]))], key=len)
        for gj, g in enumerate(gs): rec(g, f"{nid}.{gj}", nid, level + 1, mp, mysig)
    rec(list(range(len(prof))), "0", None, 0, over, None)

    # dedup collided names on the first discriminating dimension
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


def pct(x):
    x = np.asarray(x, float)
    if len(x) < 2 or np.ptp(x) == 0: return np.full(len(x), 50.0)
    return (x.argsort().argsort() / (len(x) - 1)) * 100


# ============================ BEREZKIN ============================
def build_berezkin():
    bz = json.load(open(ROOT / "outputs" / "motifs" / "berezkin.json"))
    TR, MOT = bz["traditions"], bz["motifs"]
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
    # motif continent-breadth
    mbreadth = np.zeros(len(MOT))
    for j, m in enumerate(MOT):
        cs = {cont(macro(TR[t])) for t in m.get("traditions", []) if t in TR}
        mbreadth[j] = len(cs)
    GRP = sorted({MOT[j].get("motif_group_num") for j in range(len(MOT)) if MOT[j].get("motif_group_num")})
    GIDX = {g: i for i, g in enumerate(GRP)}
    SHORT = {"01": "Sun&Moon", "02": "Stars", "03": "Cosmogony", "04": "Death", "05": "Humans",
             "06": "Subsistence", "07": "Plants/animals", "08": "Monsters", "09": "Protagonist",
             "10": "Adventures", "11": "Tricks", "12": "Names", "13": "Formulae"}
    SIG = {"01": "Sun & Moon", "02": "Star lore", "03": "Cosmogony & elements", "04": "Origin-of-death",
           "05": "Origin-of-humans", "06": "Subsistence culture", "07": "Plant & animal origins",
           "08": "Monstrous beings", "09": "Protagonist cycle", "10": "Adventure tales",
           "11": "Trick & contest", "12": "Naming lore", "13": "Tale formulae"}
    n = len(keep)
    prof = np.zeros((n, len(GRP)), np.float32); depth_raw = np.zeros(n); w = np.zeros(n)
    cont_of, macro_of, uname = [], [], []
    for i, tid in enumerate(keep):
        br = []
        for j in tset[tid]:
            g = MOT[j].get("motif_group_num")
            if g in GIDX: prof[i, GIDX[g]] += 1
            br.append(mbreadth[j])
        depth_raw[i] = np.mean(br) if br else 1
        w[i] = len(tset[tid])
        cont_of.append(cont(macro(TR[tid]))); macro_of.append(macro(TR[tid])); uname.append(TR[tid]["name"])
    prof = prof / (prof.sum(1, keepdims=True) + 1e-9)
    deep = {GIDX[g] for g in GRP if g in {"01","02","03","04","05","06","07","08","09"}}
    nodes = peel_catalogue(prof, cont_of, macro_of, uname, w, pct(depth_raw),
                           [SHORT[g] for g in GRP], [SIG[g] for g in GRP], deep, 0.55, 0.35)
    return {"nodes": nodes, "n_unit": n, "unit": "traditions", "n_dim": len(GRP),
            "taxonomy": "Berezkin's 13 etiological theme groups", "labels": [SHORT[g] for g in GRP]}


# ============================ ATU ============================
def build_atu():
    atu = json.load(open(ROOT / "outputs" / "motifs" / "atu.json"))
    CH = ["Animal Tales", "Tales Of Magic", "Religious Tales", "Realistic Tales",
          "Tales Of The Stupid Ogre", "Anecdotes And Jokes", "Formula Tales"]
    SHORT = ["Animal", "Magic", "Religious", "Realistic", "Stupid-ogre", "Anecdote/joke", "Formula"]
    SIG = ["Animal tales", "Wonder tales", "Religious tales", "Novella / realistic",
           "Stupid-ogre tales", "Anecdotes & jokes", "Formula tales"]
    CIDX = {c: i for i, c in enumerate(CH)}
    # type -> chapter, type -> #distinct-region breadth
    tybreadth, tychap = {}, {}
    for t in atu["types"]:
        ch = t.get("chapter")
        if ch not in CIDX: continue
        tychap[t["id"]] = CIDX[ch]
        regs = {r.get("region") for r in (t.get("attestations_grouped") or {}).get("regions", []) if r.get("region")}
        conts = {cont_region_atu(r) for r in regs}
        tybreadth[t["id"]] = max(1, len(conts))
    # people -> chapter profile, dominant region, breadth
    p_prof = defaultdict(lambda: np.zeros(len(CH)))
    p_reg = defaultdict(Counter); p_br = defaultdict(list); p_w = Counter()
    for t in atu["types"]:
        tid = t["id"]
        if tid not in tychap: continue
        for r in (t.get("attestations_grouped") or {}).get("regions", []):
            reg = r.get("region")
            for e in r.get("entries", []):
                pe = e.get("people")
                if not pe: continue
                p_prof[pe][tychap[tid]] += 1
                p_w[pe] += 1; p_br[pe].append(tybreadth[tid])
                if reg: p_reg[pe][reg] += 1
    peoples = [p for p in p_prof if p_w[p] >= 12]
    n = len(peoples)
    prof = np.array([p_prof[p] for p in peoples], np.float32)
    prof = prof / (prof.sum(1, keepdims=True) + 1e-9)
    depth_raw = np.array([np.mean(p_br[p]) for p in peoples])
    w = np.array([p_w[p] for p in peoples])
    macro_of = [(p_reg[p].most_common(1)[0][0] if p_reg[p] else "?") for p in peoples]
    cont_of = [cont_region_atu(m) for m in macro_of]
    deep = {CIDX["Animal Tales"], CIDX["Tales Of Magic"], CIDX["Religious Tales"]}
    nodes = peel_catalogue(prof, cont_of, macro_of, peoples, w, pct(depth_raw),
                           SHORT, SIG, deep, 0.62, 0.42)
    return {"nodes": nodes, "n_unit": n, "unit": "peoples", "n_dim": len(CH),
            "taxonomy": "ATU's 7 tale-type chapters", "labels": SHORT}


# ============================ TMI ============================
def build_tmi():
    tmi = json.load(open(ROOT / "outputs" / "motifs" / "tmi.json"))
    chap_name = {}
    for m in tmi["motifs"]:
        chap_name.setdefault(m.get("chapter"), m.get("chapter_name"))
    CH = [c for c in sorted(chap_name) if c]
    CIDX = {c: i for i, c in enumerate(CH)}
    SHORT = [f"{c} {chap_name[c]}" for c in CH]
    SIG = [f"{chap_name[c]} ({c})" for c in CH]
    # gazetteer continent per culture label (memoised)
    ccont = {}
    def cont_of_cult(lab):
        if lab not in ccont: ccont[lab] = cont_ll(gaz_coord(lab))
        return ccont[lab]
    # motif continent-breadth + per-culture chapter profile
    c_prof = defaultdict(lambda: np.zeros(len(CH)))
    c_br = defaultdict(list); c_w = Counter(); c_cont = defaultdict(Counter)
    for m in tmi["motifs"]:
        ch = m.get("chapter")
        if ch not in CIDX: continue
        cults = list((m.get("cultures") or {}))
        conts = {cont_of_cult(x) for x in cults if cont_of_cult(x) not in (None, "?")}
        br = max(1, len(conts))
        for x in cults:
            c_prof[x][CIDX[ch]] += 1
            c_w[x] += 1; c_br[x].append(br)
            cc = cont_of_cult(x)
            if cc and cc != "?": c_cont[x][cc] += 1
    cults = [c for c in c_prof if c_w[c] >= 40]
    n = len(cults)
    prof = np.array([c_prof[c] for c in cults], np.float32)
    prof = prof / (prof.sum(1, keepdims=True) + 1e-9)
    depth_raw = np.array([np.mean(c_br[c]) for c in cults])
    w = np.array([c_w[c] for c in cults])
    cont_of = [(c_cont[c].most_common(1)[0][0] if c_cont[c] else "?") for c in cults]
    macro_of = list(cont_of)  # TMI has no finer region than continent (culture names live in `reps`)
    deep = {CIDX[c] for c in ("A", "E", "F", "V", "C") if c in CIDX}
    nodes = peel_catalogue(prof, cont_of, macro_of, cults, w, pct(depth_raw),
                           SHORT, SIG, deep, 0.42, 0.22)
    return {"nodes": nodes, "n_unit": n, "unit": "cultures", "n_dim": len(CH),
            "taxonomy": "TMI's 23 letter-chapters", "labels": SHORT}


data = {"catalogues": {"brz": build_berezkin(), "atu": build_atu(), "tmi": build_tmi()},
        "note": "The worldview half of mockup 45, ported to each catalogue's own authored taxonomy so the "
                "three are comparable: Berezkin's 13 etiological groups (traditions), ATU's 7 chapters (peoples), "
                "TMI's 23 letter-chapters (cultures). Each is a coverage-aware CLR peel; node names = depth register "
                "(Deep/Young, share of archaic categories) + signature category, dated by cross-continent breadth. "
                "ATU/TMI have no per-tradition coordinates and are Euro-/literary-biased — the continent bar keeps "
                "that visible; their 'deep' layer is partly the over-catalogued European core, not antiquity."}
out = Path(__file__).parent / "data.js"
out.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
for k, c in data["catalogues"].items():
    leaves = sum(1 for nd in c["nodes"] if nd["leaf"])
    print(f"[{k}] {c['n_unit']} {c['unit']} · {c['n_dim']}-dim · {len(c['nodes'])} nodes ({leaves} leaves)")
print(f"data.js ~{out.stat().st_size // 1024}KB")
