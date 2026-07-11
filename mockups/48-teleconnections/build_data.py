"""Mockup 48 · Teleconnections — climate-science view of long-range motif sharing.

Borrows the climate idea of a *teleconnection*: a correlation between distant locations
that survives after the local (distance) trend is removed. Here: pairs of traditions that
share motifs far MORE than their geographic distance predicts. We aggregate these to a
macro-area network — the reticulation that isolation-by-distance leaves unexplained —
detect its communities, and surface the motifs responsible (the disjunct deep substrate).

  * edge weight w(A,B) = mean over long-range (>3000 km) cross-pairs of (predicted - observed)
    Jaccard dissimilarity — how much more similar than distance predicts (a teleconnection);
  * communities = agglomerative clustering of the teleconnection matrix;
  * teleconnector motifs = motifs whose attestations span the most mutually-distant areas,
    ranked by geographic spread, with their M17 disjunction depth.

Deterministic; writes data.js.
"""
import json, sys, math
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402

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

tset={}
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]): tset.setdefault(tid,set()).add(j)
keep=[t for t in TR if len(tset.get(t,()))>=15 and coord(t)]
N,M=len(keep),len(MOT)
X=np.zeros((N,M),np.float32)
for i,t in enumerate(keep):
    for j in tset[t]: X[i,j]=1.0
sz=X.sum(1)

inter=X@X.T; union=sz[:,None]+sz[None,:]-inter
Djac=1.0-inter/np.maximum(union,1.0)
LL=np.radians(np.array([coord(t) for t in keep])); la,lo=LL[:,0],LL[:,1]
hv=np.sin((la[:,None]-la[None,:])/2)**2+np.cos(la)[:,None]*np.cos(la)[None,:]*np.sin((lo[:,None]-lo[None,:])/2)**2
Dgeo=2*6371*np.arcsin(np.minimum(1,np.sqrt(hv)))
iu=np.triu_indices(N,1); dj,dg=Djac[iu],Dgeo[iu]

# IBD fit + residual (predicted - observed = excess similarity when positive)
BW=300.0; edges=np.arange(0,dg.max()+BW,BW); ctr=(edges[:-1]+edges[1:])/2
which=np.clip(np.digitize(dg,edges)-1,0,len(ctr)-1); bm=np.full(len(ctr),np.nan)
for b in range(len(ctr)):
    mm=which==b
    if mm.sum()>=30: bm[b]=dj[mm].mean()
good=~np.isnan(bm); pred_curve=np.interp(ctr,ctr[good],bm[good])
PRED=np.interp(Dgeo,ctr,pred_curve)
EXC=PRED-Djac                                    # + = more similar than distance predicts

# ---- area-level teleconnection matrix (long-range cross-pairs only) ----
cnt=Counter(macro(t) for t in keep)
MINSZ=6                                            # drop singleton/tiny areas (Madagascar=1, ?=3): pure noise
areas=[a for a in sorted(cnt) if a!="?" and cnt[a]>=MINSZ]
ai={a:i for i,a in enumerate(areas)}
gi=np.array([ai.get(macro(t),-1) for t in keep]); A=len(areas)
LONG=3000.0
Wsum=np.zeros((A,A)); Wcnt=np.zeros((A,A))
mask=Dgeo>LONG
for a in range(A):
    ia=np.where(gi==a)[0]
    for b in range(a,A):
        ib=np.where(gi==b)[0]
        sub=np.ix_(ia,ib); mm=mask[sub]
        if mm.sum()<5: continue
        w=EXC[sub][mm].mean()
        Wsum[a,b]=Wsum[b,a]=w; Wcnt[a,b]=Wcnt[b,a]=mm.sum()
# node centroids + sizes
cent={}
for a in areas:
    pts=[coord(t) for t in keep if macro(t)==a]
    cent[a]=(float(np.mean([p[0] for p in pts])),float(np.mean([p[1] for p in pts])))

