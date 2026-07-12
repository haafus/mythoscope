"""Mockup 54 · Dated catalogue — one per-motif age table combining every signal (analysis #8).

Synthesis deliverable, not a new method: gather the project's per-motif age signals —
M17 disjunction depth (percentile), phylo-signal (M18/M30), biogeographic barrier floor
(mockup 49), textual terminus floor (mockup 50), language-family expansion age (M30) — into
one row per motif, a consensus best year-floor, and how many INDEPENDENT absolute signals
corroborate it. A searchable dated motif catalogue with honest per-motif provenance.
Deterministic; writes data.js.
"""
import json, sys, math, random
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]; COORD=berezkin_coords(); M=len(MOT)
def coord(t):
    if t in COORD: return COORD[t]
    p=t.split(".")
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
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,[a[0],a[1],b[0],b[1]])
    h=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*6371*math.asin(min(1,math.sqrt(h)))
join=json.loads((ROOT/"mockups"/"30-dated-phylogeny"/"glottolog_join.json").read_text())
gfam={t:j["gfam"] for t,j in join.items()}

# M17 depth
IPset={"OCEANIA","AUSTRALIA"}; NWm={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","MEXICO – CENTRAL ANDES","EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","BERINGIA"}
DISJ=np.array([-1,-.5,1,.5,.8,1,0.])
def muf(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1].upper() if ap else None
feat=[];fid=[]
for r in MOT:
    ts=r.get("traditions") or []
    if len(ts)<3: continue
    mus=[muf(t) for t in ts if muf(t)]; pts=[COORD[t] for t in ts if t in COORD]
    if len(pts)>=2:
        cen=(np.mean([p[0] for p in pts]),np.mean([p[1] for p in pts])); sp=np.mean([hav(p,cen) for p in pts])
        fr=len(set(DBSCAN(eps=.35,min_samples=1,metric="haversine").fit(np.radians([[p[0],p[1]] for p in pts])).labels_))
    else: sp,fr=0,1
    seg={"NW" if x in NWm else ("IP" if x in IPset else "C") for x in mus}
    feat.append([len(ts),len(set(mus)),len({(TR[t].get("language") or [None])[0] for t in ts}),sp,fr,len(seg),1+(1 if r.get("atu_refs") else 0)]);fid.append(r["id"])
dz=StandardScaler().fit_transform(np.array(feat,float))@DISJ
depth={fid[k]:int(round((dz.argsort().argsort()[k]/(len(dz)-1))*100)) for k in range(len(dz))}
# barrier + textual floors
NAM={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","BERINGIA"}; SAM={"EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","MEXICO – CENTRAL ANDES"}
CORP={"3.1.1.1":4350,"5.3.1.3":4100,"5.3.1.4":3700,"5.2.3.1":3400,"5.3.1.2":3300,"5.6.1.1":3200,"10.2.1.1":2950,"5.4.1.1":2950,"5.3.1.6":2900,"3.4.1.2":2600,"6.2.2.5":2250,"14.1.6.1":1750,"10.3.2.4":1290,"5.3.2.5":1050,"14.1.2.2":600}
CORPNAME={"3.1.1.1":"Egypt","5.3.1.3":"Sumer","5.3.1.4":"Akkad","5.2.3.1":"Hittite","5.3.1.2":"Ugarit","5.6.1.1":"Vedic","10.2.1.1":"Early Chinese","5.4.1.1":"Iranian","5.3.1.6":"Phoenicia","3.4.1.2":"Ancient Italy","6.2.2.5":"Greek","14.1.6.1":"Maya","10.3.2.4":"Japan","5.3.2.5":"Arab","14.1.2.2":"Aztec"}
bfloor={};btier={};tfloor={};tcorp={}
for r in MOT:
    ts=r.get("traditions") or []; c=Counter(cont(t) for t in ts); macs=[macro(t) for t in ts]
    amE=c.get("Americas",0); ow=c.get("Eurasia",0)+c.get("Africa",0)+c.get("Oceania",0); aus=c.get("Australia",0)
    if aus>=2 and (ow+amE)>=2: bfloor[r["id"]]=50000; btier[r["id"]]="Sahul"
    elif amE>=2 and ow>=2: bfloor[r["id"]]=15000; btier[r["id"]]="trans-Beringian"
    elif sum(x in NAM for x in macs)>=2 and sum(x in SAM for x in macs)>=2: bfloor[r["id"]]=13000; btier[r["id"]]="pan-American"
    best=0;bc=None
    for t in ts:
        if t in CORP and CORP[t]>best: best=CORP[t]; bc=CORPNAME[t]
    if best: tfloor[r["id"]]=best; tcorp[r["id"]]=bc
# M30 family age + phylo-signal
children,node_of,depth_l,leaf_of=[[]],{():0},[0],{}
for tid,v in TR.items():
    path,parent=(),0
    for lvl in (v.get("language") or ["(unknown)"]):
        path=path+(lvl,); nid=node_of.get(path)
        if nid is None:
            nid=len(children);children.append([]);depth_l.append(depth_l[parent]+1);node_of[path]=nid;children[parent].append(nid)
        parent=nid
    leaf=len(children);children.append([]);depth_l.append(depth_l[parent]+1);children[parent].append(leaf);leaf_of[tid]=leaf
nN=len(children); is_leaf=[len(c)==0 for c in children]
order,stack,seen=[],[0],[False]*nN
while stack:
    x=stack[-1]
    if not seen[x]: seen[x]=True; stack.extend(children[x])
    else: order.append(stack.pop())
leaves=[i for i in range(nN) if is_leaf[i]]; st=[0]*nN
def fitch(pres):
    ch=0
    for n in order:
        if is_leaf[n]: st[n]=2 if n in pres else 1
        else:
            inter,uni=3,0
            for c in children[n]: inter&=st[c]; uni|=st[c]
            st[n]=inter if inter else uni; ch+=0 if inter else 1
    return ch
import importlib.util
spec=importlib.util.spec_from_file_location("m30",ROOT/"mockups"/"30-dated-phylogeny"/"build_data.py"); m30=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(m30)
except SystemExit: pass
FAM=m30.FAMILY_DATES
rng=random.Random(0); famage={};famname={};psig={}
for r in MOT:
    P=[t for t in (r.get("traditions") or []) if t in leaf_of]
    if len(P)<6: continue
    pres={leaf_of[t] for t in P}; obs=fitch(pres); rnd=np.mean([fitch(set(rng.sample(leaves,len(pres)))) for _ in range(8)])
    s=0.0 if rnd<=1 else max(0.,min(1.,(rnd-obs)/(rnd-1))); psig[r["id"]]=round(s,2)
    fams=Counter(gfam.get(t) for t in P if gfam.get(t))
    if fams:
        dom,dn=fams.most_common(1)[0]
        if s>=0.4 and dn/len(P)>=0.55 and dom in FAM: famage[r["id"]]=FAM[dom][0]; famname[r["id"]]=dom

# ---- assemble catalogue ----
def yl(y):
    ce=2000-y; return f"{-ce} BCE" if ce<0 else f"{ce} CE"
cat=[]
for r in MOT:
    mid=r["id"]
    abs_sigs=[]
    if mid in bfloor: abs_sigs.append(("barrier",bfloor[mid],btier[mid]))
    if mid in tfloor: abs_sigs.append(("textual",tfloor[mid],tcorp[mid]))
    if mid in famage: abs_sigs.append(("family",famage[mid],famname[mid]))
    best=max((y for _,y,_ in abs_sigs),default=0)
    cat.append({"id":mid,"name":r.get("name",""),"grp":r.get("motif_group_num"),
                "depth":depth.get(mid),"psig":psig.get(mid),
                "barrier":bfloor.get(mid),"btier":btier.get(mid),
                "textual":tfloor.get(mid),"tcorp":tcorp.get(mid),
                "family":famage.get(mid),"fname":famname.get(mid),
                "best":int(best) if best else None,"nabs":len(abs_sigs)})
absset=[c for c in cat if c["best"]]
cov={"depth":sum(1 for c in cat if c["depth"] is not None),"psig":len(psig),
     "barrier":len(bfloor),"textual":len(tfloor),"family":len(famage),
     "any_abs":len(absset),"corrob2":sum(1 for c in absset if c["nabs"]>=2),
     "any":sum(1 for c in cat if c["depth"] is not None or c["best"] or c["psig"] is not None),"total":M}
ba=np.array([c["best"] for c in absset])
hist=[{"lab":lab,"n":int(((ba>=lo)&(ba<hi)).sum())} for lo,hi,lab in
      [(20000,99999,"≥20ka"),(10000,20000,"10–20ka"),(4000,10000,"4–10ka"),(2500,4000,"2.5–4ka"),(1,2500,"<2.5ka")]]
# table: the corroborated + oldest, sorted; cap for payload
tbl=sorted(absset,key=lambda c:(-c["nabs"],-(c["best"] or 0)))
tbl=[{**c,"blabel":yl(c["best"])} for c in tbl[:400]]
data={"n_motif":M,"coverage":cov,"hist":hist,"table":tbl,
      "note":"Unified dated catalogue: per-motif age signals (M17 depth · phylo-signal · barrier floor · textual floor · family age) with a consensus best year-floor and independent-corroboration count. Synthesis of mockups 17/18/30/49/50 — floors are lower bounds, not ages."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"any-absolute {cov['any_abs']} · corroborated≥2 {cov['corrob2']} · any-signal {cov['any']}/{M} · table {len(tbl)}")
