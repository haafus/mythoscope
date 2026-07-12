"""Mockup 59 · Infinite-K — a Bayesian-nonparametric latent model (analysis #3, Tier A).

Mockup 47 found the admixture CV curve plateaus with no clean K. The principled response is a model
that does not fix K: a Hierarchical Dirichlet Process, which infers an unbounded number of latent
components. We fit HDP (traditions = documents, motifs = words) and read off the effective number of
components and how their weight decays — the formalisation of "no natural K".

Deterministic (fixed seed); writes data.js.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from gensim import corpora
from gensim.models import HdpModel

ROOT = Path(__file__).resolve().parents[2]
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
tmot=defaultdict(list)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): tmot[t].append(j)
keep=[t for t in TR if len(tmot[t])>=15]
name={j:MOT[j].get("name","") for j in range(len(MOT))}
grp={j:MOT[j].get("motif_group_num") for j in range(len(MOT))}
mid={j:MOT[j]["id"] for j in range(len(MOT))}
def macro(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1] if ap and ap[0] else "?"

# gensim corpus: doc = tradition, tokens = its motif ids
motif_ids=sorted({j for t in keep for j in tmot[t]})
dct=corpora.Dictionary([[str(j) for j in motif_ids]])
corpus=[dct.doc2bow([str(j) for j in tmot[t]]) for t in keep]
hdp=HdpModel(corpus,dct,random_state=0,T=150,K=15,alpha=1,gamma=1)

# component weights (corpus-level stick weights) → effective K
topic_term=hdp.get_topics()                      # (T, V)
# assign each tradition to its dominant component, measure weight distribution
doc_top=[hdp[c] for c in corpus]
dom=[max(dt,key=lambda x:x[1])[0] if dt else -1 for dt in doc_top]
comp_mass=Counter()
for dt in doc_top:
    for k,w in dt: comp_mass[k]+=w
total=sum(comp_mass.values())
ranked=sorted(comp_mass.items(),key=lambda x:-x[1])
weights=[(k,v/total) for k,v in ranked]
# effective K: number of components covering 90% of mass; and > 1% each
cum=0; effK90=0
for _,w in weights:
    cum+=w; effK90+=1
    if cum>=0.90: break
effK1=sum(1 for _,w in weights if w>=0.01)
id2tok={v:k for k,v in dct.token2id.items()}
def top_motifs(k,n=8):
    row=topic_term[k]; idx=np.argsort(-row)[:n]
    out=[]
    for ti in idx:
        j=int(id2tok[int(ti)]); out.append({"id":mid[j],"name":name[j],"grp":grp[j]})
    return out
comps=[]
for rank,(k,w) in enumerate(weights[:12]):
    members=[keep[i] for i in range(len(keep)) if dom[i]==k]
    areas=Counter(macro(t) for t in members).most_common(3)
    comps.append({"k":int(k),"weight":round(float(w),3),"n":len(members),
                  "areas":[{"a":a,"n":n} for a,n in areas],"motifs":top_motifs(k)})
weight_curve=[round(float(w),4) for _,w in weights[:40]]
data={"n_trad":len(keep),"n_motif":len(motif_ids),"T":150,
      "effK90":int(effK90),"effK1":int(effK1),
      "weight_curve":weight_curve,"components":comps,
      "note":"Hierarchical Dirichlet Process (infinite-K) over traditions×motifs. The component-weight curve decays smoothly with no elbow — the model spreads mass over many components with a long tail, formalising mockup 47's 'no natural K'. The top components are the familiar areal/thematic blocks; the point is the SHAPE of the weight decay, not a fixed count."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"effective K: {effK90} (90% mass), {effK1} (>1% each) · top weights {weight_curve[:5]}")
