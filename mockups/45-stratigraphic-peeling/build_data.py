"""Mockup 45 · Stratigraphic peeling — data build.

Coverage-corrected recursive peel (hard layers) + NMF soft factors + a proxy depth
index and bootstrap stability per layer. Honest framing: the structure is clinal, so
the tree is a discretisation, not discrete strata — hence soft factors alongside, and
external validation (stability, breadth-based dating proxy) rather than internal stops.
"""
import json, sys, math
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.decomposition import NMF

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402

MIN_NODE, MIN_CHILD, DEPTH = 40, 8, 3
# leaf palette: 8 maximally-distinct hues (no two adjacent blues)
PAL = ["#4f7096","#c9873f","#6f9a5a","#b45c4b","#9c6a94","#bd9a43","#3f9e93","#8a6bbf",
       "#c0728f","#5b9bd5","#d08b4f","#7fa86b"]
SHORT = {
  "North America: North And West":"N American","Plains And Southeast":"Plains / SE American",
  "Mexico – Central Andes":"Mesoamerican / Andean","Eastern South America":"Amazonian / E-S American",
  "Southern South America":"Southern Cone","Sub-Saharan Africa":"Sub-Saharan Africa",
  "Western Europe, North Africa":"W-Europe / N-Africa","Northern And Eastern Europe":"N & E Europe",
  "Southwest And Central Asia, Aryan India":"SW & C Asia / India",
  "Tibet, Non-Aryan South Asia, Southeast Asia":"Tibet / SE Asia","East Asia":"East Asia",
  "Siberia – Mongolia":"Siberia–Mongolia","Oceania":"Oceania","Beringia":"Beringia","Australia":"Australia",
}

bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
def macro(t):
    ap=t.get("areal_path") or []; return ap[0][1].title() if ap and ap[0] else "?"
macro_of={tid:macro(t) for tid,t in TR.items()}
def cont(a):
    a=a.lower()
    if "africa" in a: return "Africa"
    if "australia" in a: return "Australia"
    if any(w in a for w in ["america","andes","mexico","amazon","brazil","patagon"]): return "Americas"
    if any(w in a for w in ["oceania","polynesia","micronesia","indonesia","nusantara","melanesia"]): return "Oceania"
    return "Eurasia"
def coord(tid):
    if tid in COORD: return COORD[tid]
    parts=tid.split(".")
    for i in range(len(parts)-1,0,-1):
        k=".".join(parts[:i])
        if k in COORD: return COORD[k]
    return None

tset={}
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]): tset.setdefault(tid,set()).add(j)
keep=[tid for tid in TR if len(tset.get(tid,()))>=15]
N,M=len(keep),len(MOT)
Xb=np.zeros((N,M),dtype=np.float32)
for i,tid in enumerate(keep):
    for j in tset[tid]: Xb[i,j]=1.0
IDF=np.log((N+1)/(Xb.sum(0)+1))+1.0
def correct(X): return (X/(X.sum(1,keepdims=True)+1e-9))*IDF
Xc=correct(Xb)
OVER=Xb.mean(0)

def ward_route(V):
    active=np.arange(len(V)); routed=[]
    for _ in range(6):
        lab=AgglomerativeClustering(n_clusters=2,linkage="ward").fit(V[active]).labels_
        sz=Counter(lab); sm=min(sz,key=sz.get)
        if sz[sm]>=MIN_CHILD or len(active)<=MIN_NODE:
            full=np.full(len(V),-1); full[active]=lab; return full,routed
        routed+=list(active[lab==sm]); active=active[lab!=sm]
    full=np.full(len(V),-1); full[active]=0; return full,routed

def core_motifs(idx, topn=8):
    prev=Xb[idx].mean(0); lift=prev/(OVER+1e-9)
    cand=sorted([j for j in range(M) if prev[j]>=0.30], key=lambda j:-lift[j])[:topn]
    out=[]
    for j in cand:
        m=MOT[j]; macs={macro_of[keep[i]] for i in idx if Xb[i,j]>0}
        out.append({"id":m["id"],"name":m["name"],"grp":m["motif_group_num"],
                    "lift":round(float(lift[j]),1),"breadth":len({cont(x) for x in macs})})
    return out

def depth_proxy(idx):
    """breadth of core motifs across continents -> proxy for age (broad+disjunct=deep)."""
    cm=core_motifs(idx,12)
    if not cm: return 0.0,"—"
    b=np.mean([c["breadth"] for c in cm])          # 1..5 continents
    lbl = "deep / near-global" if b>=3.5 else "broad / inter-regional" if b>=2.2 else "regional / shallow"
    return round(float(b),2), lbl

def name_of(idx, level, is_leaf):
    c=Counter(cont(macro_of[keep[i]]) for i in idx); top=[k for k,_ in c.most_common(2)]
    frac=lambda k: c.get(k,0)/len(idx)
    if level==0: return "All traditions"
    # leaves get a concrete macro-area name so sibling blocks don't collide
    if is_leaf:
        mac=Counter(macro_of[keep[i]] for i in idx).most_common(1)[0][0]
        base=SHORT.get(mac, mac)
        if frac("Oceania")>0.3: return "Indo-Pacific"
        return base
    if level==1: return "New World" if frac("Americas")>0.5 else "Old World"
    if frac("Oceania")>0.25: return "Indo-Pacific"
    if frac("Americas")>0.7: return "American cosmology"
    if frac("Americas")>0.25 and frac("Eurasia")>0.25: return "Beringian / circum-Pacific bridge"
    if frac("Africa")>0.25 and frac("Eurasia")>0.4: return "W-Eurasian + N-African tale belt"
    if frac("Eurasia")>0.6: return "Eurasian märchen"
    return "+".join(top)

