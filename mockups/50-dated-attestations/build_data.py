"""Mockup 50 · Dated attestations — textual terminus ante quem + religion/corpus calendar.

The one route to *real calendar years* that needs no external file: several of Berezkin's own
traditions ARE dated literate corpora (Sumer, Ancient Egypt, Hittite, Ugarit, Vedic, Early Chinese,
…). A motif attested in such a corpus is **documented by** that corpus's date → an absolute
terminus-ante-quem floor. Combined with the biogeographic barrier floors (mockup 49) this gives a
unified "earliest documented / bounded" age per motif, and a timeline of when motif-complexes first
enter the written record.

Honest limits: (a) a lumped corpus (e.g. "Vedic … Purana") spans centuries — the old bound is
optimistic, flagged per corpus; (b) a documented floor is a lower bound on age, not the age; (c) only
the literate Old World + Mesoamerica is covered. Deterministic; writes data.js.
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

bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
M=len(MOT)

# ---- curated dated corpora (tradition id → date & provenance) ----
# yr = years-ago floor (terminus ante quem, present≈2000 CE); conf; span note
CORPORA={
 "3.1.1.1": ("Ancient Egypt",       4350,"high",  "Pyramid Texts ~2350 BCE"),
 "5.3.1.3": ("Sumer",               4100,"high",  "Sumerian literary texts ~2100 BCE"),
 "5.3.1.4": ("Akkad / Babylon",     3700,"high",  "Old Babylonian ~1700 BCE (Atrahasis)"),
 "5.2.3.1": ("Hittite",             3400,"high",  "Hittite/Hurrian myths ~1400 BCE"),
 "5.3.1.2": ("Ugarit",              3300,"high",  "Baal cycle ~1300 BCE"),
 "5.6.1.1": ("Vedic / Indian",      3200,"medium","Rigveda ~1500 BCE; corpus spans to Puranas ~1000 CE"),
 "10.2.1.1":("Early Chinese",       2950,"high",  "oracle bones / Shijing ~1000 BCE"),
 "5.4.1.1": ("Iranian / Avesta",    2950,"medium","Gathas ~1000 BCE; Younger Avesta later"),
 "5.3.1.6": ("Phoenicia",           2900,"medium","Phoenician sources ~900 BCE"),
 "3.4.1.2": ("Ancient Italy",       2600,"medium","Etruscan/Latin/Magna Graecia ~600 BCE"),
 "6.2.2.5": ("Greek on India",      2250,"low",   "Megasthenes ~300 BCE (small sample)"),
 "14.1.6.1":("Maya",                1750,"medium","Classic Maya inscriptions ~250 CE"),
 "10.3.2.4":("Japan (Kojiki)",      1290,"high",  "Kojiki 712 CE"),
 "5.3.2.5": ("Arab (1001 Nights)",  1050,"medium","Arabic literary tradition ~900–1400 CE"),
 "14.1.2.2":("Aztec",                600,"medium","Aztec codices ~1400 CE; Teotihuacan iconography older"),
}
def yr_to_label(y):
    ce=2000-y
    return f"{-ce+1} BCE" if ce<0 else f"{ce} CE"

def macro(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1] if ap and ap[0] else "?"
def cont(t):
    a=macro(t).lower()
    if "africa" in a and "north" not in a: return "Africa"
    if "australia" in a: return "Australia"
    if any(w in a for w in ["america","andes","mexico","amazon","brazil","patagon","beringia"]): return "Americas"
    if any(w in a for w in ["oceania","polynesia","micronesia","indonesia","nusantara","melanesia"]): return "Oceania"
    return "Eurasia"

# ---- per-motif textual floor (oldest dated corpus attesting it) ----
tex_floor=np.zeros(M); tex_corpus=[None]*M; tex_all=[[] for _ in range(M)]
for j,m in enumerate(MOT):
    for tid in m.get("traditions",[]):
        if tid in CORPORA:
            nm,y,conf,note=CORPORA[tid]; tex_all[j].append(nm)
            if y>tex_floor[j]: tex_floor[j]=y; tex_corpus[j]=nm

# ---- biogeographic barrier floor (mockup 49 logic) ----
def coord(tid):
    if tid in COORD: return COORD[tid]
    p=tid.split(".")
    for i in range(len(p)-1,0,-1):
        k=".".join(p[:i])
        if k in COORD: return COORD[k]
    return None
NAM={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","BERINGIA"}
SAM={"EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","MEXICO – CENTRAL ANDES"}
def barrier_floor(j):
    tids=MOT[j].get("traditions",[]); c=Counter(cont(t) for t in tids)
    amE=c.get("Americas",0); ow=c.get("Eurasia",0)+c.get("Africa",0)+c.get("Oceania",0); aus=c.get("Australia",0)
    if aus>=2 and (ow+amE)>=2: return 50000,"Sahul"
    if amE>=2 and ow>=2: return 15000,"trans-Beringian"
    macs=[macro(t) for t in tids]
    if sum(x in NAM for x in macs)>=2 and sum(x in SAM for x in macs)>=2: return 13000,"pan-American"
    return 0,None
bfloor=np.zeros(M); btier=[None]*M
for j in range(M):
    bfloor[j],btier[j]=barrier_floor(j)
unified=np.maximum(tex_floor,bfloor)

# ---- M17 depth (validation proxy) ----
IPset={"OCEANIA","AUSTRALIA"}
NWm={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","MEXICO – CENTRAL ANDES","EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","BERINGIA"}
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
    seg={"NW" if x in NWm else ("IP" if x in IPset else "CONT") for x in mus}
    feat.append([len(tids),len(set(mus)),len(langs),spread,frags,len(seg),1+(1 if m.get("atu_refs") else 0)]); fidx.append(j)
disj=StandardScaler().fit_transform(np.array(feat,float))@DISJ_W
rank=(disj.argsort().argsort()/(len(disj)-1))*100
depth=np.full(M,np.nan)
for k,j in enumerate(fidx): depth[j]=rank[k]

# ---- metrics ----
has_tex=tex_floor>0; has_bar=bfloor>0; has_any=unified>0
tex_only=has_tex&~has_bar
def spear(a,b):
    ra=a.argsort().argsort().astype(float); rb=b.argsort().argsort().astype(float)
    ra-=ra.mean(); rb-=rb.mean(); return float((ra@rb)/(np.sqrt((ra@ra)*(rb@rb))+1e-12))
vm=has_tex&~np.isnan(depth)
r_tex_depth=round(spear(tex_floor[vm],depth[vm]),2)     # older documented → deeper M17?
# cleaner validation: mean M17 depth by documented-age bucket (early vs late documented)
def mean_depth(mask):
    dd=depth[mask&~np.isnan(depth)]; return round(float(dd.mean()),0) if len(dd) else None
depth_by_age=[{"lab":"≥3000 ya","d":mean_depth(tex_floor>=3000)},
              {"lab":"1500–3000","d":mean_depth((tex_floor>=1500)&(tex_floor<3000))},
              {"lab":"<1500 ya","d":mean_depth((tex_floor>0)&(tex_floor<1500))}]

def gname(j): return MOT[j].get("motif_group_num")
# corpus table + counts
corpus_rows=[]
for tid,(nm,y,conf,note) in sorted(CORPORA.items(),key=lambda kv:-kv[1][1]):
    js=[j for j in range(M) if tid in MOT[j].get("traditions",[])]
    firsts=[j for j in js if tex_corpus[j]==nm]        # motifs whose OLDEST corpus is this one
    corpus_rows.append({"name":nm,"yr":y,"label":yr_to_label(y),"conf":conf,"note":note,
                        "n":len(js),"n_first":len(firsts)})
# oldest documented motifs
old_order=sorted([j for j in range(M) if has_tex[j]],key=lambda j:(-tex_floor[j],-len(tex_all[j])))
oldest=[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":gname(j),"yr":int(tex_floor[j]),
         "label":yr_to_label(int(tex_floor[j])),"corpus":tex_corpus[j],
         "ncorp":len(set(tex_all[j])),"corps":sorted(set(tex_all[j])),
         "depth":(None if np.isnan(depth[j]) else round(float(depth[j])))} for j in old_order[:20]]
# histogram of earliest documented attestation (only motifs WITH a textual floor)
buckets=[(4000,9999,"≥4000"),(3000,4000,"3–4k"),(2500,3000,"2.5–3k"),(2000,2500,"2–2.5k"),
         (1500,2000,"1.5–2k"),(1000,1500,"1–1.5k"),(1,1000,"<1k")]
hist=[{"lab":lab,"n":int(((tex_floor>=lo)&(tex_floor<hi)).sum())} for lo,hi,lab in buckets]
# multi-corpus motifs (attested in >=3 dated corpora — robustly ancient & widespread in the literate world)
multi=[{"id":MOT[j]["id"],"name":MOT[j]["name"],"grp":gname(j),"ncorp":len(set(tex_all[j])),
        "corps":sorted(set(tex_all[j])),"yr":int(tex_floor[j]),"label":yr_to_label(int(tex_floor[j]))}
       for j in sorted(range(M),key=lambda j:-len(set(tex_all[j]))) if len(set(tex_all[j]))>=4][:14]

data={"n_motif":M,"corpora":corpus_rows,
      "coverage":{"textual":int(has_tex.sum()),"barrier":int(has_bar.sum()),"any":int(has_any.sum()),
                  "tex_only":int(tex_only.sum()),"n_corpora":len(CORPORA)},
      "oldest":oldest,"hist":hist,"multi":multi,
      "validation":{"r_tex_depth":r_tex_depth,"n":int(vm.sum()),"depth_by_age":depth_by_age},
      "note":"Dated attestations: motifs documented in Berezkin's own dated literate corpora (Sumer 2350 BCE → Aztec 1400 CE) get an absolute terminus-ante-quem floor, merged with the biogeographic barrier floors. Lower bounds, not ages; lumped corpora over-state the old end (flagged)."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"{len(CORPORA)} corpora | textual-floor {int(has_tex.sum())} motifs ({int(tex_only.sum())} not barrier-covered) | "
      f"any-floor {int(has_any.sum())} | r(tex-floor,M17)={r_tex_depth} | ~{out.stat().st_size//1024}KB")
