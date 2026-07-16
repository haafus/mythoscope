"""62 · Facet map — one world map, switch the tradition facet.

Colours the same set of Berezkin traditions on the world map by a chosen facet:
`area` (12, from areal_path), `family` (11, from language), or the dominant
`theme` group (13, argmax of the theme profile). `subsistence` is listed but has
no data source yet (needs a D-PLACE join) — it shows as a disabled facet so the
gap is visible rather than hidden. Reuses mockup 21's area/family functions and
mockup 16's coordinate resolution + jitter.

Run:  python mockups/62-facet-map/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"

K_CLUSTERS = 8  # tradition profile clusters (KMeans over the 16-dim narrative profile)

MIN_MOTIFS = 30  # below this a narrative profile is too noisy to call a dominant cluster

# Subsistence comes from D-PLACE (nearest society), reusing mockup 22's snapshot.
SUB_ORDER = ["forager", "pastoralist", "horticulturalist", "agrarian_state"]
SUB_LABEL = {"forager": "Foragers", "pastoralist": "Pastoralists",
             "horticulturalist": "Horticulturalists", "agrarian_state": "Agrarian states"}
MATCH_KM = 250.0  # a nearest-society join farther than this is dropped (too weak)

# One 16-colour qualitative ramp, sliced per facet (fixed order, never cycled).
RAMP = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
        "#e11d48", "#7d8b3a", "#0891b2", "#a3457e", "#4338ca", "#65a30d",
        "#be123c", "#0f766e", "#7c3aed", "#b45309"]

# Volume-balanced sections: Berezkin's areal subregions binned into 14 sections of roughly
# equal documentation volume (~8–10k motif attestations each), so no section is a heap and
# none is a single tradition. Heavy blocks (Europe, West Asia, N America) are split by
# areal_path subregion; thin ones (Oceania, Australia, East Asia) are pooled.
SECTIONS_VOL = [
    "Southern & Western Europe", "Slavic & Balkan", "Baltic, Scandinavia & Finno-Ugric",
    "Near East & North Africa", "Caucasus & Asia Minor", "South Asia & Himalaya",
    "East & Mainland SE Asia", "Austronesia & Oceania", "Sub-Saharan Africa", "Siberia",
    "Arctic & Northwest America", "North America - Plains, Woodlands & Southwest",
    "Mesoamerica & Andes", "Amazonia & Lowland South America",
]


def section_of(ap):
    """Assign a tradition (by its areal_path) to one volume-balanced section."""
    if not ap or not ap[0]:
        return None
    m0 = ap[0][1].upper()
    sub = ap[1][1].upper() if len(ap) > 1 and ap[1] else ""
    hs = lambda *ks: any(k in sub for k in ks)   # noqa: E731
    hm = lambda *ks: any(k in m0 for k in ks)    # noqa: E731
    if m0 == "WESTERN EUROPE, NORTH AFRICA":
        if hs("NORTH AFRICA", "HORN"):
            return "Near East & North Africa"
        if hs("BALKAN"):
            return "Slavic & Balkan"
        return "Southern & Western Europe"
    if m0 == "NORTHERN AND EASTERN EUROPE":
        return "Slavic & Balkan" if hs("SLAV") else "Baltic, Scandinavia & Finno-Ugric"
    if "SOUTHWEST AND CENTRAL ASIA" in m0 or hm("ARYAN INDIA"):
        if hs("CAUCASUS"):
            return "Caucasus & Asia Minor"
        if hs("ARYAN AND SOUTH INDIA"):
            return "South Asia & Himalaya"
        return "Near East & North Africa"
    if hm("TIBET") and hm("SOUTHEAST ASIA"):
        if hs("BURMA", "INDOCHINA"):
            return "East & Mainland SE Asia"
        if hs("NUSANTARA"):
            return "Austronesia & Oceania"
        return "South Asia & Himalaya"
    if hm("SIBERIA") and hm("MONGOLIA"):
        return "Siberia"
    if "NORTH AMERICA: NORTH AND WEST" in m0:
        if hs("SUBARCTIC", "NORTHWEST COAST", "PLATEAU"):
            return "Arctic & Northwest America"
        return "North America - Plains, Woodlands & Southwest"
    if hm("EAST ASIA"):
        return "East & Mainland SE Asia"
    if hm("OCEANIA", "AUSTRALIA", "MADAGASCAR"):
        return "Austronesia & Oceania"
    if hm("SUB-SAHARAN AFRICA"):
        return "Sub-Saharan Africa"
    if hm("BERINGIA"):
        return "Arctic & Northwest America"
    if hm("PLAINS AND SOUTHEAST"):
        return "North America - Plains, Woodlands & Southwest"
    if hm("MEXICO"):
        return "Mesoamerica & Andes"
    if hm("EASTERN SOUTH AMERICA", "SOUTHERN SOUTH AMERICA"):
        return "Amazonia & Lowland South America"
    return None


# The 14 canonical regions (research/regions.md) with their curated traditions and hand coordinates
# (lat, lon). This is NOT the Berezkin index — it is the catalogue's own tradition list, coloured by
# the CARTOColors Prism region palette (regions.md §8).
REGIONS = [
    ("Sub-Saharan Africa", "#CC503E", [
        ("Yoruba", 8, 4), ("Igbo", 6, 7), ("Akan/Ashanti", 7, -2), ("Fon", 7, 2), ("Dogon", 14, -3),
        ("Bambara", 13, -6), ("Serer", 14, -16), ("Kongo", -6, 14), ("Yombe", -5, 13),
        ("Zulu", -28, 31), ("Xhosa", -32, 27), ("Shona", -19, 30), ("Kikuyu", -1, 37),
        ("Baganda", 0, 32), ("Luba", -8, 24), ("Fang", 1, 11), ("Dinka", 8, 30), ("Nuer", 9, 32),
        ("Maasai", -2, 36), ("Azande", 5, 27), ("San", -22, 21), ("Khoekhoe", -29, 19),
        ("Mbuti", 1, 28), ("Ethiopian", 11, 39)]),
    ("Near East & North Africa", "#2A4895", [
        ("Sumerian", 31, 46), ("Akkadian", 33, 44), ("Babylonian", 32, 44.5), ("Assyrian", 36, 43),
        ("Egyptian", 26, 31), ("Hittite", 39, 33), ("Hurrian", 37, 41), ("Ugaritic", 35, 36),
        ("Phoenician", 34, 35), ("Elamite", 32, 48), ("pre-Islamic Arabian", 24, 45),
        ("Jewish", 31.5, 35), ("Christian", 31.8, 35.4), ("Islamic", 21, 40), ("Berber", 31, 3)]),
    ("Europe", "#EDAD08", [
        ("Greek", 39, 22), ("Roman", 42, 12.5), ("Etruscan", 43, 11.5), ("Celtic", 53, -8),
        ("Norse", 62, 10), ("Anglo-Saxon", 52, -1.5), ("Continental Germanic", 51, 10),
        ("Slavic", 51, 27), ("Baltic", 56, 24), ("Finnish", 62, 25), ("Estonian", 59, 26),
        ("Sami", 68, 22), ("Hungarian", 47, 19), ("Mordvin/Mari", 55, 46), ("Basque", 43, -2)]),
    ("Caucasus & Iran", "#6F4070", [
        ("Persian/Zoroastrian", 32, 53), ("Scythian", 47, 36), ("Sogdian", 39, 66),
        ("Ossetian", 43, 44), ("Armenian", 40, 45), ("Georgian", 42, 44), ("Circassian", 44, 40),
        ("Chechen/Vainakh", 43, 46), ("Dagestani", 42, 47.5), ("Kurdish", 37, 43), ("Azeri", 40, 48)]),
    ("Inner Asia", "#1D6996", [
        ("Turkic", 50, 88), ("Kyrgyz", 41, 75), ("Kazakh", 48, 68), ("Uyghur", 42, 82),
        ("Yakut/Sakha", 62, 130), ("Mongol", 47, 105), ("Buryat", 52, 108), ("Kalmyk", 46, 45),
        ("Tuvan", 51, 94), ("Altai", 50, 86), ("Tibetan", 30, 90), ("Manchu", 44, 125)]),
    ("South Asia", "#38A6A5", [
        ("Vedic", 29, 77), ("Hindu", 25, 80), ("Buddhist", 25, 85), ("Jain", 23, 78),
        ("Dravidian", 11, 78), ("Munda/Santal", 23, 86), ("Gond", 21, 80), ("Bhil", 23, 74),
        ("Sinhalese", 7, 81), ("Newar/Nepali", 28, 85), ("Sikh", 31, 75), ("Kashmiri", 34, 75)]),
    ("Mainland Southeast Asia", "#94346E", [
        ("Burmese", 21, 96), ("Mon", 16, 97), ("Thai/Tai", 15, 100), ("Lao", 18, 103),
        ("Shan", 22, 98), ("Khmer", 12, 105), ("Vietnamese", 18, 106), ("Cham", 13, 109),
        ("Hmong-Mien", 24, 104), ("Karen", 18, 97.5), ("Tibeto-Burman", 26, 95)]),
    ("East Asia", "#E17C05", [
        ("Chinese", 34, 110), ("Korean", 37, 128), ("Japanese", 36, 138), ("Ryukyuan", 26, 128),
        ("Ainu", 43, 143), ("Yi", 26, 102)]),
    ("Austronesia", "#0F8554", [
        ("Formosan", 23.5, 121), ("Javanese", -7, 110), ("Balinese", -8, 115), ("Sundanese", -7, 107),
        ("Batak", 2, 99), ("Dayak", 0, 114), ("Toraja", -3, 120), ("Filipino", 15, 121),
        ("Malay", 3, 102), ("Maori", -41, 175), ("Hawaiian", 20, -157), ("Tahitian", -17, -149),
        ("Samoan", -14, -172), ("Tongan", -21, -175), ("Rapa Nui", -27, -109), ("Micronesian", 7, 150),
        ("Fijian", -18, 178), ("Malagasy", -19, 47)]),
    ("Papua & Aboriginal Australia", "#A9773F", [
        ("Arrernte", -24, 134), ("Yolngu", -12, 136), ("Warlpiri", -20, 131), ("Pitjantjatjara", -26, 131),
        ("Enga", -5.5, 143.5), ("Huli", -6, 143), ("Melanesian", -6, 147)]),
    ("Circumpolar North", "#5F4690", [
        ("Chukchi", 66, 175), ("Koryak", 62, 166), ("Yukaghir", 68, 150), ("Nivkh", 53, 142),
        ("Itelmen", 56, 159), ("Evenki", 60, 100), ("Even", 63, 140), ("Khanty", 62, 70),
        ("Mansi", 62, 62), ("Nenets", 68, 73), ("Ket", 63, 88), ("Yupik", 61, -162),
        ("Inupiat", 70, -153), ("Kalaallit", 72, -40), ("Aleut", 53, -170), ("Dene", 62, -130),
        ("Northern Cree", 54, -80)]),
    ("Native North America", "#73AF48", [
        ("Iroquois", 43, -76), ("Ojibwe", 47, -90), ("Abenaki", 45, -71), ("Lakota/Sioux", 44, -101),
        ("Cheyenne", 40, -104), ("Pawnee", 41, -98), ("Blackfoot", 49, -113), ("Nez Perce", 46, -116),
        ("Salish", 48, -120), ("Pomo", 39, -123), ("Miwok", 38, -120), ("Yokuts", 36, -119),
        ("Navajo", 36, -109), ("Hopi", 36, -110.5), ("Zuni", 35, -108.5), ("Pueblo", 35.5, -106),
        ("Apache", 33, -109.5), ("Tlingit", 58, -134), ("Haida", 53, -132), ("Kwakwaka'wakw", 51, -127),
        ("Tsimshian", 54, -130)]),
    ("Mesoamerica & the Andes", "#994E95", [
        ("Aztec/Nahua", 19, -99), ("Maya", 17, -89), ("Mixtec", 17, -97), ("Zapotec", 17, -96),
        ("Olmec", 18, -94), ("Toltec", 20, -99.3), ("Tarascan", 19.5, -101), ("Huichol", 22, -104),
        ("Inca/Quechua", -13, -72), ("Aymara", -16, -69), ("Moche", -8, -79), ("Chibcha/Muisca", 5, -74),
        ("Nazca", -14, -75)]),
    ("Lowland South America", "#2A8A9F", [
        ("Tupí/Guaraní", -20, -50), ("Carib", 8, -62), ("Arawak", 3, -60), ("Ge", -10, -52),
        ("Yanomami", 2, -64), ("Tucano", -1, -70), ("Jivaro/Shuar", -3, -78), ("Warao", 9, -62),
        ("Mapuche", -38, -71), ("Selk'nam", -54, -68), ("Tehuelche", -46, -70), ("Guaycuru", -24, -58)]),
]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sunflower(j, n):
    r = math.sqrt((j + 0.5) / n)
    a = j * math.pi * (3 - math.sqrt(5))
    return r * math.cos(a), r * math.sin(a)


def _haversine(lat, lon, lats, lons):
    lat, lon = math.radians(lat), math.radians(lon)
    lats, lons = np.radians(lats), np.radians(lons)
    dlat, dlon = lats - lat, lons - lon
    h = np.sin(dlat / 2) ** 2 + math.cos(lat) * np.cos(lats) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


# dark ramp end per region (regions.md §8) — used for the tradition dots on the areas facet
REGION_DARK = {
    "Sub-Saharan Africa": "#953223", "Near East & North Africa": "#162857", "Europe": "#9B7208",
    "Caucasus & Iran": "#3C223D", "Inner Asia": "#0E3A54", "South Asia": "#216B6A",
    "Mainland Southeast Asia": "#591D41", "East Asia": "#8D5007", "Austronesia": "#075534",
    "Papua & Aboriginal Australia": "#6E4C24", "Circumpolar North": "#3A2A5A",
    "Native North America": "#4D772E", "Mesoamerica & the Andes": "#643162",
    "Lowland South America": "#175361",
}


def region_borders(regions):
    """Region areas as filled polygons draped over real vector borders (Natural Earth
    countries/provinces), precomputed by build_region_geo.py into regions_geo.json.
    Returns a cat per region with its combined SVG path; Antarctica is left blank."""
    geo = json.loads((Path(__file__).resolve().parent / "regions_geo.json").read_text())
    return [{"name": name, "color": color, "dark": REGION_DARK[name], "d": geo.get(name, "")}
            for name, color, _ in regions]


# predominant-religion choropleth palette (Abrahamic = cool, Islam = green, Indic = warm,
# East Asian = red); paths precomputed by build_religions_geo.py into religions_geo.json
RELIGIONS = [
    ("Catholic Christianity", "#2C6FB3"), ("Orthodox Christianity", "#7048B6"),
    ("Protestant / other Christian", "#6FB1DE"), ("Sunni Islam", "#3E9B57"),
    ("Shia Islam", "#0B7A7A"), ("Judaism", "#16365C"), ("Hinduism", "#E07B1A"),
    ("Buddhism", "#E6B93E"), ("East Asian (folk / syncretic)", "#C0392B"),
    ("Ethnic / traditional", "#744A28"),
]


def religion_borders():
    """Predominant religion per country as filled polygons (same Natural Earth borders as
    the regions areas facet), precomputed by build_religions_geo.py into religions_geo.json."""
    geo = json.loads((Path(__file__).resolve().parent / "religions_geo.json").read_text())
    return [{"name": name, "color": color, "d": geo.get(name, "")} for name, color in RELIGIONS]


# substrate-strength choropleth — a sequential earth ramp (strong = dark), precomputed by
# build_substrate_geo.py; how strongly the pre-scriptural indigenous layer survives as practice
SUBSTRATE = [
    ("Very strong", "#5C3A1A"), ("Strong", "#8A5E30"), ("Moderate", "#B5895A"),
    ("Weak", "#CBB187"), ("Very weak", "#E0CFB0"),
]


def substrate_borders():
    geo = json.loads((Path(__file__).resolve().parent / "substrate_geo.json").read_text())
    return [{"name": name, "color": color, "d": geo.get(name, "")} for name, color in SUBSTRATE]


# language facets, precomputed by build_lang_geo.py (illustrative groupings, see that file)
FAMILIES = [  # predominant (indigenous) language family — qualitative
    ("Indo-European", "#4C78A8"), ("Sino-Tibetan", "#E45756"), ("Niger-Congo", "#F58518"),
    ("Afroasiatic", "#72B7B2"), ("Austronesian", "#54A24B"), ("Dravidian", "#B279A2"),
    ("Turkic", "#EECA3B"), ("Uralic", "#9D755D"), ("Austroasiatic", "#FF9DA6"),
    ("Tai-Kadai", "#17BECF"), ("Japonic & Koreanic", "#D37295"), ("Mongolic", "#BAB03B"),
    ("Nilo-Saharan", "#5B5BA0"), ("Papuan (New Guinea)", "#79706E"),
    ("Australian (Aboriginal)", "#C49C94"),
    ("North America (many families)", "#7FBF7B"), ("Mesoamerica (Uto-Aztecan, Maya…)", "#C7B241"),
    ("Andean (Quechua–Aymara)", "#3E9E8F"), ("Amazonian & Southern (many families)", "#A6D96A"),
]
LANGDIV = [  # linguistic diversity / fragmentation — sequential purple, dark = high
    ("Very high", "#54278F"), ("High", "#756BB1"), ("Moderate", "#9E9AC8"),
    ("Low", "#CBC9E2"), ("Very low", "#EFEDF5"),
]
ZONES = [  # Nichols spread<->residual as a sequential blue ramp, dark = strongest residual.
    # lightest step lifted off #EFF3FF (≈ ocean #eef3f4) to a clear pale blue: at the
    # facet's 0.4 fill-opacity #EFF3FF dissolved into the sea and the land read as hollow.
    ("Strong spread", "#C4D8EF"), ("Spread", "#BDD7E7"), ("Mixed", "#6BAED6"),
    ("Residual", "#3182BD"), ("Strong residual", "#08519C"),
]


def _geo_cats(filename, palette):
    geo = json.loads((Path(__file__).resolve().parent / filename).read_text())
    return [{"name": name, "color": color, "d": geo.get(name, "")} for name, color in palette]


def main():
    geo = _load("_geo", MOCKS / "_geo.py")
    f21 = _load("_f21", MOCKS / "21-facet-population" / "build_data.py")
    coords = geo.berezkin_coords()

    # Hard layers: the coverage-corrected recursive geo-peel of mockup 45. Importing it runs
    # the peel; each kept tradition lands in a leaf stratum with its own name and colour.
    m45 = _load("_m45", MOCKS / "45-stratigraphic-peeling" / "build_data.py")
    hard_cats = [{"name": nd["name"], "color": nd["color"]} for nd in m45.leaves]
    hard_ix = {nd["id"]: i for i, nd in enumerate(m45.leaves)}
    tid_hard = {m45.keep[i]: hard_ix[lid] for i, lid in m45.leaf_of.items() if lid in hard_ix}

    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # Data-driven narrative clusters (mockup 41): each motif → one of 16 named clusters.
    # The dominant theme (Berezkin's 13) is uninformative — "Adventures" swamps everything —
    # so the theme facet uses the balanced narrative clusters instead.
    with open(MOCKS / "41-theme-rederivation" / "narrative_taxonomy.json", encoding="utf-8") as f:
        tax = json.load(f)
    NT = tax["motifs"]
    NARR = [c["name"] for c in sorted(tax["clusters"], key=lambda c: c["l1"])]

    # per-tradition narrative-cluster counts → dominant cluster
    prof = defaultdict(lambda: np.zeros(len(NARR)))
    for r in bz["motifs"]:
        nt = NT.get(r["id"])
        if nt:
            for tid in (r.get("traditions") or []):
                prof[tid][nt["l1"]] += 1

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])   # [lat,lon] -> (lon,lat)
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    # D-PLACE societies (id, name, lat, lon, subsistence bucket) — mockup 22's snapshot.
    with open(MOCKS / "22-subsistence-external" / "dplace_subsistence.json", encoding="utf-8") as f:
        dp = json.load(f)
    dp_lat = np.array([s["lat"] for s in dp])
    dp_lon = np.array([s["lon"] for s in dp])
    dp_sub = [s["s"] for s in dp]

    area_ix = {a: i for i, a in enumerate(f21.AREAS12)}
    fam_ix = {a: i for i, a in enumerate(f21.FAMILIES11)}
    sub_ix = {s: i for i, s in enumerate(SUB_ORDER)}

    recs = []  # [tid, lon, lat, area_idx, fam_idx, narr_cluster, sub_idx]  (-1 = no value)
    prof_rows, prof_tids = [], []   # narrative profiles of placed, well-attested traditions
    for t, v in T.items():
        xy = coord(t)
        if not xy:
            continue
        lon, lat = xy
        ap = v.get("areal_path") or []
        area = f21.area_of(ap)
        lang0 = (v.get("language") or [None])[0]
        family, _ = f21.family_of(lang0, area)
        d = _haversine(lat, lon, dp_lat, dp_lon)
        j = int(np.argmin(d))
        sub = sub_ix[dp_sub[j]] if d[j] <= MATCH_KM else -1
        recs.append([t, lon, lat, area_ix.get(area, -1), fam_ix.get(family, -1), -1, sub])
        p = prof.get(t)
        if p is not None and p.sum() >= MIN_MOTIFS:
            prof_rows.append(p / p.sum())
            prof_tids.append(t)

    # Cluster the traditions by their narrative profile (mockup 43's move), then colour
    # each tradition by its profile cluster — not by a single dominant motif group.
    X = np.array(prof_rows)
    labels = KMeans(n_clusters=K_CLUSTERS, random_state=0, n_init=10).fit(X).labels_
    sizes = [int((labels == c).sum()) for c in range(K_CLUSTERS)]
    order = sorted(range(K_CLUSTERS), key=lambda c: -sizes[c])   # biggest cluster first
    remap = {c: i for i, c in enumerate(order)}
    # Name a cluster by what it over-represents vs the global mean (its *distinctive*
    # complexes), not its biggest dims — those are shared across clusters and don't separate them.
    gm = X.mean(0)
    cluster_names = [" · ".join(NARR[k] for k in (X[labels == c].mean(0) - gm).argsort()[::-1][:2])
                     for c in order]
    tid_cluster = {t: remap[int(labels[i])] for i, t in enumerate(prof_tids)}
    for r in recs:
        r[5] = tid_cluster.get(r[0], -1)

    # spread points sharing a base coordinate so nothing piles up (mockup 16 recipe)
    groups = defaultdict(list)
    for i, r in enumerate(recs):
        groups[(round(r[1], 2), round(r[2], 2))].append(i)
    xy_by_i = {}
    for (lon, lat), members in groups.items():
        members.sort(key=lambda i: recs[i][0])
        n = len(members)
        span = 1.1 * math.sqrt(n)
        for j, i in enumerate(members):
            ox, oy = _sunflower(j, n)
            xy_by_i[i] = (round(lon + ox * span * 1.35, 2), round(lat + oy * span, 2))

    # Motif diversity (mockup 52): β-turnover (γ/α) per macro-area, broadcast to its traditions.
    # Continuous, not categorical: α (per-tradition richness) tracks cataloguing effort; β does not.
    tmot = defaultdict(set)
    for k, m in enumerate(bz["motifs"]):
        for t in (m.get("traditions") or []):
            tmot[t].add(k)

    def _macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap and ap[0] else None

    by_macro = defaultdict(list)
    for r in recs:
        if len(tmot[r[0]]) >= 15:
            by_macro[_macro(r[0])].append(r[0])
    area_beta = {}
    for a, ts in by_macro.items():
        if a is None or len(ts) < 8:
            continue
        alpha = float(np.mean([len(tmot[t]) for t in ts]))
        area_beta[a] = len(set().union(*[tmot[t] for t in ts])) / alpha
    tid_beta = {r[0]: area_beta[_macro(r[0])] for r in recs if _macro(r[0]) in area_beta}

    # Tradition depth = mean depth-rank of its motifs. Motif depth = breadth (# attesting
    # traditions, mockup 17); breadth is heavy-tailed, so a raw mean is distorted by the few
    # pan-global motifs. Rank-transform each motif's breadth to a 0–1 percentile first, then
    # average over the tradition: bounded, robust, and uses every motif (not just a top tier).
    breadth = np.array([len(m.get("traditions") or []) for m in bz["motifs"]])
    rank = (rankdata(breadth, method="average") - 1) / (len(breadth) - 1)   # 0..1 depth percentile
    tid_depth = {}
    for r in recs:
        ms = list(tmot[r[0]])
        if len(ms) >= 8:
            tid_depth[r[0]] = float(np.mean([rank[k] for k in ms]))

    # Coverage correction: depth is negatively confounded by coverage a(t) = richness — a thickly
    # catalogued corpus records more rare local motifs and looks artificially shallow (mockup 39).
    # Partial it out: replace depth with the residual of depth on log-coverage, i.e. how deep a
    # tradition is *relative to what its cataloguing level predicts*. >0 = deeper than expected.
    dep_tids = list(tid_depth)
    logcov = np.log([len(tmot[t]) for t in dep_tids])
    dy = np.array([tid_depth[t] for t in dep_tids])
    slope, intercept = np.polyfit(logcov, dy, 1)
    tid_depth = {t: float(dy[i] - (slope * logcov[i] + intercept)) for i, t in enumerate(dep_tids)}

    # Histogram-equalize the corrected depth for the map: colour by a tradition's rank among all
    # traditions (0–1), so the concentrated middle spreads across the full ramp instead of one shade.
    srt = sorted(tid_depth, key=lambda t: tid_depth[t])
    depth_eq = {t: i / (len(srt) - 1) for i, t in enumerate(srt)} if len(srt) > 1 else {}

    # Category-A (cosmology) share: Berezkin groups 01–09 (A: cosmology/etiology) vs 10–13
    # (B: adventures/tricks) per tradition. High = cosmology-heavy corpus.
    grpA, grpAB = defaultdict(int), defaultdict(int)
    for m in bz["motifs"]:
        g = m.get("motif_group_num")
        if g and 1 <= int(g) <= 13:
            for t in (m.get("traditions") or []):
                grpAB[t] += 1
                if int(g) <= 9:
                    grpA[t] += 1
    tid_cosmo = {t: grpA[t] / grpAB[t] for t in grpAB if grpAB[t] >= 15}

    # Peopling age (ky BP) of a tradition's macro-area — the validation axis for depth (mockup 39).
    PEOPLING = {
        "Sub-Saharan Africa": 65, "Aboriginal Australia": 50, "East & SE Asia": 50,
        "Iran, C. & S. Asia": 45, "Near East & N. Africa": 45, "Europe": 42,
        "Austronesia & Oceania": 33, "Siberia & Beringia": 32,
        "Northern & Western N. America": 15, "Eastern North America": 15,
        "Mesoamerica & Andes": 14, "South America": 14,
    }
    tid_peo = {r[0]: PEOPLING[f21.AREAS12[r[3]]] for r in recs
               if r[3] >= 0 and f21.AREAS12[r[3]] in PEOPLING}

    vsec_ix = {s: i for i, s in enumerate(SECTIONS_VOL)}
    tid_vsec = {t: vsec_ix.get(section_of(v.get("areal_path") or []), -1)
                for t, v in T.items()}

    points = [{"x": xy_by_i[i][0], "y": xy_by_i[i][1],
               "h": tid_hard.get(r[0], -1), "v": tid_vsec.get(r[0], -1),
               "a": r[3], "f": r[4], "n": r[5], "s": r[6],
               "d": round(tid_beta[r[0]], 3) if r[0] in tid_beta else None,
               "p": round(depth_eq[r[0]], 3) if r[0] in depth_eq else None,
               "c": round(tid_cosmo[r[0]], 3) if r[0] in tid_cosmo else None,
               "e": tid_peo.get(r[0])}
              for i, r in enumerate(recs)]

    def facet(label, cats, key, colors=None):
        counts = Counter(p[key] for p in points if p[key] >= 0)
        return {
            "label": label,
            "cats": [{"name": c, "color": (colors or RAMP)[i % len(colors or RAMP)],
                      "n": counts.get(i, 0)}
                     for i, c in enumerate(cats)],
        }

    # forager · pastoralist · horticulturalist · agrarian_state — a jewel/earth set:
    # slate-blue / terracotta / teal-green / plum. Contrasting but not flat primaries.
    sub_colors = ["#3f6f9e", "#cc7a33", "#2f8f6b", "#9c4576"]
    betas = list(tid_beta.values())
    cosmos = list(tid_cosmo.values())
    peos = list(tid_peo.values())
    facets = {
        "area": facet(f"Area · {len(f21.AREAS12)}", f21.AREAS12, "a"),
        "family": facet(f"Family · {len(f21.FAMILIES11)}", f21.FAMILIES11, "f"),
        "narrative": facet(f"Narrative · {K_CLUSTERS}", cluster_names, "n"),
        "subsistence": facet("Subsistence · 4",
                             [SUB_LABEL[s] for s in SUB_ORDER], "s", sub_colors),
        "diversity": {
            "label": "Motif diversity",
            "kind": "continuous", "key": "d", "unit": "β = γ/α",
            "min": round(min(betas), 2), "max": round(max(betas), 2),
            # mockup 52's blue→red β scale, blue end softened (lighter, less saturated).
            "ramp": ["#83a4c6", "#e65a46"],
            "note": "β-turnover (γ/α) по макроареалу: низкий — общий фонд мотивов, высокий — "
                    "внутренне разнородный (мокап 52)",
        },
        "depth": {
            "label": "Tradition depth",
            "kind": "continuous", "key": "p", "unit": "перцентиль среди традиций",
            "min": 0, "max": 1,
            # high-contrast light→dark (YlOrRd): shallow = pale, deep = dark red.
            "ramp": ["#ffffcc", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
            "note": "средний ранг глубины мотивов традиции с поправкой на покрытие — "
                    ">0 = глубже, чем предсказывает каталогизация (мокапы 17/39)",
        },
        "cosmology": {
            "label": "Cosmology",
            "kind": "continuous", "key": "c", "unit": "доля Категории A",
            "min": round(min(cosmos), 2), "max": round(max(cosmos), 2),
            # sequential purple: low (adventure-heavy) → high (cosmology-heavy).
            "ramp": ["#f3eef8", "#c8a8dd", "#9151d8", "#4a1e77"],
            "note": "доля мотивов Категории A — космогония/этиология против приключений "
                    "(мокапы 22/24)",
        },
        "peopling": {
            "label": "Peopling age",
            "kind": "continuous", "key": "e", "unit": "ky BP",
            "min": min(peos), "max": max(peos),
            # sequential green: recently peopled (pale) → anciently peopled (dark).
            "ramp": ["#ffffcc", "#addd8e", "#41ab5d", "#005a32"],
            "note": "возраст первого заселения макроареала, тыс. лет назад (мокап 39)",
        },
    }
    facets["volume"] = facet(f"Volume · {len(SECTIONS_VOL)}", SECTIONS_VOL, "v")
    facets["volume"]["note"] = ("разделы, сбалансированные по объёму фиксации Березкина — "
                                "~8–10k атрибуций на раздел (без скопа и одиночек)")
    hc = Counter(p["h"] for p in points if p["h"] >= 0)
    facets["hardlayers"] = {
        "label": f"Hard layers · {len(hard_cats)}",
        "cats": [{"name": c["name"], "color": c["color"], "n": hc.get(i, 0)}
                 for i, c in enumerate(hard_cats)],
        "note": "рекурсивный geo-peel с поправкой на покрытие — жёсткие страты-листья (мокап 45)",
    }
    facets["area"]["note"] = "12 макроареалов, детерминированно из areal_path (мокап 21)"
    facets["family"]["note"] = "~11 языковых/религиозных семей из языковой цепочки (мокап 21)"
    facets["narrative"]["note"] = ("кластер традиции по нарративному профилю — KMeans k=8 "
                                   "над 16-мерным профилем (мокапы 41/43)")
    facets["subsistence"]["note"] = f"ближайшее общество D-PLACE в пределах {MATCH_KM:.0f} км (мокап 22)"

    # Regions layer — the catalogue's own curated traditions (research/regions.md), its own point set
    # (not the Berezkin index), coloured by the CARTOColors Prism region palette.
    region_pts = [{"x": float(lon), "y": float(lat), "r": ri, "t": tname}
                  for ri, (_, _, trads) in enumerate(REGIONS) for tname, lat, lon in trads]
    rgroups = defaultdict(list)
    for i, p in enumerate(region_pts):
        rgroups[(round(p["x"]), round(p["y"]))].append(i)
    for members in rgroups.values():
        if len(members) > 1:
            span = 1.5 * math.sqrt(len(members))
            for j, i in enumerate(members):
                ox, oy = _sunflower(j, len(members))
                region_pts[i]["x"] = round(region_pts[i]["x"] + ox * span, 2)
                region_pts[i]["y"] = round(region_pts[i]["y"] + oy * span, 2)
    rcounts = Counter(p["r"] for p in region_pts)
    facets["regions"] = {
        "label": f"Regions dots · {len(REGIONS)}",
        "kind": "regions",
        "cats": [{"name": rname, "color": rcolor, "n": rcounts.get(ri, 0)}
                 for ri, (rname, rcolor, _) in enumerate(REGIONS)],
        "points": region_pts,
        "note": "курированные традиции канона (research/regions.md), не индекс Березкина; палитра CARTO Prism",
    }

    # Territory layer — the full tradition list, region areas washed in their colour, tradition
    # points a single neutral tone.
    terr_pts = [{"x": float(lon), "y": float(lat), "r": ri, "t": tname}
                for ri, (_, _, trads) in enumerate(REGIONS) for tname, lat, lon in trads]
    tgroups = defaultdict(list)
    for i, p in enumerate(terr_pts):
        tgroups[(round(p["x"]), round(p["y"]))].append(i)
    for members in tgroups.values():
        if len(members) > 1:
            span = 2.0 * math.sqrt(len(members))
            for j, i in enumerate(members):
                ox, oy = _sunflower(j, len(members))
                terr_pts[i]["x"] = round(terr_pts[i]["x"] + ox * span, 2)
                terr_pts[i]["y"] = round(terr_pts[i]["y"] + oy * span, 2)
    tcounts = Counter(p["r"] for p in terr_pts)
    facets["territory"] = {
        "label": f"Regions fill · {len(terr_pts)}",
        "kind": "territory",
        "cats": [{"name": rname, "color": rcolor, "n": tcounts.get(ri, 0)}
                 for ri, (rname, rcolor, _) in enumerate(REGIONS)],
        "points": terr_pts,
        "note": "полный список традиций; заливка — ареал региона, точки нейтральны",
    }

    # Borders layer — region areas as filled polygons (nearest-region partition), no points
    facets["borders"] = {
        "label": "Regions",
        "kind": "borders",
        "cats": region_borders(REGIONS),
        "points": region_pts,
        "antarctica": json.loads(
            (Path(__file__).resolve().parent / "regions_geo.json").read_text()).get("Antarctica", ""),
        "note": "ареалы регионов на реальных границах (Natural Earth: страны + провинции крупных стран, "
                "раздел по ближайшей традиции); полупрозрачная заливка + точки курируемых традиций; "
                "Антарктида — нейтральная суша",
    }

    # Religions layer — predominant religion per country (the modern scriptural overlay stratum,
    # not the deep indigenous layer the areas map colours)
    facets["religions"] = {
        "label": f"Religions · {len(RELIGIONS)}",
        "kind": "borders",
        "cats": religion_borders(),
        "note": "предоминантная религия по странам (плюрализм) — современная письменная надстройка, "
                "а не коренной пласт, который красит карта areas",
    }

    # Substrate layer — how strongly the pre-scriptural indigenous/folk layer survives as living
    # practice beneath the nominal religion (the mirror of `religions`); illustrative estimate
    facets["substrate"] = {
        "label": f"Substrate · {len(SUBSTRATE)}",
        "kind": "borders",
        "cats": substrate_borders(),
        "note": "сила субстрата — насколько доскриптурный коренной/народный пласт выживает как живая "
                "практика под номинальной религией (экспертная оценка, не перепись); зеркало religions",
    }

    # Language facets (illustrative groupings, build_lang_geo.py)
    facets["families"] = {
        "label": f"Families · {len(FAMILIES)}",
        "kind": "borders",
        "cats": _geo_cats("families_geo.json", FAMILIES),
        "note": "предоминантная (коренная) языковая семья по странам; шаттер-зоны свёрнуты ареально "
                "(Papuan, Australian), Америки — по 4 культур-ареальным макрогруппам, юг Индии — Dravidian",
    }
    facets["langdiv"] = {
        "label": f"Lang diversity · {len(LANGDIV)}",
        "kind": "borders",
        "cats": _geo_cats("langdiv_geo.json", LANGDIV),
        "note": "языковое разнообразие / фрагментация (много языков на ареал) — тёмное в шаттер-зонах "
                "(Н. Гвинея, Амазония, В. Африка, Кавказ), бледное в спред-зонах",
    }
    facets["zones"] = {
        "label": f"Zones · {len(ZONES)}",
        "kind": "borders",
        "cats": _geo_cats("zones_geo.json", ZONES),
        "note": "спред↔остаточные зоны (Николс) 5-ступенчатой шкалой: тёмное = сильная спред-зона "
                "(одна семья разлилась — степь, Сахель, банту), светлое = аккреционная зона со старым "
                "разнообразием (Н. Гвинея, Амазония)",
    }

    data = {"facets": facets,
            "order": ["regions", "borders", "territory", "religions", "substrate", "families",
                      "langdiv", "zones", "hardlayers", "volume", "area", "family", "narrative",
                      "subsistence", "diversity", "depth", "cosmology", "peopling"],
            "points": points, "n": len(points), "min_motifs": MIN_MOTIFS}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    n_narr = sum(1 for p in points if p["n"] >= 0)
    print(f"{len(points)} placed · {n_narr} narrative-clustered · {len(tid_beta)} β-diversity "
          f"· {len(tid_depth)} depth · {len(tid_cosmo)} cosmology-share · {len(tid_peo)} peopling")


if __name__ == "__main__":
    main()
