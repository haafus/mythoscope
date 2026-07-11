"""Mockup 46 · Migration surface — population-genetics view of the motif matrix.

Treats the tradition × motif presence matrix like a landscape-genetics dataset and
borrows three standard tools:

  * Mantel test — isolation-by-distance (motif dissimilarity vs geographic distance),
    with a permutation p-value;
  * AMOVA / Fst-analog — fraction of motif variance between Berezkin macro-areas,
    with a permutation p-value, plus the pairwise area Fst matrix;
  * EEMS-lite — an effective-migration surface: the residual of the isolation-by-
    distance fit mapped in space. Positive residual = more dissimilar than distance
    predicts = a BARRIER (low effective migration); negative = a CORRIDOR. Plus the
    strongest long-range corridors ("bridges") drawn as edges.

Descriptive re-encoding, not a demographic model: cultural transmission is horizontal
and biased, so the drift null is only analogical. Deterministic; writes data.js.
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

tset={}
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]): tset.setdefault(tid,set()).add(j)
keep=[t for t in TR if len(tset.get(t,()))>=15 and coord(t)]
N,M=len(keep),len(MOT)
X=np.zeros((N,M),np.float32)
for i,t in enumerate(keep):
    for j in tset[t]: X[i,j]=1.0
sz=X.sum(1)

# ---- pairwise Jaccard dissimilarity & haversine distance ----
inter=X@X.T
union=sz[:,None]+sz[None,:]-inter
Djac=1.0-inter/np.maximum(union,1.0)
LL=np.radians(np.array([coord(t) for t in keep]))          # (lat, lon)
la,lo=LL[:,0],LL[:,1]
dlat=la[:,None]-la[None,:]; dlon=lo[:,None]-lo[None,:]
hv=np.sin(dlat/2)**2+np.cos(la)[:,None]*np.cos(la)[None,:]*np.sin(dlon/2)**2
Dgeo=2*6371*np.arcsin(np.minimum(1,np.sqrt(hv)))
iu=np.triu_indices(N,1)
dj,dg=Djac[iu],Dgeo[iu]

# ---- Mantel: isolation-by-distance + permutation p ----
def pear(a,b):
    a=a-a.mean(); b=b-b.mean(); return float((a@b)/(math.sqrt((a@a)*(b@b))+1e-12))
r_obs=pear(dj,dg)
PERM=299
cnt=0
for _ in range(PERM):
    p=rng.permutation(N)
    Dp=Djac[np.ix_(p,p)][iu]
    if pear(Dp,dg)>=r_obs: cnt+=1
mantel_p=(cnt+1)/(PERM+1)

# ---- IBD fit (binned monotone) + residuals ----
BW=300.0
edges=np.arange(0,dg.max()+BW,BW)
ctr=(edges[:-1]+edges[1:])/2
binmean=np.full(len(ctr),np.nan)
which=np.clip(np.digitize(dg,edges)-1,0,len(ctr)-1)
for b in range(len(ctr)):
    mm=which==b
    if mm.sum()>=30: binmean[b]=dj[mm].mean()
good=~np.isnan(binmean)
pred_curve=np.interp(ctr,ctr[good],binmean[good])
pred=np.interp(dg,ctr,pred_curve)
resid=dj-pred                                              # + = barrier, - = corridor
decay=[{"km":round(float(c)),"dissim":round(float(v),4)} for c,v in zip(ctr,pred_curve) if c<=20000]

# ---- AMOVA / Fst-analog by macro-area + permutation p + pairwise matrix ----
grp=np.array([macro(t) for t in keep])
areas=sorted(set(grp)); ai={a:i for i,a in enumerate(areas)}
gi=np.array([ai[g] for g in grp])
same=gi[iu[0]]==gi[iu[1]]
Dw,Db,Dt=dj[same].mean(),dj[~same].mean(),dj.mean()
fst=float((Db-Dw)/Db)
cnt=0
for _ in range(PERM):
    gp=gi[rng.permutation(N)]
    sm=gp[iu[0]]==gp[iu[1]]
    if ((dj[~sm].mean()-dj[sm].mean())/dj[~sm].mean())>=fst: cnt+=1
fst_p=(cnt+1)/(PERM+1)
# pairwise area Fst (only areas with >=8 traditions)
big=[a for a in areas if (grp==a).sum()>=8]
pw=[]
for x in range(len(big)):
    for y in range(x+1,len(big)):
        A,B=big[x],big[y]; ia=(gi==ai[A]); ib=(gi==ai[B])
        wa=Djac[np.ix_(ia,ia)][np.triu_indices(ia.sum(),1)].mean()
        wb=Djac[np.ix_(ib,ib)][np.triu_indices(ib.sum(),1)].mean()
        bt=Djac[np.ix_(ia,ib)].mean()
        f=(bt-(wa+wb)/2)/bt
        pw.append({"a":A,"b":B,"fst":round(float(f),3)})

# ---- EEMS-lite: effective-migration surface (IBD residual mapped in space) ----
loc = dg<3500.0                                            # local pairs carry barrier signal
mi,mj=iu[0][loc],iu[1][loc]; rl=resid[loc]
latd=np.degrees(la); lond=np.degrees(lo)
mlat=(latd[mi]+latd[mj])/2
# guard antimeridian (rare for local pairs)
lon_ok=np.abs(lond[mi]-lond[mj])<180
mlon=(lond[mi]+lond[mj])/2
mi,mj,rl,mlat,mlon=mi[lon_ok],mj[lon_ok],rl[lon_ok],mlat[lon_ok],mlon[lon_ok]
# grid, masked to cells near data
STEP=3.0; KB=650.0
glon=np.arange(-180,180+STEP,STEP); glat=np.arange(-58,82+STEP,STEP)
tlat,tlon=latd,lond
def km(alat,alon,blat,blon):
    a1,a2,b1,b2=map(np.radians,[alat,alon,blat,blon])
    h=np.sin((b1-a1)/2)**2+np.cos(a1)*np.cos(b1)*np.sin((b2-a2)/2)**2
    return 2*6371*np.arcsin(np.minimum(1,np.sqrt(h)))
cells=[]
mlat_r=np.radians(mlat); mlon_r=np.radians(mlon)
for gy in glat:
    for gx in glon:
        # near data?
        if km(gy,gx,tlat,tlon).min()>500: continue
        d=km(gy,gx,mlat,mlon)
        near=d<1600
        if near.sum()<12: continue
        w=np.exp(-(d[near]**2)/(2*KB*KB))
        val=float((w*rl[near]).sum()/(w.sum()+1e-9))
        cells.append({"lon":round(float(gx),1),"lat":round(float(gy),1),
                      "v":round(val,4),"n":int(near.sum())})
vv=np.array([c["v"] for c in cells]); vabs=np.percentile(np.abs(vv),90) or 1e-6
for c in cells: c["t"]=round(float(np.clip(c["v"]/vabs,-1,1)),3)   # -1 corridor .. +1 barrier

# ---- strongest long-range corridors (bridges): surprising similarity at distance ----
far = dg>4000.0
fi,fj,fr,fd=iu[0][far],iu[1][far],resid[far],dg[far]
order=np.argsort(fr)                                       # most negative = strongest corridor
seen=set(); edges_out=[]
for k in order:
    a,b=keep[fi[k]],keep[fj[k]]; A,B=macro(a),macro(b)
    key=tuple(sorted((A,B)))
    if key in seen: continue
    seen.add(key)
    ca,cb=coord(a),coord(b)
    edges_out.append({"lat1":round(ca[0],1),"lon1":round(ca[1],1),"lat2":round(cb[0],1),"lon2":round(cb[1],1),
                      "resid":round(float(fr[k]),3),"km":round(float(fd[k])),"a":A,"b":B})
    if len(edges_out)>=28: break

# ---- points (per-tradition mean local residual = how barriered its neighbourhood is) ----
loc_all=Dgeo<3500.0
np.fill_diagonal(loc_all,False)
tr_resid=[]
R=np.full((N,N),np.nan); R[iu]=resid; R.T[iu]=resid
for i in range(N):
    nb=loc_all[i]
    tr_resid.append(float(np.nanmean(R[i][nb])) if nb.sum()>0 else 0.0)
tr=np.array(tr_resid); tabs=np.percentile(np.abs(tr),90) or 1e-6
points=[]
for i,t in enumerate(keep):
    c=coord(t)
    points.append({"lon":round(c[1],1),"lat":round(c[0],1),"name":TR[t]["name"],
                   "macro":macro(t),"t":round(float(np.clip(tr[i]/tabs,-1,1)),3)})

data={"n_trad":N,"n_motif":M,"n_pairs":int(len(dj)),
      "mantel":{"r":round(r_obs,3),"p":round(mantel_p,4),"perm":PERM},
      "fst":{"value":round(fst,3),"p":round(fst_p,4),"within":round(float(Dw),3),
             "between":round(float(Db),3),"n_areas":len(areas)},
      "decay":decay,"pairwise_fst":sorted(pw,key=lambda x:-x["fst"]),
      "cells":cells,"edges":edges_out,"points":points,
      "note":"Population-genetics view: isolation-by-distance (Mantel), AMOVA/Fst by macro-area, and an EEMS-lite effective-migration surface (IBD residual: red=barrier, blue=corridor) with long-range bridges."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"Mantel r={r_obs:.3f} p={mantel_p:.4f} | Fst={fst:.3f} p={fst_p:.4f} | "
      f"{len(cells)} cells · {len(edges_out)} bridges · {len(points)} points · {len(pw)} area-pairs · ~{out.stat().st_size//1024}KB")
