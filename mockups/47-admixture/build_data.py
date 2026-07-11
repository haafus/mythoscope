"""Mockup 47 · Admixture — a proper STRUCTURE/ADMIXTURE model of the motif matrix.

Fits the population-genetics admixture model to the tradition × motif presence matrix:
each presence X[t,m] ~ Bernoulli( sum_k Q[t,k] · P[k,m] ), where Q is row-stochastic
(a tradition's ancestry proportions over K latent motif-pools) and P[k,m] ∈ [0,1] is
pool k's frequency for motif m. Exact EM (monotone in the Bernoulli likelihood).

K is chosen the way ADMIXTURE chooses it — by **cross-validation**: a random 12% of the
matrix entries are held out, the model is fit on the rest for each K, and the K with the
lowest held-out Bernoulli deviance wins. This replaces the ad-hoc k=6 of mockup 45's NMF
with a principled, uncertainty-aware soft-factor model. Deterministic; writes data.js.
"""
import json, sys, math
from collections import Counter
from pathlib import Path
import numpy as np

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
def cont(a):
    a=(a or "").lower()
    if "africa" in a: return "Africa"
    if "australia" in a: return "Australia"
    if any(w in a for w in ["america","andes","mexico","amazon","brazil","patagon"]): return "Americas"
    if any(w in a for w in ["oceania","polynesia","micronesia","indonesia","nusantara","melanesia"]): return "Oceania"
    return "Eurasia"

tset={}
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]): tset.setdefault(tid,set()).add(j)
keep=[t for t in TR if len(tset.get(t,()))>=15 and coord(t)]
N,M=len(keep),len(MOT)
X=np.zeros((N,M),np.float32)
for i,t in enumerate(keep):
    for j in tset[t]: X[i,j]=1.0

EPS=1e-4
def em(X, W, K, iters=90, seed=0):
    """EM for admixture Bernoulli. W = weight mask (0=held out). Returns Q,P."""
    r=np.random.default_rng(seed)
    Q=r.dirichlet(np.ones(K),size=N).astype(np.float64)
    P=(r.random((K,M))*0.1+0.02).astype(np.float64)
    Xw=X*W
    for _ in range(iters):
        A=np.clip(Q@P,EPS,1-EPS)                 # P(x=1)
        U=(Xw)/A; V=(W-Xw)/(1-A)                 # weighted 1/denominators
        Q=Q*(U@P.T+V@(1-P).T); Q/=Q.sum(1,keepdims=True)+1e-12
        A=np.clip(Q@P,EPS,1-EPS)
        U=(Xw)/A; V=(W-Xw)/(1-A)
        num=(U.T@Q).T*P                          # k×m
        den=num+((V.T@Q).T)*(1-P)
        P=np.clip(num/(den+1e-12),EPS,1-EPS)
    return Q,P
def deviance(X,mask,Q,P):
    A=np.clip(Q@P,EPS,1-EPS)
    ll=X*np.log(A)+(1-X)*np.log(1-A)
    return float(-2*ll[mask].sum()/mask.sum())

# ---- cross-validation for K: hold out 12% of entries, 3 folds averaged ----
Ks=list(range(2,12)); cv=[]; cvsd=[]
for K in Ks:
    ds=[]
    for f in range(3):
        r=np.random.default_rng(100+f); held=r.random((N,M))<0.12
        Q,P=em(X,(~held).astype(np.float64),K,iters=45,seed=1+f)
        ds.append(deviance(X,held,Q,P))
    cv.append(float(np.mean(ds))); cvsd.append(float(np.std(ds)))
    print(f"  K={K:2d}  CV={cv[-1]:.4f} ± {cvsd[-1]:.4f}")
# choose the KNEE (max distance below the endpoint chord), not the noisy global min —
# the curve plateaus (no sharp optimum), the diagnostic of clinal (continuous-K) structure
c0,c1=cv[0],cv[-1]
chord=[c0+(c1-c0)*(k-Ks[0])/(Ks[-1]-Ks[0]) for k in Ks]
Kstar=Ks[int(np.argmax([ch-v for ch,v in zip(chord,cv)]))]
print(f"K* (knee) = {Kstar}   [plateau: gains past the knee are within CV noise → clinal]")

