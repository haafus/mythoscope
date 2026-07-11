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
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

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

# ---- per-motif depth score (M17 Method A, disjunction-weighted) ----
NW={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","MEXICO – CENTRAL ANDES",
    "EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","BERINGIA"}
IP={"OCEANIA","AUSTRALIA"}
DISJ_W=np.array([-1.0,-0.5,1.0,0.5,0.8,1.0,0.0])   # n_trad n_macro n_lang spread fragments set_span xindex
def macro_u(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1].upper() if ap else None
def lang0(t):
    lg=TR[t].get("language") or []; return lg[0] if lg else None
def megaset(mu): return "NW" if mu in NW else ("IP" if mu in IP else "CONT")
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,[a[0],a[1],b[0],b[1]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371*math.asin(min(1,math.sqrt(h)))
feat,fidx=[],[]
for j,m in enumerate(MOT):
    tids=m.get("traditions") or []
    if len(tids)<3: continue
    mus=[macro_u(t) for t in tids if macro_u(t)]
    langs={lang0(t) for t in tids if lang0(t)}
    pts=[COORD[t] for t in tids if t in COORD]
    if len(pts)>=2:
        cen=(np.mean([p[0] for p in pts]),np.mean([p[1] for p in pts]))
        spread=np.mean([hav(p,cen) for p in pts])
        frags=len(set(DBSCAN(eps=0.35,min_samples=1,metric="haversine").fit(np.radians([[p[0],p[1]] for p in pts])).labels_))
    else: spread,frags=0.0,1
    feat.append([len(tids),len(set(mus)),len(langs),spread,frags,len({megaset(x) for x in mus}),1+(1 if m.get("atu_refs") else 0)])
    fidx.append(j)
Z=StandardScaler().fit_transform(np.array(feat,dtype=float))
disj=Z@DISJ_W
depth=np.full(M,np.nan); rank=(disj.argsort().argsort()/(len(disj)-1))*100
for k,j in enumerate(fidx): depth[j]=rank[k]     # 0..100 percentile, high=deep

# ---- soft factors: TWO models, both dated by the M17 depth score ----
from sklearn.decomposition import NMF
def fdepth(hk):
    w=hk.copy(); mask=~np.isnan(depth); w=w*mask
    return float(np.nansum(w*np.nan_to_num(depth))/(w.sum()+1e-9))
def build_factors(W,H):
    dom=W.argmax(1); K=W.shape[1]; fl=[]
    for f in range(K):
        topm=np.argsort(-H[f])[:8]; topt=np.argsort(-W[:,f])[:12]
        members=[i for i in range(N) if dom[i]==f]     # FULL dominant membership, not just top-12
        d=fdepth(H[f])
        fl.append({"id":f,"color":PAL[(f+7)%len(PAL)],"depth":round(d,1),"n":len(members),
            "depth_label":"deep / near-global" if d>=62 else "intermediate" if d>=45 else "shallow / regional",
            "cont":dict(Counter(cont(macro_of[keep[i]]) for i in members).most_common()),
            "motifs":[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":MOT[j]["motif_group_num"],
                       "depth":(None if np.isnan(depth[j]) else round(float(depth[j]),0))} for j in topm],
            "trads":[TR[keep[i]]["name"] for i in topt]})
    fl.sort(key=lambda x:-x["depth"])                  # dated stratigraphy: deep first
    old2new={f["id"]:i for i,f in enumerate(fl)}
    for i,f in enumerate(fl): f["id"]=i
    leafmap={}
    for nd in nodes:
        if nd["leaf"]:
            mem=[i for i in leaf_of if leaf_of[i]==nd["id"]]
            leafmap[nd["id"]]=int(old2new[Counter(dom[i] for i in mem).most_common(1)[0][0]]) if mem else None
    return fl, leafmap
K=6
# model 1 — NMF (Euclidean) on the coverage-corrected matrix
nmf=NMF(n_components=K,init="nndsvda",max_iter=400,random_state=0); Wn=nmf.fit_transform(Xc); Hn=nmf.components_
fl_nmf, leaf_nmf = build_factors(Wn, Hn)
# model 2 — M38-style effort-corrected Poisson: P~Poisson(a(t)·(WH)), KL updates
rng0=np.random.default_rng(0); a=Xb.sum(1,keepdims=True); a[a==0]=1
Wp=rng0.random((N,K))+0.1; Hp=rng0.random((K,M))+0.1; ones=np.ones_like(Xb)
for _ in range(220):
    Mh=a*(Wp@Hp)+1e-9; Q=Xb/Mh; Hp*=((a*Wp).T@Q)/(((a*Wp).T@ones)+1e-9)
    Mh=a*(Wp@Hp)+1e-9; Q=Xb/Mh; Wp*=(Q@Hp.T)/((a*(ones@Hp.T))+1e-9)
fl_pois, leaf_pois = build_factors(Wp, Hp)
for nd in nodes:
    if nd["leaf"]:
        nd["factor_nmf"]=leaf_nmf.get(nd["id"]); nd["factor_poisson"]=leaf_pois.get(nd["id"])
factors={"nmf":fl_nmf,"poisson":fl_pois}
factor_info={
  "nmf":{"label":"NMF","desc":"Non-negative matrix factorisation (Euclidean) on the coverage-corrected (L1+idf) matrix. Isolates a clean Austronesian/Oceanic layer, but is not corrected for cataloguing effort by construction."},
  "poisson":{"label":"M38 Poisson","desc":"Effort-corrected Poisson factorisation with an exposure offset a(t) — the M38 form, coverage-corrected by construction. Distributes Oceania across factors rather than isolating it."}}

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

data={"n_trad":N,"n_motif":M,"depth":DEPTH,"nodes":nodes,"points":points,
      "factors":factors,"factor_info":factor_info,
      "note":"Coverage-corrected recursive peel (L1+idf) + two soft-factor models (NMF, M38 Poisson), both dated by the M17 depth score. Structure is clinal; the hard tree is a discretisation."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"{len(nodes)} nodes ({len(leaves)} leaves) · {len(points)} placed · {K} factors · data.js ~{out.stat().st_size//1024}KB")
