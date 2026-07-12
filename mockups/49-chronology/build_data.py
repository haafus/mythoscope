"""Mockup 49 · Chronology — can we put a (relative) time axis on the motifs?

Three complementary views over one build, following docs/research/dating-and-chronology-methods.md:

  1. DATABILITY — which motifs are tree-like (clumped on Berezkin's areal taxonomy) enough to
     order/date, vs reticulate (dispersed = diffused or pan-global substrate). Per-motif NRI
     (net relatedness: MPD z-score vs a size-matched null on the areal tree).
  2. BARRIER FLOORS — absolute year lower-bounds from biogeographic barriers: a motif shared
     across a barrier (trans-Beringian ≥~15 ka, pan-American ≥~13 ka, Sahul ≥~50 ka contested)
     is no younger than the crossing. These few anchors also root the ordering's polarity.
  3. PSEUDO-CHRONOLOGY — a consensus relative order from several independent ordinations
     (CA seriation, diffusion-map pseudotime, M17 breadth, prevalence), rooted by the barrier
     anchors, with per-motif agreement bands and validation (barrier-old / ATU-young checks).

Descriptive: ordering needs a polarity assumption, and diffusion still confounds breadth.
Deterministic; writes data.js.
"""
import json, sys, math
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402

rng = np.random.default_rng(0)
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
def coord(tid):
    if tid in COORD: return COORD[tid]
    p=tid.split(".")
    for i in range(len(p)-1,0,-1):
        k=".".join(p[:i])
        if k in COORD: return COORD[k]
    return None
def macro(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1] if ap and ap[0] else "?"
def cont(t):
    a=macro(t).lower()
    if "africa" in a and "north" not in a: return "Africa"
    if "australia" in a: return "Australia"
    if any(w in a for w in ["america","andes","mexico","amazon","brazil","patagon","beringia"]): return "Americas"
    if any(w in a for w in ["oceania","polynesia","micronesia","indonesia","nusantara","melanesia"]): return "Oceania"
    return "Eurasia"

tset={}
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]): tset.setdefault(tid,set()).add(j)
keep=[t for t in TR if len(tset.get(t,()))>=15 and coord(t)]
N,M=len(keep),len(MOT)
ki={t:i for i,t in enumerate(keep)}
X=np.zeros((N,M),np.float32)
for i,t in enumerate(keep):
    for j in tset[t]: X[i,j]=1.0
prev=X.sum(0)                                   # attestations per motif

# ---- areal-taxonomy tree distance (patristic on the dotted-code hierarchy) ----
paths=[t.split(".") for t in keep]
def tdist(a,b):
    s=0
    for x,y in zip(a,b):
        if x==y: s+=1
        else: break
    return (len(a)-s)+(len(b)-s)
Dt=np.zeros((N,N),np.int16)
for i in range(N):
    for j in range(i+1,N):
        d=tdist(paths[i],paths[j]); Dt[i,j]=Dt[j,i]=d

# ---- 1. DATABILITY: NRI (net relatedness index) per motif on the areal tree ----
# null MPD mean/std by set size, from random samples
sizes=sorted(set(int(p) for p in prev if p>=3))
iu_full=np.triu_indices(N,1)
def mpd(idx):
    if len(idx)<2: return np.nan
    sub=Dt[np.ix_(idx,idx)]; return sub[np.triu_indices(len(idx),1)].mean()
null_mu={}; null_sd={}
grid=sorted(set(min(s,120) for s in sizes))
for s in grid:
    vals=[mpd(rng.choice(N,s,replace=False)) for _ in range(150)]
    null_mu[s]=float(np.mean(vals)); null_sd[s]=float(np.std(vals)+1e-9)