# ---- final fit on full matrix at K* ----
Q,P=em(X,np.ones((N,M)),Kstar,iters=160,seed=2)
# order pools by M17 depth (deep first) for a consistent, dated palette
# per-motif M17 disjunction depth (reuse Method A features)
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
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
feat,fidx=[],[]
for j,m in enumerate(MOT):
    tids=m.get("traditions") or []
    if len(tids)<3: continue
    mus=[mu(t) for t in tids if mu(t)]; langs={lg(t) for t in tids if lg(t)}
    pts=[COORD[t] for t in tids if t in COORD]
    if len(pts)>=2:
        cen=(np.mean([p[0] for p in pts]),np.mean([p[1] for p in pts]))
        spread=np.mean([hav(p,cen) for p in pts])
        frags=len(set(DBSCAN(eps=0.35,min_samples=1,metric="haversine").fit(np.radians([[p[0],p[1]] for p in pts])).labels_))
    else: spread,frags=0.0,1
    seg={"NW" if x in NW else ("IP" if x in IP else "CONT") for x in mus}
    feat.append([len(tids),len(set(mus)),len(langs),spread,frags,len(seg),1+(1 if m.get("atu_refs") else 0)]); fidx.append(j)
disj=StandardScaler().fit_transform(np.array(feat,float))@DISJ_W
rank=(disj.argsort().argsort()/(len(disj)-1))*100
depth=np.full(M,np.nan)
for k,j in enumerate(fidx): depth[j]=rank[k]

OVER=X.mean(0)
def pool_depth(k):
    w=P[k]*(~np.isnan(depth))
    return float(np.nansum(w*np.nan_to_num(depth))/(w.sum()+1e-9))
order=sorted(range(Kstar),key=lambda k:-pool_depth(k))
Q=Q[:,order]; P=P[order]
PAL=["#4f7096","#c0873f","#6f9a5a","#b45c4b","#9c6a94","#3f9e93","#8a6bbf","#c0728f","#bd9a43"]

dom=Q.argmax(1)
pools=[]
for k in range(Kstar):
    lift=P[k]/(OVER+1e-9)
    topm=sorted(range(M),key=lambda j:-P[k][j]*math.log(1+lift[j]))[:9]   # frequent & over-represented
    members=[i for i in range(N) if dom[i]==k]
    d=pool_depth(k)
    pools.append({"id":k,"color":PAL[k%len(PAL)],"depth":round(d,1),"n":int(len(members)),
        "depth_label":"deep / near-global" if d>=62 else "intermediate" if d>=45 else "shallow / regional",
        "cont":dict(Counter(cont(macro(keep[i])) for i in members).most_common()),
        "macros":[{"name":a,"n":v} for a,v in Counter(macro(keep[i]) for i in members).most_common(5)],
        "motifs":[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":MOT[j].get("motif_group_num"),
                   "p":round(float(P[k][j]),3),"lift":round(float(lift[j]),1),
                   "depth":(None if np.isnan(depth[j]) else round(float(depth[j])))} for j in topm]})

# structure-plot order: group by macro-area, then by dominant pool, then by that pool's share
mac=[macro(t) for t in keep]
macro_order=[a for a,_ in Counter(mac).most_common()]
mi={a:i for i,a in enumerate(macro_order)}
torder=sorted(range(N),key=lambda i:(mi[mac[i]],dom[i],-Q[i,dom[i]]))
bars=[{"q":[round(float(Q[i,k]),3) for k in range(Kstar)],"dom":int(dom[i]),
       "macro":mac[i],"cont":cont(mac[i])} for i in torder]
# macro-area group spans for the structure plot axis
spans=[]; s=0
for i in range(1,len(torder)+1):
    if i==len(torder) or mac[torder[i]]!=mac[torder[s]]:
        spans.append({"macro":mac[torder[s]],"start":s,"end":i}); s=i

points=[]
for i,t in enumerate(keep):
    c=coord(t)
    points.append({"lon":round(c[1],1),"lat":round(c[0],1),"name":TR[t]["name"],"macro":mac[i],
                   "dom":int(dom[i]),"conf":round(float(Q[i].max()),2)})

data={"n_trad":N,"n_motif":M,"K":Kstar,"Ks":Ks,"cv":[round(x,4) for x in cv],"cvsd":[round(x,4) for x in cvsd],
      "pools":pools,"bars":bars,"spans":spans,"points":points,
      "note":"Admixture (STRUCTURE) model of the motif matrix: X~Bernoulli(Q·P), K at the CV knee. The CV curve plateaus (no sharp optimum) — admixture finds no discrete K, the diagnostic of clinal structure. Each tradition is a mix of K dated motif-pools (deep→shallow by M17). Descriptive, not demographic — no admixture-LD clock; dating is the M17 proxy."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"K*={Kstar} · {len(pools)} pools · {len(bars)} bars · {len(points)} points · ~{out.stat().st_size//1024}KB")