# communities from the teleconnection matrix (positive part)
Wp=np.clip(Wsum.copy(),0,None); np.fill_diagonal(Wp,0)
dist=Wp.max()-Wp; np.fill_diagonal(dist,0)
NC=4
comm=AgglomerativeClustering(n_clusters=NC,metric="precomputed",linkage="average").fit(dist).labels_
CPAL=["#4f7096","#c0873f","#6f9a5a","#b45c4b","#9c6a94","#3f9e93"]

# ---- per-motif M17 depth (Method A) for teleconnector annotation ----
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
depth={j:rank[k] for k,j in enumerate(fidx)}

# ---- teleconnector motifs: attestations span the most mutually-distant AREAS ----
keepset=set(keep); bigset=set(areas)
tele=[]
for j,m in enumerate(MOT):
    tids=[t for t in (m.get("traditions") or []) if t in keepset]
    macs=set(macro(t) for t in tids) & bigset
    if len(macs)<3 or len(tids)<4: continue
    cs=[cent[a] for a in macs]
    if len(cs)<3: continue
    dsum=[];
    for x in range(len(cs)):
        for y in range(x+1,len(cs)):
            dsum.append(hav(cs[x],cs[y]))
    spread=float(np.mean(dsum))
    tele.append({"id":m["id"],"name":m["name"],"grp":m.get("motif_group_num"),
                 "areas":len(macs),"spread":round(spread),"n":len(tids),
                 "depth":(None if j not in depth else round(float(depth[j])))})
tele.sort(key=lambda x:-(x["spread"]*math.log(1+x["areas"])))
tele=tele[:14]

SHORT={"NORTHERN AND EASTERN EUROPE":"N&E Europe","WESTERN EUROPE, NORTH AFRICA":"W-Europe/N-Afr",
 "SOUTHWEST AND CENTRAL ASIA, ARYAN INDIA":"SW/C-Asia·India","TIBET, NON-ARYAN SOUTH ASIA, SOUTHEAST ASIA":"Tibet/SE-Asia",
 "EAST ASIA":"East Asia","SIBERIA – MONGOLIA":"Siberia–Mongolia","BERINGIA":"Beringia","OCEANIA":"Oceania",
 "AUSTRALIA":"Australia","Sub-Saharan Africa":"Sub-Sah. Africa","NORTH AMERICA: NORTH AND WEST":"N America",
 "PLAINS AND SOUTHEAST":"Plains/SE","MEXICO – CENTRAL ANDES":"Meso/Andes","EASTERN SOUTH AMERICA":"E-S America",
 "SOUTHERN SOUTH AMERICA":"S Cone"}
nodes=[{"area":a,"short":SHORT.get(a,a),"lat":round(cent[a][0],1),"lon":round(cent[a][1],1),
        "n":cnt[a],"comm":int(comm[ai[a]]),"color":CPAL[int(comm[ai[a]])%len(CPAL)]} for a in areas]
# edges: strongest positive teleconnections
elist=[]
for a in range(A):
    for b in range(a+1,A):
        if Wsum[a,b]>0 and Wcnt[a,b]>=5:
            elist.append({"a":areas[a],"b":areas[b],"w":round(float(Wsum[a,b]),4),"n":int(Wcnt[a,b])})
elist.sort(key=lambda e:-e["w"])
wmax=max((e["w"] for e in elist),default=1)
matrix={"areas":[SHORT.get(a,a) for a in areas],
        "W":[[round(float(Wsum[a,b]),4) for b in range(A)] for a in range(A)]}

data={"n_trad":N,"n_motif":M,"n_areas":A,"long_km":LONG,"wmax":round(wmax,4),
      "nodes":nodes,"edges":elist,"matrix":matrix,"tele":tele,"n_comm":NC,
      "note":"Teleconnections: distance-detrended long-range motif sharing (>3000 km). Edge = more similar than isolation-by-distance predicts; communities = agglomerative clustering of the teleconnection matrix; teleconnector motifs are the disjunct, widespread substrate (annotated by M17 depth)."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"{A} areas · {len(elist)} teleconnection edges · {NC} communities · {len(tele)} teleconnector motifs · ~{out.stat().st_size//1024}KB")
