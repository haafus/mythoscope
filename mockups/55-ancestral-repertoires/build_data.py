"""Mockup 55 · Ancestral repertoires — reconstructed proto-mythologies (analysis #9).

Ancestral-state reconstruction at the SET level: for a language family, a motif is reconstructed
present at the proto-node if it is attested in ≥2 of the family's primary sub-branches (parsimony:
present in two sister clades → present in their ancestor). Aggregated per family this gives a
reconstructed proto-repertoire — "the mythology of proto-Indo-Europeans / proto-Austronesians …" —
dated by the family's expansion age (M30 table). Deterministic; writes data.js.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parents[2]
bz = json.load(open(ROOT/"outputs"/"motifs"/"berezkin.json"))
TR, MOT = bz["traditions"], bz["motifs"]
join=json.loads((ROOT/"mockups"/"30-dated-phylogeny"/"glottolog_join.json").read_text())
gfam={t:j["gfam"] for t,j in join.items()}
spec=importlib.util.spec_from_file_location("m30",ROOT/"mockups"/"30-dated-phylogeny"/"build_data.py"); m30=importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(m30)
except SystemExit: pass
FAM=m30.FAMILY_DATES
def yl(y):
    ce=2000-y; return f"{-ce} BCE" if ce<0 else f"{ce} CE"

# motif → set of traditions
mot_tr=defaultdict(set)
for j,m in enumerate(MOT):
    for t in m.get("traditions",[]): mot_tr[j].add(t)
name={j:MOT[j].get("name","") for j in range(len(MOT))}
grp={j:MOT[j].get("motif_group_num") for j in range(len(MOT))}
mid={j:MOT[j]["id"] for j in range(len(MOT))}

# group traditions by Glottolog family; primary sub-branch = language-path level index 1 (fallback: the tradition)
famtr=defaultdict(list)
for t in TR:
    f=gfam.get(t)
    if f: famtr[f].append(t)
def subbranch(t):
    lp=TR[t].get("language") or []
    return lp[1] if len(lp)>1 else (lp[0] if lp else t)

FAMLIST=["Indo-European","Austronesian","Afro-Asiatic","Sino-Tibetan","Atlantic-Congo",
         "Uralic","Uto-Aztecan","Pama-Nyungan","Dravidian","Turkic"]
out_fams=[]
for f in FAMLIST:
    ts=famtr.get(f,[])
    if len(ts)<6: continue
    branches=defaultdict(set)
    for t in ts: branches[subbranch(t)].add(t)
    if len(branches)<2: continue
    bkeys=list(branches)
    recon=[]
    for j,trs in mot_tr.items():
        hit=[bk for bk in bkeys if trs & branches[bk]]
        if len(hit)>=2: recon.append((len(hit),j))
    recon.sort(key=lambda x:(-x[0], -len(mot_tr[x[1]])))
    age=FAM.get(f,[None])[0]
    out_fams.append({"family":f,"age":age,"label":(yl(age) if age else "—"),
                     "n_trad":len(ts),"n_branch":len(branches),"n_recon":len(recon),
                     "motifs":[{"id":mid[j],"name":name[j],"grp":grp[j],"branches":nb,
                                "of":len(branches)} for nb,j in recon[:22]]})
out_fams.sort(key=lambda x:-(x["age"] or 0))
data={"families":out_fams,
      "note":"Reconstructed proto-repertoires: a motif is placed at a family's proto-node if attested in ≥2 primary sub-branches (parsimony). Aggregated per family = a reconstructed proto-mythology, dated by the family's expansion age. Coarse (family-resolution, presence-only), not a Bayesian ASR."}
out=Path(__file__).parent/"data.js"
out.write_text("window.DATA = "+json.dumps(data,ensure_ascii=False)+";",encoding="utf-8")
print(f"families reconstructed: {len(out_fams)} · "+", ".join(x["family"][:12]+"("+str(x["n_recon"])+")" for x in out_fams))
