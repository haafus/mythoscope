"""Mockup 57 · Contagion — simple vs complex spreading as a generative model (analysis #4, Tier A).

Epidemiology of representations, as a model-comparison. Build a small-world tradition network (k-NN
geography + a few long-range weak ties). Spread a "motif" under two rules and compare the synthetic
footprints to the real ones:

  * SIMPLE contagion (SI): a tradition adopts if ANY neighbour has it (one exposure) — crosses weak
    ties, so it can jump → spatially disjunct footprints are reachable;
  * COMPLEX contagion (threshold θ): adopts only if a FRACTION of neighbours have it (reinforcement) —
    stalls at weak ties, stays in dense cores → compact, contiguous footprints.

Summary statistic = geographic fragmentation (DBSCAN clusters) at a given footprint size. For each real
motif we ask which rule's simulated ensemble reproduces its (size, fragmentation), and cross-check the
assignment against motif complexity (mockup 51) and M17 depth. Honest limit: no time axis → this is
model-comparison on the static snapshot, not a reconstruction. Deterministic; writes data.js.
"""
import json, math, re
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import DBSCAN
import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
import sys; sys.path.insert(0, str(ROOT/"mockups"))
from _geo import berezkin_coords  # noqa
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
rng = np.random.default_rng(0)
def coord(t):
    if t in COORD: return COORD[t]
    p=t.split(".")
    for i in range(len(p)-1,0,-1):
        k=".".join(p[:i])
        if k in COORD: return COORD[k]
    return None
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,[a[0],a[1],b[0],b[1]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371*math.asin(min(1,math.sqrt(h)))
tmot=defaultdict(set)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): tmot[t].add(j)
keep=[t for t in TR if len(tmot[t])>=15 and coord(t)]
N=len(keep); ki={t:i for i,t in enumerate(keep)}
LL=np.array([coord(t) for t in keep]); LLr=np.radians(LL)

# ---- small-world tradition network: k-NN geography + few long-range weak ties ----
K=6
from sklearn.neighbors import BallTree
bt=BallTree(LLr,metric="haversine")
_,nbr=bt.query(LLr,k=K+1)
G=nx.Graph()
G.add_nodes_from(range(N))
for i in range(N):
    for j in nbr[i][1:]: G.add_edge(int(i),int(j))
# add ~2% long-range weak ties
n_long=int(0.02*G.number_of_edges())
for _ in range(n_long):
    a,b=int(rng.integers(N)),int(rng.integers(N))
    if a!=b: G.add_edge(a,b)
adj=[list(G.neighbors(i)) for i in range(N)]

def frag(idx):
    if len(idx)<2: return 1
    return len(set(DBSCAN(eps=0.35,min_samples=1,metric="haversine").fit(LLr[idx]).labels_))

def sim_simple(m):
    seed=int(rng.integers(N)); inf={seed}; front=[seed]
    while len(inf)<m:
        cand=set()
        for u in inf:
            for v in adj[u]:
                if v not in inf: cand.add(v)
        if not cand: break
        # each candidate adopts w.p. 0.6 (one exposure enough)
        newly=[v for v in cand if rng.random()<0.6]
        if not newly: newly=[rng.choice(list(cand))]
        for v in newly:
            inf.add(v)
            if len(inf)>=m: break
    return frag(np.array(sorted(inf)))

def sim_complex(m,theta=0.4):
    # seed a small connected clump (complex contagion needs reinforcement)
    seed=int(rng.integers(N)); inf=set([seed]+adj[seed][:2])
    stall=0
    while len(inf)<m and stall<6:
        newly=[]
        for v in range(N):
            if v in inf: continue
            d=len(adj[v]);
            if d==0: continue
            share=sum(1 for u in adj[v] if u in inf)/d
            if share>=theta: newly.append(v)
        if not newly: stall+=1;
        else:
            stall=0
            for v in newly:
                inf.add(v)
                if len(inf)>=m: break
    return frag(np.array(sorted(inf)))

# ---- simulate fragmentation-vs-size bands for both rules ----
sizes=list(range(8,220,12)); B=40
band={"simple":{}, "complex":{}}
for m in sizes:
    band["simple"][m]=[sim_simple(m) for _ in range(B)]
    band["complex"][m]=[sim_complex(m) for _ in range(B)]
