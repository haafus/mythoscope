"""Deterministic facet population (mockup 21) — does the recipe in macro-area-facets.md
actually cover the whole corpus?

Runs the three *deterministic* facet functions over all 1046 traditions and 3488 motifs
and reports coverage + distribution:

- area(areal_path)  — 12 macro-areas, pure function of areal_path[0] with a few
  areal_path[1] reassignments. Should be 100% coverage.
- theme(motif_group_num) — Berezkin category A/B → 13 groups. 100% by construction.
- family(language[0]) — the *linguistic seed* of the ~11 culture families. This is the
  honest part: the seed covers most rows, but the religion overlay (Abrahamic / Islamicate
  / Indic-Dharmic / Sinic) needs curation not present in berezkin.json, so we mark each
  assignment as `seed` (direct from language) or `area-fallback` (ambiguous family
  resolved by area — Afroasiatic, Caucasian, isolates), and flag the overlay-approximate
  ones. The point is to surface exactly where curation is still required.

Run:  python mockups/21-facet-population/build_data.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"

# --- area: 12 macro-areas from areal_path[0], with [1] moves for 4 split macros ---
AREA = {
    "NORTHERN AND EASTERN EUROPE": "Europe",
    "EAST ASIA": "East & SE Asia",
    "OCEANIA": "Austronesia & Oceania", "MADAGASCAR": "Austronesia & Oceania",
    "SIBERIA – MONGOLIA": "Siberia & Beringia", "BERINGIA": "Siberia & Beringia",
    "PLAINS AND SOUTHEAST": "Eastern North America",
    "MEXICO – CENTRAL ANDES": "Mesoamerica & Andes",
    "EASTERN SOUTH AMERICA": "South America", "SOUTHERN SOUTH AMERICA": "South America",
    "SUB-SAHARAN AFRICA": "Sub-Saharan Africa", "AUSTRALIA": "Aboriginal Australia",
}
SPLIT = {
    "WESTERN EUROPE, NORTH AFRICA": {
        "ANCIENT GREECE AND ROME": "Europe", "BALKAN-CARPATHIANS": "Europe",
        "SOUTHERN AND WESTERN EUROPE": "Europe",
        "HORN OF AFRICA": "Near East & N. Africa", "NORTH AFRICA": "Near East & N. Africa"},
    "SOUTHWEST AND CENTRAL ASIA, ARYAN INDIA": {
        "NEAR EAST": "Near East & N. Africa", "NORTH CAUCASUS – ASIA MINOR": "Near East & N. Africa",
        "SOUTH CAUCASUS – ASIA MINOR": "Near East & N. Africa",
        "IRAN – CENTRAL ASIA": "Iran, C. & S. Asia", "TURKESTAN": "Iran, C. & S. Asia",
        "ARYAN AND SOUTH INDIA": "Iran, C. & S. Asia"},
    "TIBET, NON-ARYAN SOUTH ASIA, SOUTHEAST ASIA": {
        "SOUTH ASIA": "Iran, C. & S. Asia",
        "TIBET, NORTHEAST INDIA": "East & SE Asia", "BURMA, INDOCHINA": "East & SE Asia",
        "NUSANTARA": "Austronesia & Oceania"},
    "NORTH AMERICA: NORTH AND WEST": {
        "MIDWEST": "Eastern North America", "THE NORTHEAST": "Eastern North America"},
}
NW_NA = "Northern & Western N. America"
AREAS12 = ["Europe", "Near East & N. Africa", "Iran, C. & S. Asia", "East & SE Asia",
           "Austronesia & Oceania", "Siberia & Beringia", NW_NA, "Eastern North America",
           "Mesoamerica & Andes", "South America", "Sub-Saharan Africa", "Aboriginal Australia"]


def area_of(ap):
    if not ap:
        return None
    m0 = ap[0][1].upper()
    if m0 in SPLIT:
        sub = ap[1][1].upper() if len(ap) > 1 else ""
        if m0 == "NORTH AMERICA: NORTH AND WEST":
            return SPLIT[m0].get(sub, NW_NA)
        return SPLIT[m0].get(sub)
    return AREA.get(m0)


# --- family: linguistic seed → 11 buckets; ambiguous ones resolved by area ---
FAM_SEED = {
    "indoeuropean": "Indo-European",
    "altaic": "Uralic & Altaic", "uralic": "Uralic & Altaic",
    "sino-tibetan": "Sinic",
    "escoaleut": "Circumpolar & Palaeo-Asiatic", "paleoasiatic": "Circumpolar & Palaeo-Asiatic",
    "yukaghir": "Circumpolar & Palaeo-Asiatic", "yeniseian": "Circumpolar & Palaeo-Asiatic",
    "niger-kongo": "Sub-Saharan", "nilo-saharan": "Sub-Saharan", "khoisan": "Sub-Saharan",
    "austronesian": "Austronesian & Papuan", "austroasiatic": "Austronesian & Papuan",
    "papuan": "Austronesian & Papuan", "tai-kadai": "Austronesian & Papuan",
    "trans new guinea": "Austronesian & Papuan", "sepik-ramu": "Austronesian & Papuan",
    "torricelli": "Austronesian & Papuan", "north assam": "Austronesian & Papuan",
    "kuki-chin-naga": "Austronesian & Papuan", "konyak-bodo-garo": "Austronesian & Papuan",
    "dravidian": "Indic / Dharmic",
    "australian": "Australian",
}
# Amerindian: any American family (resolved by area if not explicitly listed)
AMERIND = {"na-dene", "uto-aztecan", "algic", "tupian", "carib", "macro ge", "macro-ge",
           "salishan", "penuti", "arawak", "arawakan", "sioux-katawba", "hokan", "mayan",
           "chibchan", "pano-tacana", "iroquois", "oto-mangean", "muskogean", "caddoan",
           "matacoan", "tucano", "kechua", "quechua", "guaikuru", "guajibo", "mixe-zoquean",
           "zamuco", "witoto", "barbacoan", "tunican", "keresan", "kiowa-tanoan", "wakashan",
           "macu-puinave", "salivan", "yanomamo", "yukian", "kunza", "uru-chipaya", "chinchan",
           "araua", "catukinan", "candoshi", "chimakum", "mascoyan", "chon", "lule-villelan",
           "zaparoan", "jivaroan-cahuapanan", "chapacura"}
AMER_AREAS = {NW_NA, "Eastern North America", "Mesoamerica & Andes", "South America"}
FAMILIES11 = ["Indo-European", "Abrahamic", "Indic / Dharmic", "Sinic", "Islamicate",
              "Uralic & Altaic", "Circumpolar & Palaeo-Asiatic", "Amerindian", "Sub-Saharan",
              "Austronesian & Papuan", "Australian"]


def _canon(s):
    s = (s or "").lower().split("(")[0].split(",")[0].strip()
    return s.rstrip("+?").strip()


def family_of(lang0, area):
    key = _canon(lang0)
    if key in FAM_SEED:
        return FAM_SEED[key], "seed"
    if key in AMERIND or (area in AMER_AREAS and key in ("isolate", "different", "unknown", "")):
        return "Amerindian", "seed" if key in AMERIND else "area-fallback"
    # ambiguous linguistic families resolved by area
    if key in ("afrasian", "afroasiatic"):
        return ("Sub-Saharan", "area-fallback") if area == "Sub-Saharan Africa" \
            else ("Abrahamic", "area-fallback")
    if key in ("north caucasian", "kartwelian", "kartvelian"):
        return "Islamicate", "area-fallback"
    if key == "spanish" or "spanish" in _canon(lang0):
        return "Indo-European", "area-fallback"
    if area in AMER_AREAS:
        return "Amerindian", "area-fallback"
    if area == "Sub-Saharan Africa":
        return "Sub-Saharan", "area-fallback"
    return None, "unresolved"


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T, Ms = bz["traditions"], bz["motifs"]

    area_c, fam_c, method_c = Counter(), Counter(), Counter()
    no_area, no_fam, samples = 0, 0, []
    for tid, v in T.items():
        a = area_of(v.get("areal_path") or [])
        lang0 = (v.get("language") or [None])[0]
        fam, method = family_of(lang0, a)
        area_c[a] += 1; fam_c[fam] += 1; method_c[method] += 1
        if a is None:
            no_area += 1
        if fam is None:
            no_fam += 1
        if len(samples) < 16 and a and fam:
            samples.append({"n": v.get("name", tid), "ru": v.get("name_rus", ""),
                            "area": a, "fam": fam, "lang": lang0 or "—", "m": method})

    # theme over motifs
    GROUP = {1: "Sun & Moon", 2: "Stars & constellations", 3: "Cosmogony & elements",
             4: "Origin of death", 5: "Origin of humans", 6: "Origin of subsistence",
             7: "Plants & animals", 8: "Monstrous beings", 9: "Protagonist identity",
             10: "Adventures", 11: "Tricks & competitions", 12: "Proper names", 13: "Formulae"}
    theme_c, cat_c, no_theme = Counter(), Counter(), 0
    for r in Ms:
        g = int(r.get("motif_group_num") or 0)
        if g in GROUP:
            theme_c[g] += 1
            cat_c["A" if g <= 9 else "B"] += 1
        else:
            no_theme += 1

    data = {
        "n_trad": len(T), "n_motif": len(Ms),
        "area": {"order": AREAS12, "counts": {a: area_c.get(a, 0) for a in AREAS12},
                 "uncovered": no_area},
        "family": {"order": FAMILIES11, "counts": {a: fam_c.get(a, 0) for a in FAMILIES11},
                   "method": dict(method_c), "unresolved": fam_c.get(None, 0)},
        "theme": {"groups": [{"g": g, "name": GROUP[g], "cat": "A" if g <= 9 else "B",
                              "n": theme_c.get(g, 0)} for g in range(1, 14)],
                  "cat": dict(cat_c), "uncovered": no_theme},
        "samples": samples,
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"traditions {len(T)} · motifs {len(Ms)}")
    print(f"  area: {dict(area_c)}  (uncovered {no_area})")
    print(f"  family method: {dict(method_c)}  (unresolved {fam_c.get(None,0)})")
    print(f"  theme cat: {dict(cat_c)}  (uncovered {no_theme})")


if __name__ == "__main__":
    main()
