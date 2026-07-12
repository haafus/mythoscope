"""Mockup 56 · Motif coupling — a pairwise maximum-entropy (inverse-Ising) model.

The minimal model reproducing the observed pairwise motif co-occurrences is the Ising / Boltzmann
model  P(s) ∝ exp( Σ h_i s_i + Σ J_ij s_i s_j ).  Its couplings J_ij are the **direct** links — what
remains after every transitive path through other motifs is removed. We fit it by pseudo-likelihood:
an L1-logistic regression of each motif on all the others, **with the tradition's log-richness as a
covariate** so the cataloguing-effort confound (a densely-recorded tradition has more of everything)
does not masquerade as coupling. Then:

  * positive J  = direct attraction (co-occur beyond what their other correlations explain);
  * negative J  = direct repulsion — mutually-exclusive motifs (genuinely new; the matrix's marginals
    can't show this);
  * high raw correlation but J≈0 = an INDIRECT pair (correlated only through a hub) — the "debunked"
    associations that mockup 53's implication list would have shown as real.

Deterministic; writes data.js.
"""
import json, math, warnings
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
import networkx as nx
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
TOPN = 500          # motifs modelled (by frequency) — keeps the pseudo-likelihood tractable
C = 0.15            # L1 strength (smaller = sparser)

tmot=defaultdict(set)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): tmot[t].add(j)
keep=[t for t in TR if len(tmot[t])>=15]
N=len(keep)
full_rich=np.array([len(tmot[t]) for t in keep],float)     # richness over ALL motifs (effort proxy)
rich_z=(np.log(full_rich)-np.log(full_rich).mean())/np.log(full_rich).std()

freq=sorted(range(len(MOT)),key=lambda j:-sum(1 for t in keep if j in tmot[t]))
sel=freq[:TOPN]
name={j:MOT[j].get("name","") for j in range(len(MOT))}
grp={j:MOT[j].get("motif_group_num") for j in range(len(MOT))}
mid={j:MOT[j]["id"] for j in range(len(MOT))}
X=np.zeros((N,TOPN),np.float32)
for c,j in enumerate(sel):
    for i,t in enumerate(keep):
        if j in tmot[t]: X[i,c]=1.0

# ---- pseudo-likelihood: L1-logistic of each motif on the others + effort covariate ----
Jrow=np.zeros((TOPN,TOPN))
Feat=np.hstack([X, rich_z[:,None]])
for c in range(TOPN):
    y=X[:,c]
    if y.sum()<3 or y.sum()>N-3: continue
    cols=[k for k in range(TOPN) if k!=c]
    Xin=np.hstack([X[:,cols], rich_z[:,None]])
    lr=LogisticRegression(penalty="l1",solver="liblinear",C=C,max_iter=200)
    lr.fit(Xin,y)
    coef=lr.coef_[0]
    for idx,k in enumerate(cols):
        Jrow[c,k]=coef[idx]
    if c%100==0: print(f"  fit {c}/{TOPN}")
J=(Jrow+Jrow.T)/2.0     # symmetrise

# raw association (phi = Pearson on binary columns)
Xc=X-X.mean(0); sd=X.std(0)+1e-9
Phi=(Xc.T@Xc)/N/np.outer(sd,sd)

iu=np.triu_indices(TOPN,1)
Jv=J[iu]; Pv=Phi[iu]
def pair(a,b):
    return {"a":mid[sel[a]],"an":name[sel[a]],"ag":grp[sel[a]],
            "b":mid[sel[b]],"bn":name[sel[b]],"bg":grp[sel[b]],
            "J":round(float(J[a,b]),2),"phi":round(float(Phi[a,b]),2)}
order=np.argsort(-Jv)
attract=[pair(*[iu[0][k],iu[1][k]]) for k in order[:18]]
order_neg=np.argsort(Jv)   # most negative first
repel=[pair(iu[0][k],iu[1][k]) for k in order_neg if Jv[k]<-0.05][:16]
# indirect: high |phi| but J~0
mask_ind=(np.abs(Pv)>=0.30)&(np.abs(Jv)<0.05)
ind_idx=iu[0][mask_ind],iu[1][mask_ind]
ind_order=np.argsort(-np.abs(Pv[mask_ind]))
indirect=[pair(ind_idx[0][k],ind_idx[1][k]) for k in ind_order[:16]]

# how many strong raw correlations survive as direct couplings?
strong=np.abs(Pv)>=0.30
surv=(np.abs(Jv[strong])>=0.05).mean() if strong.sum() else 0.0
n_pos=int((Jv>0.05).sum()); n_neg=int((Jv<-0.05).sum())

# ---- network layout (spring) on the strongest |J| edges ----
thr=np.percentile(np.abs(Jv),99.2)
G=nx.Graph()
for k in range(len(Jv)):
    if abs(Jv[k])>=thr:
        G.add_edge(int(iu[0][k]),int(iu[1][k]),w=float(Jv[k]))
if G.number_of_nodes()==0: thr=np.percentile(np.abs(Jv),98.5)
pos=nx.spring_layout(G,seed=0,k=0.6,iterations=120) if G.number_of_nodes() else {}
nodes=[{"i":int(n),"id":mid[sel[n]],"name":name[sel[n]],"grp":grp[sel[n]],
        "deg":int(G.degree(n)),"x":round(float(pos[n][0]),3),"y":round(float(pos[n][1]),3)} for n in G.nodes()]
edges=[{"s":int(u),"t":int(v),"J":round(float(d["w"]),2)} for u,v,d in G.edges(data=True)]

data={"n_trad":N,"n_motif_model":TOPN,"C":C,
      "n_pos":n_pos,"n_neg":n_neg,"survive":round(float(surv),2),
      "attract":attract,"repel":repel,"indirect":indirect,
      "nodes":nodes,"edges":edges,
      "note":"Pairwise maximum-entropy (inverse-Ising) model of the top-500 motifs, effort-corrected (log-richness covariate). J_ij = DIRECT coupling: positive=attraction, negative=mutual exclusion; high correlation with J≈0 = indirect (via a hub). Couplings still share the residual effort/areal confound — read as structure, not causation."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"pos {n_pos} · neg {n_neg} · strong-corr surviving as direct {surv:.0%} · network {len(nodes)} nodes {len(edges)} edges")