def stat(rule,m):
    ms=min(sizes,key=lambda s:abs(s-m)); a=np.array(band[rule][ms]); return a.mean(),a.std()+0.5

# ---- real motifs: size, fragmentation → assign mode ----
STOP=set("a an the of and or to in on at from by for with as is are was were be that this which who his her its their he she it into out up over under one two some any all more most very can could would usually often etc".split())
def complexity(m):
    d=(m.get("definition") or m.get("name") or "").lower()
    return len({w for w in re.findall(r"[a-z]+",d) if w not in STOP and len(w)>2})
IPset={"OCEANIA","AUSTRALIA"}; NWm={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","MEXICO – CENTRAL ANDES","EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","BERINGIA"}
rows=[]; pts=[]
for j,m in enumerate(MOT):
    idx=[ki[t] for t in m.get("traditions",[]) if t in ki]
    if len(idx)<8: continue
    f=frag(np.array(idx)); sz=len(idx)
    ms,ss=stat("simple",sz); mc,sc=stat("complex",sz)
    z_s=abs(f-ms)/ss; z_c=abs(f-mc)/sc
    # reachable by local contagion at all? (both bands are contiguous-ish; very disjunct → neither)
    unreachable = f > max(ms,mc)+2*max(ss,sc)
    mode = "long-range/descent" if unreachable else ("simple" if z_s<z_c else "complex")
    rows.append({"id":m["id"],"name":m.get("name",""),"grp":m.get("motif_group_num"),
                 "n":sz,"frag":f,"cx":complexity(m),"mode":mode})
    pts.append({"n":sz,"frag":f,"mode":mode})
cnt=Counter(r["mode"] for r in rows)
def spear(a,b):
    a=np.array(a,float); b=np.array(b,float); ra=a.argsort().argsort()-.0; rb=b.argsort().argsort()-.0
    ra-=ra.mean(); rb-=rb.mean(); return float((ra@rb)/(np.sqrt((ra@ra)*(rb@rb))+1e-9))
# validation: complex-contagion motifs should be MORE complex (need reinforcement) than simple ones
cx_complex=np.mean([r["cx"] for r in rows if r["mode"]=="complex"])
cx_simple=np.mean([r["cx"] for r in rows if r["mode"]=="simple"])
cx_long=np.mean([r["cx"] for r in rows if r["mode"]=="long-range/descent"])
def ex(mode,k=8):
    xs=[r for r in rows if r["mode"]==mode]; xs.sort(key=lambda r:-r["n"])
    return [{"id":r["id"],"name":r["name"],"grp":r["grp"],"n":r["n"],"frag":r["frag"],"cx":r["cx"]} for r in xs[:k]]
# simulated bands for the chart
bands=[{"m":m,"s_mean":round(float(np.mean(band["simple"][m])),2),"s_sd":round(float(np.std(band["simple"][m])),2),
        "c_mean":round(float(np.mean(band["complex"][m])),2),"c_sd":round(float(np.std(band["complex"][m])),2)} for m in sizes]
data={"n_trad":N,"edges":G.number_of_edges(),"long_ties":n_long,
      "counts":{k:int(cnt.get(k,0)) for k in ("complex","simple","long-range/descent")},
      "cx_by_mode":{"complex":round(float(cx_complex),1),"simple":round(float(cx_simple),1),"long":round(float(cx_long),1)},
      "bands":bands,"points":pts[:1600],
      "examples":{"complex":ex("complex"),"simple":ex("simple"),"long":ex("long-range/descent")},
      "note":"Simple vs complex contagion on a small-world tradition network, compared to real motif footprints by geographic fragmentation. Complex (needs reinforcement) → compact/contiguous; simple (one exposure) → can cross weak ties; very disjunct footprints are unreachable by local contagion → long-range/descent. Model-comparison on a static snapshot, no time axis; the network is a geographic proxy."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"modes {dict(cnt)} · cx complex {cx_complex:.1f} vs simple {cx_simple:.1f} vs long {cx_long:.1f} · {len(rows)} motifs")
