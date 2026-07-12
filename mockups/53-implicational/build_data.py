"""Mockup 53 · Implicational structure — data-driven motif taxonomy (analysis #6).

Asymmetric co-occurrence: if a tradition has motif X it (almost) always has motif Y, but not
vice versa → "X implies Y" — X is a *specialization* of Y. Aggregated, these implications
recover a subtype→type hierarchy the flat motif_group can't express (Duck-wife ⇒ Magic wife;
Puss-in-Boots ⇒ Trickster-fox). We surface the strongest hubs (types) with their implied
subtypes, and the cross-theme implications (the non-trivial ones). Deterministic; writes data.js.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
def coordless_keep():
    tmot=defaultdict(set)
    for j,m in enumerate(MOT):
        for t in m.get("traditions",[]): tmot[t].add(j)
    return [t for t in TR if len(tmot[t])>=15], tmot
keep,tmot=coordless_keep()
ki={t:i for i,t in enumerate(keep)}
mt=defaultdict(set)
for i,t in enumerate(keep):
    for j in tmot[t]: mt[j].add(i)
name={j:MOT[j].get("name","") for j in range(len(MOT))}
grp={j:MOT[j].get("motif_group_num") for j in range(len(MOT))}
mid={j:MOT[j]["id"] for j in range(len(MOT))}
freq=[j for j in range(len(MOT)) if len(mt[j])>=25]
# implications X ⇒ Y : P(Y|X) high, asymmetric
imp=defaultdict(list)   # Y -> list of X that imply it
edges=[]
for a in freq:
    A=mt[a]
    for b in freq:
        if a==b: continue
        inter=len(A&mt[b])
        if inter<12: continue
        pba=inter/len(A)                 # P(b|a): a implies b
        pab=inter/len(mt[b])
        if pba>=0.80 and pba-pab>=0.40 and len(mt[a])<len(mt[b])*0.7:
            imp[b].append((pba,pab,a,inter))
            edges.append((pba,pab,a,b,inter))
# hubs = types with the most implied subtypes
hubs=sorted(imp.items(),key=lambda kv:-len(kv[1]))
def crosstheme(a,b): return grp[a]!=grp[b]
HUB=[]
for b,xs in hubs[:14]:
    xs.sort(key=lambda x:-(x[0]-x[1]))
    HUB.append({"id":mid[b],"name":name[b],"grp":grp[b],"n":len(mt[b]),"nsub":len(xs),
                "subs":[{"id":mid[a],"name":name[a],"grp":grp[a],"n":len(mt[a]),
                         "pyx":round(p,2),"pxy":round(q,2),"cross":crosstheme(a,b)} for p,q,a,inter in xs[:10]]})
# the strongest CROSS-THEME implications (the surprising ones)
cross=[e for e in edges if crosstheme(e[2],e[3])]
cross.sort(key=lambda e:-(e[0]-e[1]))
CROSS=[{"x":mid[a],"xname":name[a],"xgrp":grp[a],"y":mid[b],"yname":name[b],"ygrp":grp[b],
        "pyx":round(p,2),"pxy":round(q,2)} for p,q,a,b,inter in cross[:20]]
data={"n_motif":len(MOT),"n_freq":len(freq),"n_edges":len(edges),
      "hubs":HUB,"cross":CROSS,
      "note":"Implicational structure: X⇒Y when P(Y|X)≥0.80 and much > P(X|Y) and X is rarer — X is a specialization of Y. Hubs = motif 'types' with their implied subtypes; cross-theme implications are the non-obvious ones. Recovers a data-driven subtype→type hierarchy over the flat motif groups."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"freq motifs {len(freq)} · implications {len(edges)} · hubs {len(HUB)} · cross-theme {len(cross)}")
