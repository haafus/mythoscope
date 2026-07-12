"""Mockup 51 · Descent / Diffusion / Invention — a per-motif mode scorecard.

Low NRI (a widely-dispersed motif) does NOT by itself say old-inheritance: a dispersed motif can be
(a) deep DESCENT (inherited from a common ancestor, differentially lost → relict/disjunct),
(b) late DIFFUSION (recently borrowed along a contact corridor → contiguous, corridor-confined), or
(c) independent INVENTION (a cognitively obvious motif reinvented → simple, observational).

We can't read the mode off dispersal, but we can STACK the discriminators the project already has,
plus one new one — motif COMPLEXITY / arbitrariness from the definition text (the classic
transmission-vs-invention test: a complex, arbitrary motif is not reinvented twice).

Two axes:
  x = complexity (content-words in the definition) — invention (low) ↔ transmission (high)
  y = descent evidence — barrier-crossing (diffusion can't cross a closed barrier) + geographic
      disjunction (relict, not a wave) + independent early attestation in disconnected dated corpora
      — diffusion (low) ↔ descent (high)
Plus an invention flag: low complexity AND etiological/observational domain.

Heuristic, not ground truth — a transparent stack of signals, each defensible, none decisive alone.
Deterministic; writes data.js.
"""
import json, sys, math, re
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import DBSCAN

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402

bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
M=len(MOT)
def macro(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1] if ap and ap[0] else "?"
def cont(t):
    a=macro(t).lower()
    if "africa" in a and "north" not in a: return "Africa"
    if "australia" in a: return "Australia"
    if any(w in a for w in ["america","andes","mexico","amazon","brazil","patagon","beringia"]): return "Americas"
    if any(w in a for w in ["oceania","polynesia","micronesia","indonesia","nusantara","melanesia"]): return "Oceania"
    return "Eurasia"
NAM={"NORTH AMERICA: NORTH AND WEST","PLAINS AND SOUTHEAST","BERINGIA"}
SAM={"EASTERN SOUTH AMERICA","SOUTHERN SOUTH AMERICA","MEXICO – CENTRAL ANDES"}
CORP={"3.1.1.1","5.3.1.3","5.3.1.4","5.2.3.1","5.3.1.2","5.6.1.1","10.2.1.1","5.4.1.1","5.3.1.6",
      "3.4.1.2","6.2.2.5","14.1.6.1","10.3.2.4","5.3.2.5","14.1.2.2"}

STOP=set("a an the of and or to in on at from by for with as is are was were be been being that this "
 "which who whom his her its their he she it they them who into out up down over under after before "
 "than then so but not no also one two some any all each other another more most very can could would "
 "usually often sometimes etc eg ie him hers our your my per".split())
def complexity(m):
    d=(m.get("definition") or m.get("name") or "").lower()
    toks=[w for w in re.findall(r"[a-z]+",d) if w not in STOP and len(w)>2]
    return len(set(toks))                          # distinct content words = narrative elements

def frags(tids):
    pts=[COORD[t] for t in tids if t in COORD]
    if len(pts)<2: return 1
    return len(set(DBSCAN(eps=0.35,min_samples=1,metric="haversine").fit(
        np.radians([[p[0],p[1]] for p in pts])).labels_))

# ---- per-motif features ----
rows=[]
for j,m in enumerate(MOT):
    tids=[t for t in (m.get("traditions") or []) if COORD.get(t) is not None]
    if len(tids)<5: continue
    c=Counter(cont(t) for t in tids); nmac=len({macro(t) for t in tids})
    amE=c.get("Americas",0); ow=c.get("Eurasia",0)+c.get("Africa",0)+c.get("Oceania",0); aus=c.get("Australia",0)
    macs=[macro(t) for t in tids]
    if aus>=2 and (ow+amE)>=2: barrier="Sahul"
    elif amE>=2 and ow>=2: barrier="trans-Beringian"
    elif sum(x in NAM for x in macs)>=2 and sum(x in SAM for x in macs)>=2: barrier="pan-American"
    else: barrier=None
    fr=frags(tids)
    ncorp=len({t for t in (m.get("traditions") or []) if t in CORP})
    corridor = (amE==0 and aus==0 and c.get("Oceania",0)==0)     # Eurasia+Africa only
    rows.append({"j":j,"id":m["id"],"name":m.get("name",""),"grp":m.get("motif_group_num"),
                 "nmac":nmac,"barrier":barrier,"frag":fr,"ncorp":ncorp,"corridor":corridor,
                 "cx":complexity(m),"etio":(m.get("motif_type")=="Cosmology and etiology"),
                 "atu":bool(m.get("atu_refs")),"n":len(tids)})

