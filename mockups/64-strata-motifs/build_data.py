"""Precompute strata × motif set-algebra for mockup 64 → gitignored data.js.

The regions map (mockup 62) is a *horizontal* cut through vertically layered material
(docs/proposals/regions.md §3: substrate → expansion → literate overlay). This mockup makes the
*vertical* cut: it groups traditions by the historical layer they share, then intersects
those groups with the Berezkin motif index to derive the motif set characteristic of each
layer — using set algebra, not statistical enrichment.

Three grouping axes, one shared method (see index.html for the live strictness slider):

  strata   — 3 depth bands (forager substrate / Neolithic-Bronze expansions / literate states),
             classified by the stratum at which each of our 14 canon regions *coheres*.
  religion — the great scriptural overlays as an areal cut (Christian Märchen belt, Islamic
             belt, Buddhist belt) — cross-cuts the deep regions.
  events   — concrete empires / migrations (Austronesian, Bantu, Na-Dene, Inca, Thule,
             Turko-Mongol) as small area sets.

For every group and every motif we store (inside, outside) = how many of the group's Berezkin
areas carry the motif vs how many areas *outside* the group do. The slider then filters live:
  strict   → motif in ALL group areas AND in NO outside area (∩ & exclusive)
  relaxed  → motif in ≥half the group areas AND in ≤k outside areas ("rare outside")
Strict exclusion suits broad cross-continental layers; single migrations need the relaxed end.

    python mockups/64-strata-motifs/build_data.py
"""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
bz = json.loads((ROOT / "outputs/motifs/berezkin.json").read_text())
AREAS, MOT = bz["areas"], bz["motifs"]  # AREAS: {id: ru label}; MOT: list of motif dicts

# 65 Berezkin areas → our 14 canon regions (re-mapped to OUR classification, not raw Berezkin
# macro-areas). Kept identical to docs/proposals/regions.md's region assignments.
A2R = {
    "10": "Sub-Saharan Africa", "11": "Sub-Saharan Africa", "12": "Sub-Saharan Africa",
    "13": "Sub-Saharan Africa",
    "14": "Near East & North Africa", "17": "Near East & North Africa",
    "15": "Europe", "16": "Europe", "27": "Europe", "28": "Europe", "31": "Europe", "32": "Europe",
    "29": "Caucasus & Iran", "30": "Caucasus & Iran",
    "21": "Inner Asia", "33": "Inner Asia", "34": "Inner Asia",
    "23": "South Asia", "22": "Mainland Southeast Asia", "26": "East Asia", "38": "East Asia",
    "20": "Austronesia", "24": "Austronesia", "25": "Austronesia",
    "18": "Papua & Aboriginal Australia", "19": "Papua & Aboriginal Australia",
    "35": "Circumpolar North", "36": "Circumpolar North", "37": "Circumpolar North",
    "39": "Circumpolar North", "40": "Circumpolar North", "41": "Circumpolar North",
    "42": "Native North America", "43": "Native North America", "44": "Native North America",
    "45": "Native North America", "46": "Native North America", "47": "Native North America",
    "48": "Native North America", "49": "Native North America", "50": "Native North America",
    "51": "Mesoamerica & the Andes", "52": "Mesoamerica & the Andes", "53": "Mesoamerica & the Andes",
    "55": "Mesoamerica & the Andes", "60": "Mesoamerica & the Andes", "65": "Mesoamerica & the Andes",
    "54": "Lowland South America", "56": "Lowland South America", "57": "Lowland South America",
    "58": "Lowland South America", "59": "Lowland South America", "61": "Lowland South America",
    "62": "Lowland South America", "63": "Lowland South America", "64": "Lowland South America",
    "66": "Lowland South America", "67": "Lowland South America", "68": "Lowland South America",
    "69": "Lowland South America", "70": "Lowland South America", "71": "Lowland South America",
    "72": "Lowland South America", "73": "Lowland South America", "74": "Lowland South America",
}
assert set(A2R) == set(AREAS), set(AREAS) - set(A2R)