def nearest(s): return min(grid,key=lambda g:abs(g-s))
nri=np.full(M,np.nan); nmac=np.zeros(M,int)
for j in range(M):
    tids=[t for t in MOT[j].get("traditions",[]) if t in ki]
    nmac[j]=len({macro(t) for t in tids})
    idx=[ki[t] for t in tids]
    if len(idx)<3: continue
    g=nearest(min(len(idx),120))
    nri[j]=-(mpd(idx)-null_mu[g])/null_sd[g]     # high = clade-concentrated (recent); ~0 = spread (substrate)

# ---- 2. BARRIER FLOORS ----
BARRIER=[("Sahul",50000,"contested"),("trans-Beringian",15000,"solid"),
         ("pan-American",13000,"solid")]
def floor_of(j):
    tids=[t for t in MOT[j].get("traditions",[]) if t in ki]
    c=Counter(cont(t) for t in tids)
    amE=c.get("Americas",0); eur=c.get("Eurasia",0); afr=c.get("Africa",0)
    oce=c.get("Oceania",0); aus=c.get("Australia",0)
    oldworld=eur+afr+oce
    # require >=2 on the minority side to avoid a single stray attestation
    if aus>=2 and (eur+afr+oce+amE)>=2:
        return ("Sahul",50000,"contested")
    if amE>=2 and oldworld>=2:
        return ("trans-Beringian",15000,"solid")
    # pan-American: both a northern and a southern American area
    NAM={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","BERINGIA"}
    SAM={"EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","MEXICO – CENTRAL ANDES"}
    macs=[macro(t) for t in tids]
    if sum(m in NAM for m in macs)>=2 and sum(m in SAM for m in macs)>=2:
        return ("pan-American",13000,"solid")
    return (None,0,None)
bfloor=[floor_of(j) for j in range(M)]
barrier_anchor=np.array([bf[1]>=13000 for bf in bfloor])   # motifs that root polarity (old)

# ---- 3. PSEUDO-CHRONOLOGY: several orderings on motifs attested >=5 ----
sel=np.where(prev>=5)[0]; Xs=X[:,sel]
# CA seriation (first non-trivial axis) — motif col coords
Pm=Xs/Xs.sum()
r=Pm.sum(1,keepdims=True); c=Pm.sum(0,keepdims=True)
S=(Pm-r@c)/np.sqrt(r@c+1e-12)
U,sv,Vt=np.linalg.svd(S,full_matrices=False)
ca=(Vt[0]/np.sqrt(c.ravel()+1e-12))              # motif scores, axis 1
# diffusion-map pseudotime on motifs (cosine graph, 2nd eigenvector)
Xn=Xs/ (np.linalg.norm(Xs,axis=0,keepdims=True)+1e-9)
Aff=(Xn.T@Xn).astype(np.float64); np.fill_diagonal(Aff,0)
d=Aff.sum(1)+1e-9; Msym=Aff/np.sqrt(np.outer(d,d))
w,V=np.linalg.eigh(Msym)
dm=V[:,-2]                                        # first non-trivial diffusion coordinate
# M17 disjunction depth (Method A) restricted to sel
NW={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","MEXICO – CENTRAL ANDES",
    "EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","BERINGIA"}; IP={"OCEANIA","AUSTRALIA"}
DISJ_W=np.array([-1.0,-0.5,1.0,0.5,0.8,1.0,0.0])
def mu(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1].upper() if ap else None
def lg(t):
    l=TR[t].get("language") or []; return l[0] if l else None
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,[a[0],a[1],b[0],b[1]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371*math.asin(min(1,math.sqrt(h)))
feat=[]
for j in sel:
    m=MOT[j]; tids=m.get("traditions") or []
    mus=[mu(t) for t in tids if mu(t)]; langs={lg(t) for t in tids if lg(t)}
    pts=[COORD[t] for t in tids if t in COORD]
    if len(pts)>=2:
        cen=(np.mean([p[0] for p in pts]),np.mean([p[1] for p in pts]))
        spread=np.mean([hav(p,cen) for p in pts])
        frags=len(set(DBSCAN(eps=0.35,min_samples=1,metric="haversine").fit(np.radians([[p[0],p[1]] for p in pts])).labels_))
    else: spread,frags=0.0,1
    seg={"NW" if x in NW else ("IP" if x in IP else "CONT") for x in mus}
    feat.append([len(tids),len(set(mus)),len(langs),spread,frags,len(seg),1+(1 if m.get("atu_refs") else 0)])
m17=StandardScaler().fit_transform(np.array(feat,float))@DISJ_W
prevsel=prev[sel]
# rank each ordering in [0,1]; root so barrier-anchor motifs sit at the OLD (high) end
anchor_sel=barrier_anchor[sel]
def to_rank(v):
    r=v.argsort().argsort()/(len(v)-1)
    if anchor_sel.sum()>=5 and r[anchor_sel].mean()<0.5: r=1-r
    return r
methods={"CA seriation":to_rank(ca),"Diffusion pseudotime":to_rank(dm),
         "M17 breadth":to_rank(m17),"Prevalence":to_rank(prevsel.astype(float))}
R=np.vstack(list(methods.values()))
consensus=R.mean(0); agree=1-2*R.std(0)          # 1=methods agree, →0 disagree
# spearman corr between methods
def spear(a,b):
    ra=a.argsort().argsort(); rb=b.argsort().argsort()
    ra=ra-ra.mean(); rb=rb-rb.mean(); return float((ra@rb)/(np.sqrt((ra@ra)*(rb@rb))+1e-12))
mk=list(methods); cm=[[round(spear(methods[a],methods[b]),2) for b in mk] for a in mk]
# DIAGNOSTIC: how much is each ordering just geography? corr with New-World share of the motif
nw_share=np.array([ (lambda tl:(sum(cont(t)=="Americas" for t in tl)/max(1,len(tl))))(
    [t for t in MOT[j].get("traditions",[]) if t in ki]) for j in sel])
geo_corr={m:round(spear(methods[m],nw_share),2) for m in mk}
# validation
atu_sel=np.array([bool(MOT[j].get("atu_refs")) for j in sel])
val={"barrier_old_rank":round(float(consensus[anchor_sel].mean()),3) if anchor_sel.sum() else None,
     "overall_rank":round(float(consensus.mean()),3),
     "atu_young_rank":round(float(consensus[atu_sel].mean()),3) if atu_sel.sum() else None,
     "n_anchor":int(anchor_sel.sum()),"n_atu":int(atu_sel.sum())}

# ---- assemble payload ----
def gname(j): return MOT[j].get("motif_group_num")
# datability = which dating ROUTE applies (not datable-vs-not: areal clustering is near-universal)
scored=~np.isnan(nri)
has_floor=np.array([bf[1]>0 for bf in bfloor])
route=np.full(M,"",object)
for j in range(M):
    if not scored[j]: continue
    if has_floor[j]: route[j]="barrier"                       # crosses a barrier → absolute floor
    elif nri[j]>=3 and nmac[j]<=2: route[j]="tree"            # clade-concentrated → language/phylogeny
    else: route[j]="weak"                                     # spread, no clean barrier → weakly datable
nri_ok=nri[scored]
clip=np.clip(nri_ok,-2,12)
def ex(mask, key, rev):
    js=[j for j in range(M) if scored[j] and route[j]==mask]
    js=sorted(js,key=lambda j:(-nri[j] if rev else nri[j]))[:10]
    return [{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":gname(j),"nri":round(float(nri[j]),1),
             "nmac":int(nmac[j]),"n":int(prev[j])} for j in js]
# cross-link: NRI (recency) vs consensus age over the ordered set
nri_sel=nri[sel]; ok=~np.isnan(nri_sel)
def spear2(a,b):
    ra=a.argsort().argsort().astype(float); rb=b.argsort().argsort().astype(float)
    ra-=ra.mean(); rb-=rb.mean(); return float((ra@rb)/(np.sqrt((ra@ra)*(rb@rb))+1e-12))
r_nri_age=round(spear2(nri_sel[ok],consensus[ok]),2)
data_datability={
  "hist":[int(((clip>=lo)&(clip<lo+1)).sum()) for lo in range(-2,12)],
  "bins":list(range(-2,12)),"median_nri":round(float(np.median(nri_ok)),1),
  "frac_clustered":round(float((nri_ok>0).mean()),3),
  "n_scored":int(scored.sum()),
  "routes":{"barrier":int((route=="barrier").sum()),"tree":int((route=="tree").sum()),"weak":int((route=="weak").sum())},
  "r_nri_age":r_nri_age,
  "tree":ex("tree","nri",True),"barrier":ex("barrier","nri",False),"weak":ex("weak","nri",False)}
# barriers: counts + examples + per-tradition oldest floor (for the map)
tier_count=Counter(bf[0] for bf in bfloor if bf[0])
examples={}
for tier,yr,conf in BARRIER:
    js=[j for j in range(M) if bfloor[j][0]==tier]
    js=sorted(js,key=lambda j:-prev[j])[:10]
    examples[tier]=[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":gname(j),"n":int(prev[j]),
                     "nri":(None if np.isnan(nri[j]) else round(float(nri[j]),1))} for j in js]
trad_floor=np.zeros(N)
for j in range(M):
    if bfloor[j][1]>0:
        for t in MOT[j].get("traditions",[]):
            if t in ki: trad_floor[ki[t]]=max(trad_floor[ki[t]],bfloor[j][1])
tpoints=[]
for i,t in enumerate(keep):
    c=coord(t); tpoints.append({"lon":round(c[1],1),"lat":round(c[0],1),"floor":int(trad_floor[i]),
                                "name":TR[t]["name"]})
data_barriers={"tiers":[{"name":t,"yr":y,"conf":cf,"n":int(tier_count.get(t,0))} for t,y,cf in BARRIER],
               "examples":examples,"points":tpoints,
               "n_floored":int(sum(1 for bf in bfloor if bf[1]>0))}
# chronology: ribbon (motifs sorted by consensus) + method corr + validation
order=np.argsort(consensus)
ribbon=[{"c":round(float(consensus[k]),3),"a":round(float(max(0,agree[k])),2),
         "d":(None if np.isnan(nri[sel[k]]) else round(float(nri[sel[k]]),1)),
         "anc":bool(anchor_sel[k]),"atu":bool(atu_sel[k])} for k in order]
labels=[]
for k in list(order[:14])+list(order[-14:]):
    j=sel[k]; labels.append({"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":gname(j),
        "c":round(float(consensus[k]),3),"a":round(float(max(0,agree[k])),2),
        "anc":bool(anchor_sel[k]),"atu":bool(atu_sel[k])})
data_chrono={"n":int(len(sel)),"methods":mk,"corr":cm,"geo_corr":geo_corr,
             "mean_agree":round(float(np.mean(np.clip(agree,0,1))),2),"ribbon":ribbon,"labels":labels,"val":val}

data={"n_trad":N,"n_motif":M,"n_ordered":int(len(sel)),
      "datability":data_datability,"barriers":data_barriers,"chronology":data_chrono,
      "note":"Chronology: (1) datability = NRI clustering on the areal tree; (2) barrier year-floors (trans-Beringian ≥15ka, pan-American ≥13ka, Sahul ≥50ka contested); (3) consensus pseudo-order from CA/diffusion/M17/prevalence, rooted by barrier anchors, with agreement bands. Descriptive — ordering needs a polarity assumption; diffusion confounds breadth."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"routes {data_datability['routes']} / {data_datability['n_scored']} scored · r(NRI,age)={data_datability['r_nri_age']} | "
      f"floored {data_barriers['n_floored']} ({dict(tier_count)}) | ordered {len(sel)} | "
      f"val barrier-old={val['barrier_old_rank']} atu-young={val['atu_young_rank']} overall={val['overall_rank']} | ~{out.stat().st_size//1024}KB")