nodes=[]; leaf_of={}   # tradition index -> leaf node id
def peel(idx, nid, parent, level):
    n=len(idx); V=correct(Xb[idx])
    lab,routed=ward_route(V); m=lab>=0
    sil = float(silhouette_score(V[m],lab[m])) if len(set(lab[m]))>1 else 0.0
    is_leaf = (n<MIN_NODE) or (level>=DEPTH) or (len(set(lab[m]))<2)
    di,dl = depth_proxy(idx)
    node={"id":nid,"parent":parent,"level":level,"name":name_of(idx,level,is_leaf),"n":n,
          "sil":round(sil,3),"leaf":is_leaf,
          "cont":dict(Counter(cont(macro_of[keep[i]]) for i in idx).most_common()),
          "macros":[{"name":a,"n":v} for a,v in Counter(macro_of[keep[i]] for i in idx).most_common(6)],
          "themes":[{"grp":g,"n":v} for g,v in Counter(c["grp"] for c in core_motifs(idx,20)).most_common()],
          "core":core_motifs(idx,8),"depth_index":di,"depth_label":dl}
    nodes.append(node)
    if is_leaf:
        for i in idx: leaf_of[i]=nid
        return
    gs=sorted([[idx[i] for i in range(n) if lab[i]==c] for c in sorted(set(lab[m]))],key=len)
    for gi,g in enumerate(gs):
        peel(g, f"{nid}.{gi}", nid, level+1)

peel(list(range(N)), "0", None, 0)

# ---- bootstrap stability per node (subsample 80%, re-peel, max Jaccard) ----
def full_peel(sub_idx):
    parts=[]
    def rec(idx,level):
        V=correct(Xb[idx]); lab,_=ward_route(V); m=lab>=0
        if len(idx)<MIN_NODE or level>=DEPTH or len(set(lab[m]))<2:
            parts.append(set(keep[i] for i in idx)); return
        for c in sorted(set(lab[m])):
            rec([idx[i] for i in range(len(idx)) if lab[i]==c], level+1)
    rec(sub_idx,0); return parts
leaf_sets={nd["id"]:set(keep[i] for i in leaf_of if leaf_of[i]==nd["id"]) for nd in nodes if nd["leaf"]}
B=12; stab={k:[] for k in leaf_sets}
rng=np.random.default_rng(0)
for _ in range(B):
    sub=sorted(rng.choice(N,int(0.8*N),replace=False))
    parts=full_peel(sub)
    for k,orig in leaf_sets.items():
        o=orig & set(keep[i] for i in sub)
        if not o: continue
        best=max((len(o&p)/len(o|p) for p in parts), default=0.0)
        stab[k].append(best)
for nd in nodes:
    if nd["leaf"]:
        s=stab.get(nd["id"],[]); nd["stability"]=round(float(np.mean(s)),2) if s else None

# ---- NMF soft factors (the "clinal" representation) ----
K=6
W=NMF(n_components=K,init="nndsvda",max_iter=400,random_state=0).fit_transform(Xc)
Hn=NMF(n_components=K,init="nndsvda",max_iter=400,random_state=0).fit(Xc).components_
factors=[]
for f in range(K):
    topm=np.argsort(-Hn[f])[:8]
    topt=np.argsort(-W[:,f])[:12]
    macs=Counter(cont(macro_of[keep[i]]) for i in topt)
    factors.append({"id":f,"color":PAL[(f+7)%len(PAL)],
        "cont":dict(macs.most_common()),
        "motifs":[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":MOT[j]["motif_group_num"]} for j in topm],
        "trads":[TR[keep[i]]["name"] for i in topt]})
# match each leaf to dominant factor
dom=W.argmax(1)
for nd in nodes:
    if nd["leaf"]:
        members=[i for i in leaf_of if leaf_of[i]==nd["id"]]
        nd["factor"]=int(Counter(dom[i] for i in members).most_common(1)[0][0]) if members else None

# ---- points for the map (colored by leaf) ----
leaves=[nd for nd in nodes if nd["leaf"]]
lcolor={nd["id"]:PAL[i%len(PAL)] for i,nd in enumerate(leaves)}
for nd in nodes:
    if nd["leaf"]: nd["color"]=lcolor[nd["id"]]
points=[]
for i,tid in enumerate(keep):
    c=coord(tid); lid=leaf_of.get(i)
    if c and lid:
        points.append({"lon":round(c[1],2),"lat":round(c[0],2),"leaf":lid,
                       "name":TR[tid]["name"],"macro":macro_of[tid]})

data={"n_trad":N,"n_motif":M,"depth":DEPTH,"nodes":nodes,"points":points,"factors":factors,
      "note":"Coverage-corrected recursive peel (L1+idf). Structure is clinal; tree is a discretisation."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"{len(nodes)} nodes ({len(leaves)} leaves) · {len(points)} placed · {K} factors · data.js ~{out.stat().st_size//1024}KB")