# each canon region → the depth band at which it *coheres* (docs/proposals/regions.md §3, "a region's
# coherence lives at one particular stratum"). Illustrative expert classification, 5 / 5 / 4.
BAND = {
    "Sub-Saharan Africa": "I", "Circumpolar North": "I", "Papua & Aboriginal Australia": "I",
    "Native North America": "I", "Lowland South America": "I",
    "Europe": "II", "Inner Asia": "II", "Austronesia": "II", "South Asia": "II",
    "Mainland Southeast Asia": "II",
    "Near East & North Africa": "III", "Caucasus & Iran": "III", "East Asia": "III",
    "Mesoamerica & the Andes": "III",
}
BANDS = [
    ("I", "Форагерный субстрат", "Палеолит, >20 тыс. лет назад",
     "Дописьменный охотничье-собирательский базовый пласт — регионы, чья связность лежит "
     "на самом глубоком, доземледельческом слое."),
    ("II", "Неолитические и бронзовые экспансии", "~7000–1000 лет до н.э.",
     "Расселение одной языковой семьи поверх субстрата — индоевропейцы, австронезийцы, "
     "степные кочевники. Регион когерентен на слое экспансии."),
    ("III", "Государства и письменность", "с ~3000 лет до н.э.",
     "Городские цивилизации с письменной традицией — связность на литературном/"
     "государственном слое, поверх более глубоких субстратов."),
]

# scriptural overlays as an areal cut (Berezkin area ids). Cross-cut the deep regions.
RELIGION = [
    ("christ", "Христианство — европейский Märchen-слой", ["15", "16", "27", "28", "31", "32"],
     "Южная, Западная, Балканская, Центральная, Северная Европа, Поволжье"),
    ("islam", "Ислам — от Магриба до Туркестана", ["14", "17", "30", "33", "24"],
     "Северная Африка, Ближний Восток, Иран, Туркестан, Малайско-индонезийский мир"),
    ("buddh", "Буддизм — от Тибета до Японии", ["21", "22", "26", "34", "38"],
     "Тибет, Индокитай, Китай-Корея, Южная Сибирь-Монголия, Япония"),
    ("hindu", "Индуизм — индийский культурный круг (Greater India)", ["23", "21", "22", "24"],
     "Южная Азия, Гималаи-СВ Индия, Бирма-Индокитай, Малайзия-Индонезия (индианизированная зона; "
     "ареалы перекрываются с буддийскими — оба круга расходятся из Индии)"),
]

# concrete empires / migrations as small area sets.
EVENTS = [
    ("austro", "Австронезийская экспансия", "~3000 лет до н.э.", ["20", "24", "25"],
     "Полинезия-Микронезия, Малайско-индонезийский мир, Тайвань-Филиппины"),
    ("bantu", "Экспансия банту", "~1000 до н.э. – 500 н.э.", ["10", "11"],
     "Юго-западная и бантуязычная Африка"),
    ("nadene", "Миграция на-дене / атабасков", "~1–2 тыс. лет назад", ["41", "50"],
     "Субарктика → Большой Юго-Запад (навахо, апачи)"),
    ("inca", "Андские государства / инки", "~500–1500 н.э.", ["55", "60", "65"],
     "Северные Анды, Эквадор, Центральные Анды"),
    ("thule", "Эскимо-алеуты / культура Туле", "~1000 н.э.", ["39", "40"],
     "Северо-восточная Азия, Арктика"),
    ("turkomongol", "Тюрко-монгольская степь", "1 тыс. до н.э. – 2 тыс. н.э.", ["33", "34"],
     "Туркестан, Южная Сибирь-Монголия"),
]

# --- indices ---
# area_mot: Berezkin area → set of motif ids (unit for religion/event axes — small area sets)
# reg_mot:  our region → set of motif ids (any of its areas; unit for the depth-strata axis —
#           without this a broad band would demand a motif span dozens of areas and vanish)
area_mot = defaultdict(set)
for m in MOT:
    for a in m["areas"]:
        sa = str(a)
        if sa in A2R:
            area_mot[sa].add(m["id"])
