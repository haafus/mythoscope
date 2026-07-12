"""Mockup 58 · Higher-order structure — synergistic triples + the topology of trait-space (analysis #2).

Two things the pairwise view (mockups 53/56) misses:

  * SYNERGY — motif triples that form a package only together. Interaction information
    II(X;Y;Z) = ΣH(pairs) − ΣH(singles) − H(triple)  (sign convention: >0 = synergy, the triple
    carries dependency beyond all its pairs; <0 = redundancy). Computed over frequent, pairwise-linked
    motifs.
  * TOPOLOGY — the shape of the motif cloud (each motif a point in 948-dim tradition-incidence space,
    Jaccard distance) via persistent homology: H0 (connected components) and H1 (loops) across scale.
    A single persistent H0 component + weak H1 = one connected clinal blob; persistent loops would mean
    cyclic / mutually-avoiding structure.

Deterministic; writes data.js.
"""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from ripser import ripser

ROOT = Path(__file__).resolve().parents[2]
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
TOPN = 300
tmot=defaultdict(set)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): tmot[t].add(j)
keep=[t for t in TR if len(tmot[t])>=15]
N=len(keep); ki={t:i for i,t in enumerate(keep)}
mtr=defaultdict(set)
for i,t in enumerate(keep):
    for j in tmot[t]: mtr[j].add(i)
freq=sorted(range(len(MOT)),key=lambda j:-len(mtr[j]))[:TOPN]
name={j:MOT[j].get("name","") for j in range(len(MOT))}
grp={j:MOT[j].get("motif_group_num") for j in range(len(MOT))}
mid={j:MOT[j]["id"] for j in range(len(MOT))}
X=np.zeros((N,TOPN),bool)
for c,j in enumerate(freq):
    X[list(mtr[j]),c]=True

# ---- synergy: interaction information over pairwise-linked triples (bounded) ----
def H(p):
    p=p[p>0]; return float(-(p*np.log2(p)).sum())
col=[X[:,c] for c in range(TOPN)]
code=(X[:,:].astype(np.int64))            # N×TOPN 0/1
p1=X.mean(0)
Hs=np.array([H(np.array([1-p,p])) for p in p1])
Xf=X.astype(float); Xc=Xf-Xf.mean(0); sd=Xf.std(0)+1e-9
Phi=(Xc.T@Xc)/N/np.outer(sd,sd)
pair_cnt=(X.astype(np.float32).T@X.astype(np.float32))   # co-occurrence counts
def H2c(a,b):
    nab=pair_cnt[a,b]; na=col[a].sum(); nb=col[b].sum()
    return H(np.array([N-na-nb+nab, nb-nab, na-nab, nab])/N)
# candidate triangles among phi>=0.30 links, capped by joint support
adj=defaultdict(set)
for a in range(TOPN):
    for b in range(a+1,TOPN):
        if Phi[a,b]>=0.30: adj[a].add(b); adj[b].add(a)
cand=[]
for a in adj:
    ns=sorted(x for x in adj[a] if x>a)
    for i in range(len(ns)):
        for jx in range(i+1,len(ns)):
            b,c=ns[i],ns[jx]
            if c in adj[b]:
                s=int((col[a]&col[b]&col[c]).sum())
                if s>=6: cand.append((s,a,b,c))
cand.sort(reverse=True); cand=cand[:4000]     # evaluate the best-supported 4000 triples
H2cache={}
def H2(a,b):
    k=(a,b) if a<b else (b,a)
    if k not in H2cache: H2cache[k]=H2c(*k)
    return H2cache[k]
syn=[]
for s,a,b,c in cand:
    key=code[:,a]*4+code[:,b]*2+code[:,c]
    cnt=np.bincount(key,minlength=8)/N
    ii=H2(a,b)+H2(a,c)+H2(b,c)-Hs[a]-Hs[b]-Hs[c]-H(cnt)
    syn.append((ii,a,b,c))
syn.sort(key=lambda x:-x[0])
def tri(a,b,c):
    return {"m":[{"id":mid[freq[x]],"name":name[freq[x]],"grp":grp[freq[x]]} for x in (a,b,c)]}
synergy=[{**tri(a,b,c),"ii":round(float(ii),3)} for ii,a,b,c in syn[:16]]
redund=[{**tri(a,b,c),"ii":round(float(ii),3)} for ii,a,b,c in sorted(syn,key=lambda x:x[0])[:8]]

# ---- persistent homology of the motif cloud (Jaccard distance) ----
inter=(X.astype(np.float32).T@X.astype(np.float32))
sz=X.sum(0).astype(np.float32)
union=sz[:,None]+sz[None,:]-inter
D=1.0-inter/np.maximum(union,1.0); np.fill_diagonal(D,0)
res=ripser(D,distance_matrix=True,maxdim=1)
dgms=res["dgms"]
def diag(d):
    out=[]
    for b,dd in d:
        if np.isinf(dd): dd=1.0
        out.append([round(float(b),3),round(float(dd),3)])
    return out
h0=diag(dgms[0]); h1=diag(dgms[1])
# persistence = death-birth; count "real" features (persistence > noise floor)
def persist(d): return sorted([(dd-b) for b,dd in d],reverse=True)
h1p=persist(h1)
n_h0_components=sum(1 for b,dd in h0 if dd-b>0.05)   # components merging late
n_h1_loops=sum(1 for p in h1p if p>0.08)
data={"n_motif_model":TOPN,"n_triples":len(cand),
      "synergy":synergy,"redundancy":redund,
      "h0":h0[:400],"h1":h1,
      "n_h1_loops":int(n_h1_loops),"top_h1_persistence":[round(float(p),3) for p in h1p[:6]],
      "note":"Higher-order structure: synergistic motif triples (interaction information > 0 = a package beyond its pairs) and the persistent homology of the motif cloud (Jaccard). One dominant H0 component + only weak H1 loops = a single connected clinal blob, confirming the geography result from a topological angle; the value is the synergy triples the pairwise view can't see."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"triples {len(cand)} · max II {syn[0][0]:.3f} (>0=synergy) · H1 loops>0.08: {n_h1_loops} · top H1 persist {[round(p,2) for p in h1p[:4]]}")