cxs=np.array([r["cx"] for r in rows],float)
frs=np.array([r["frag"] for r in rows],float)
def pct(v,arr): return float((arr<v).mean())
# axes
for r in rows:
    r["x"]=round(pct(r["cx"],cxs),3)                                   # complexity percentile
    disj=min(1.0,(r["frag"]-1)/6.0)                                    # geographic disjunction (relict)
    corp=min(1.0,r["ncorp"]/3.0)
    bar=1.0 if r["barrier"] else 0.0
    r["y"]=round(min(1.0,0.55*bar+0.30*disj+0.30*corp),3)             # descent evidence
# ---- classify mode ----
# invention-prone = simple + observational + NOT a recognised complex tale-type (ATU).
# An ATU tale-type or a low-complexity-but-arbitrary narrative is transmitted by construction.
def classify(r):
    if r["x"]<0.35 and r["etio"] and not r["atu"]: return "invention"
    if r["barrier"] or r["y"]>=0.45: return "descent"
    if r["corridor"] and r["y"]<0.30: return "diffusion"
    return "ambiguous"
for r in rows: r["mode"]=classify(r)

# focus on the dispersed motifs (where the question bites): span >=5 macro-areas
disp=[r for r in rows if r["nmac"]>=5]
counts=Counter(r["mode"] for r in disp)
# nuance: invention-prone motifs that ALSO cross a barrier / are multiply attested are OLD but
# mode-undecidable (independent invention vs deep descent both fit)
inv=[r for r in disp if r["mode"]=="invention"]
inv_old=sum(1 for r in inv if r["barrier"] or r["ncorp"]>=2)
COL={"descent":"#4f7096","diffusion":"#c0873f","invention":"#9c6a94","ambiguous":"#9aa0a6"}

def ex(mode,key,rev=True,k=9):
    xs=[r for r in disp if r["mode"]==mode]
    xs.sort(key=lambda r:(-r[key] if rev else r[key]))
    return [{"id":r["id"],"name":r["name"],"grp":r["grp"],"nmac":r["nmac"],"cx":r["cx"],
             "barrier":r["barrier"],"ncorp":r["ncorp"],"frag":r["frag"]} for r in xs[:k]]

points=[{"x":r["x"],"y":r["y"],"mode":r["mode"],"nmac":r["nmac"],"id":r["id"],
         "name":r["name"],"grp":r["grp"]} for r in disp]
data={"n_motif":M,"n_scored":len(rows),"n_dispersed":len(disp),
      "counts":{k:int(counts.get(k,0)) for k in ("descent","diffusion","invention","ambiguous")},
      "colors":COL,"points":points,
      "examples":{"descent":ex("descent","y"),"diffusion":ex("diffusion","nmac"),
                  "invention":ex("invention","nmac"),"ambiguous":ex("ambiguous","nmac")},
      "median_cx":int(np.median(cxs)),"inv_old":int(inv_old),"n_inv":int(len(inv)),
      "note":"Descent/Diffusion/Invention scorecard for dispersed motifs. x=complexity (definition content-words → invention vs transmission); y=descent evidence (barrier-crossing + geographic disjunction + independent dated-corpus attestation → diffusion vs descent); invention = simple + etiological. Heuristic stack of the project's discriminators, not ground truth."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"scored {len(rows)} · dispersed {len(disp)} · modes {dict(counts)} · median complexity {int(np.median(cxs))} words · ~{out.stat().st_size//1024}KB")