ALL_AREAS = set(A2R)
ALL_REGIONS = sorted(set(A2R.values()))
reg_mot = defaultdict(set)
for a in ALL_AREAS:
    reg_mot[A2R[a]] |= area_mot[a]
area_out = defaultdict(int)  # motif → # of the 65 areas carrying it
for a in ALL_AREAS:
    for mi in area_mot[a]:
        area_out[mi] += 1
reg_out = defaultdict(int)   # motif → # of the 14 regions carrying it
for r in ALL_REGIONS:
    for mi in reg_mot[r]:
        reg_out[mi] += 1

name_ru = {m["id"]: (m.get("name_rus") or m["name"]) for m in MOT}
name_en = {m["id"]: m["name"] for m in MOT}
grp_ru = {m["id"]: (m.get("motif_group") or "") for m in MOT}

used = set()  # motif ids that survive pruning anywhere (for the compact motif table)


def rows_for(unit_sets, out_total):
    """Given {unit → motif set} for a group's units, return [id, inside, outside] for every
    motif in ≥2 units and in ≤4 units *outside* the group. inside/outside are unit counts;
    `out_total` maps motif → total units carrying it (band regions ∪ world, or all 65 areas)."""
    inside = defaultdict(int)
    for s in unit_sets:
        for mi in s:
            inside[mi] += 1
    rows = []
    for mi, ins in inside.items():
        if ins < 2:
            continue
        out = out_total[mi] - ins  # units outside the group carrying the motif
        if out > 4:
            continue
        rows.append([mi, ins, out])
        used.add(mi)
    rows.sort(key=lambda r: (r[2], -r[1], r[0]))  # most-exclusive first, then broadest inside
    return rows


strata_groups = []
for key, title, dating, blurb in BANDS:
    carriers = sorted(r for r in ALL_REGIONS if BAND[r] == key)
    strata_groups.append({
        "key": key, "title": f"{key} · {title}", "dating": dating, "blurb": blurb,
        "carriers": carriers, "unit": "регион", "insize": len(carriers),
        "rows": rows_for([reg_mot[r] for r in carriers], reg_out),
    })

religion_groups = []
for key, title, areas, blurb in RELIGION:
    religion_groups.append({
        "key": key, "title": title, "dating": "", "blurb": blurb,
        "carriers": [AREAS[a] for a in areas], "unit": "ареал", "insize": len(areas),
        "rows": rows_for([area_mot[a] for a in areas], area_out),
    })

event_groups = []
for key, title, dating, areas, blurb in EVENTS:
    event_groups.append({
        "key": key, "title": title, "dating": dating, "blurb": blurb,
        "carriers": [AREAS[a] for a in areas], "unit": "ареал", "insize": len(areas),
        "rows": rows_for([area_mot[a] for a in areas], area_out),
    })

motifs = {mi: {"ru": name_ru[mi], "en": name_en[mi], "grp": grp_ru[mi]} for mi in sorted(used)}
DATA = {
    "meta": {"n_motifs": len(MOT), "n_areas": len(AREAS)},
    "band_titles": {k: t for k, t, _d, _b in BANDS},
    "motifs": motifs,
    "axes": {
        "strata": {"label": "Глубинные страты", "groups": strata_groups},
        "religion": {"label": "Религиозные оверлеи", "groups": religion_groups},
        "events": {"label": "Империи и миграции", "groups": event_groups},
    },
}
(HERE / "data.js").write_text("window.DATA = " + json.dumps(DATA, ensure_ascii=False) + ";\n")
tot = sum(len(g["rows"]) for ax in DATA["axes"].values() for g in ax["groups"])
print(f"motifs table: {len(motifs)} | group rows: {tot} | "
      f"data.js {((HERE / 'data.js').stat().st_size / 1024):.0f}KB")
for ax in DATA["axes"].values():
    for g in ax["groups"]:
        print(f"  {g['insize']:>2} areas | {len(g['rows']):>4} rows | {g['title']}")
