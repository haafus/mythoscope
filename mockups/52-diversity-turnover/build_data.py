"""Mockup 52 · Diversity turnover — biogeography of motif diversity (analysis #5).

Ecology's alpha / gamma / beta split applied to motifs by macro-area. The honest twist:
per-tradition richness (alpha) is dominated by cataloguing effort (over-studied Europe on top),
so it is NOT a diversity signal. **Beta-diversity (turnover = gamma/alpha)** is far less
effort-driven and IS informative: low beta = a homogeneous shared stock (a diffusion belt),
high beta = internally divergent traditions. Deterministic; writes data.js.
"""
import json, sys
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mockups"))
from _geo import berezkin_coords  # noqa: E402
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
COORD = berezkin_coords()
def coord(t):
    if t in COORD: return COORD[t]
    p=t.split(".")
    for i in range(len(p)-1,0,-1):
        k=".".join(p[:i])
        if k in COORD: return COORD[k]
    return None
def macro(t):
    ap=TR[t].get("areal_path") or []; return ap[0][1] if ap and ap[0] else "?"
SHORT={"NORTHERN AND EASTERN EUROPE":"N&E Europe","WESTERN EUROPE, NORTH AFRICA":"W-Eur/N-Afr",
 "SOUTHWEST AND CENTRAL ASIA, ARYAN INDIA":"SW/C-Asia·India","TIBET, NON-ARYAN SOUTH ASIA, SOUTHEAST ASIA":"Tibet/SE-Asia",
 "EAST ASIA":"East Asia","SIBERIA – MONGOLIA":"Siberia–Mongolia","BERINGIA":"Beringia","OCEANIA":"Oceania",
 "AUSTRALIA":"Australia","Sub-Saharan Africa":"Sub-Sah. Africa","NORTH AMERICA: NORTH AND WEST":"N America",
 "PLAINS AND SOUTHEAST":"Plains/SE","MEXICO – CENTRAL ANDES":"Meso/Andes","EASTERN SOUTH AMERICA":"E-S America",
 "SOUTHERN SOUTH AMERICA":"S Cone"}
tmot=defaultdict(set)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): tmot[t].add(j)
keep=[t for t in TR if len(tmot[t])>=15 and coord(t)]
by=defaultdict(list)
for t in keep: by[macro(t)].append(t)
rows=[]
for a,ts in by.items():
    if len(ts)<8: continue
    alpha=float(np.mean([len(tmot[t]) for t in ts]))
    gamma=len(set().union(*[tmot[t] for t in ts]))
    beta=gamma/alpha
    c=coord(ts[0]); cs=[coord(t) for t in ts]
    rows.append({"area":a,"short":SHORT.get(a,a),"n":len(ts),
                 "alpha":round(alpha),"gamma":gamma,"beta":round(beta,2),
                 "lat":round(float(np.mean([p[0] for p in cs])),1),
                 "lon":round(float(np.mean([p[1] for p in cs])),1)})
rows.sort(key=lambda r:-r["beta"])
# per-tradition points for the map, coloured by their region's beta
bmin=min(r["beta"] for r in rows); bmax=max(r["beta"] for r in rows)
areabeta={r["area"]:r["beta"] for r in rows}
pts=[]
for t in keep:
    a=macro(t)
    if a not in areabeta: continue
    c=coord(t)
    pts.append({"lon":round(c[1],1),"lat":round(c[0],1),"beta":areabeta[a],
                "name":TR[t]["name"],"area":SHORT.get(a,a)})
# effort-confound illustration: corr(alpha, n) essentially; report alpha rank vs beta rank
data={"rows":rows,"points":pts,"bmin":round(bmin,2),"bmax":round(bmax,2),
      "note":"Biogeography of motif diversity by macro-area. Alpha (per-tradition richness) tracks cataloguing effort (Europe highest) — not a diversity signal. Beta = turnover (gamma/alpha), less effort-driven: low beta = homogeneous shared stock (diffusion belt), high beta = internally divergent traditions."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"{len(rows)} areas · beta {bmin:.1f}–{bmax:.1f} · {len(pts)} points")
