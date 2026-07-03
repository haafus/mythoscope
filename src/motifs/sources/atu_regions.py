"""People/region dictionary for ATU "Attestations by tradition" (Uther's
``provenance`` apparatus).

Each type's attestations are prose of the form ``People: citation; People, People:
citation; …`` — a people (nationality / ethnonym) before each colon, sometimes a
comma-list sharing one citation. This module

  * parses that prose into ``(people, citation)`` entries,
  * canonicalises the people label (folding spelling variants), and
  * maps it to a broad macro-region.

The region names match the TMI/Berezkin taxonomy (``culture_dict._REGION`` and
``docs``), with one addition — **Central Asia** — because ATU carries a real
mass of Turkic/Iranian Central-Asian peoples (Uzbek, Tadzhik, Kazakh, …) that
neither of the other two indexes distinguishes. This map is ATU-specific and
separate from ``culture_dict`` so TMI's established figures stay untouched.

The ~260 distinct labels here cover ~99% of all attestation mentions; anything
unmapped keeps region "" and lands in the "—" bucket.
"""

from __future__ import annotations

import re
from collections import Counter

# Spelling variants / demonyms -> canonical people label. Only unambiguous folds.
_ALIAS = {
    "France": "French", "Greece": "Greek", "England": "English",
    "Englisch": "English", "Iclandic": "Icelandic", "Faroese": "Faeroese",
    "Faroesian": "Faeroese", "Morocan": "Moroccan", "Algrian": "Algerian",
    "ALgerian": "Algerian", "Bylorussian": "Byelorussian",
    "Ukraininan": "Ukrainian", "Plestinian": "Palestinian",
    "Tadzik": "Tadzhik", "Tadzhikian": "Tadzhik", "Tadzihikian": "Tadzhik",
    "Corsian": "Corsican", "Rumanaian": "Rumanian", "Austrain": "Austrian",
    "Burjat": "Buryat", "Mongol": "Mongolian", "Ostjakian": "Ostyak",
    "Chemis/Mari": "Cheremis/Mari", "Mordvin": "Mordvinian",
    "Cap Verdian": "Cape Verdian", "Guatamalan": "Guatemalan",
    "Wallonian": "Walloon", "Puerto-Rican": "Puerto Rican",
    "Spanish-America": "Spanish-American", "African-American": "African American",
    "French American": "French-American", "French-Amercian": "French-American",
    "English-Canada": "English-Canadian", "English-American": "English-Canadian",
    "North American indian": "North American Indian", "Kazak": "Kazakh",
    "Kazakhian": "Kazakh", "Yakutian": "Yakut", "Tuvan": "Tuva",
    "Zimbabwen": "Zimbabwe", "Rhodesian": "Zimbabwe", "Botswanian": "Botswana",
    "Kurdisch": "Kurdish", "Saudi Aranian": "Saudi Arabian",
    "Indonesia": "Indonesian", "Ghanaese": "Ghanaian", "Ossetic": "Ossetian",
    "Mingril": "Mingrelian",
    # Bare "Indian" is India in Uther (Native Americans are N./S. American Indian).
    "Indian": "India", "Filipino": "Philippine", "French Canadian": "French-Canadian",
    "Chile": "Chilean",
}

# Canonical people -> broad macro-region. Absent labels keep region "".
_REGION = {
    # --- Europe ---
    "German": "Europe", "Latvian": "Europe", "Finnish": "Europe",
    "Hungarian": "Europe", "Lithuanian": "Europe", "Spanish": "Europe",
    "Greek": "Europe", "Ukrainian": "Europe", "Bulgarian": "Europe",
    "Italian": "Europe", "Frisian": "Europe", "Russian": "Europe",
    "Estonian": "Europe", "Polish": "Europe", "French": "Europe",
    "Irish": "Europe", "Portuguese": "Europe", "Danish": "Europe",
    "Swedish": "Europe", "Rumanian": "Europe", "Byelorussian": "Europe",
    "Dutch": "Europe", "Catalan": "Europe", "Flemish": "Europe",
    "Czech": "Europe", "Slovakian": "Europe", "Norwegian": "Europe",
    "English": "Europe", "Serbian": "Europe", "Finnish-Swedish": "Europe",
    "Slovene": "Europe", "Austrian": "Europe", "Croatian": "Europe",
    "Lappish": "Europe", "Livonian": "Europe", "Karelian": "Europe",
    "Macedonian": "Europe", "Swiss": "Europe", "Maltese": "Europe",
    "Icelandic": "Europe", "Scottish": "Europe", "Wepsian": "Europe",
    "Sardinian": "Europe", "Walloon": "Europe", "Ladinian": "Europe",
    "Faeroese": "Europe", "Sorbian": "Europe", "Syrjanian": "Europe",
    "Basque": "Europe", "Chuvash": "Europe", "Wotian": "Europe",
    "Corsican": "Europe", "Bosnian": "Europe", "Welsh": "Europe",
    "Mordvinian": "Europe", "Cheremis/Mari": "Europe", "Albanian": "Europe",
    "Votyak": "Europe", "Udmurt": "Europe", "Luxembourg": "Europe",
    "Kashubian": "Europe", "Tatar": "Europe", "Bashkir": "Europe",
    "Gagauz": "Europe",
    # Roma (pan-European here); "Lydian" = the Finnic Ludic people, listed with
    # Wepsian/Karelian — not ancient Lydia.
    "Gypsy": "Europe", "Lydian": "Europe",
    # --- Near East (West Asia, Caucasus, Arab N. Africa) ---
    "Jewish": "Near East", "Egyptian": "Near East", "Turkish": "Near East",
    "Iranian": "Near East", "Persian": "Near East", "Palestinian": "Near East",
    "Iraqi": "Near East", "Syrian": "Near East", "Georgian": "Near East",
    "Armenian": "Near East", "Kurdish": "Near East", "Lebanese": "Near East",
    "Yemenite": "Near East", "Saudi Arabian": "Near East", "Jordanian": "Near East",
    "Qatar": "Near East", "Aramaic": "Near East", "Persian Gulf": "Near East",
    "Oman": "Near East", "Kuwaiti": "Near East", "Druze": "Near East",
    "Azerbaijan": "Near East", "Abkhaz": "Near East", "Ossetian": "Near East",
    "Dagestan": "Near East", "Adygea": "Near East", "Chechen-Ingush": "Near East",
    "Kabardin": "Near East", "Karachay": "Near East", "Avar": "Near East",
    "Mingrelian": "Near East", "Moroccan": "Near East", "Algerian": "Near East",
    "Tunisian": "Near East", "Libyan": "Near East", "North African": "Near East",
    # --- Central Asia (Turkic / Iranian Inner Asia) ---
    "Tadzhik": "Central Asia", "Uzbek": "Central Asia", "Kazakh": "Central Asia",
    "Turkmen": "Central Asia", "Kirghiz": "Central Asia", "Kara-Kalpak": "Central Asia",
    "Uighur": "Central Asia", "Afghan": "Central Asia", "Mongolian": "Central Asia",
    "Kalmyk": "Central Asia",
    # --- South Asia ---
    "India": "South Asia", "Pakistani": "South Asia", "Sri Lankan": "South Asia",
    "Nepalese": "South Asia",
    # --- East Asia ---
    "Chinese": "East Asia", "Japanese": "East Asia", "Korean": "East Asia",
    "Tibetian": "East Asia",
    # --- Southeast Asia ---
    "Indonesian": "Southeast Asia", "Philippine": "Southeast Asia",
    "Burmese": "Southeast Asia", "Cambodian": "Southeast Asia",
    "Vietnamese": "Southeast Asia", "Thai": "Southeast Asia",
    "Laotian": "Southeast Asia", "Malaysian": "Southeast Asia",
    # --- Siberia ---
    "Siberian": "Siberia", "Yakut": "Siberia", "Buryat": "Siberia",
    "Tuva": "Siberia", "Vogul/Mansi": "Siberia", "Ostyak": "Siberia",
    "Nenets": "Siberia", "Tungus": "Siberia", "Altaic": "Siberia",
    # --- Africa (Sub-Saharan + islands) ---
    "South African": "Africa", "East African": "Africa", "Central African": "Africa",
    "Namibian": "Africa", "Ethiopian": "Africa", "Congolese": "Africa",
    "Somalian": "Africa", "Tanzanian": "Africa", "Guinean": "Africa",
    "Nigerian": "Africa", "Cameroon": "Africa", "Ghanaian": "Africa",
    "West African": "Africa", "Eritrean": "Africa", "Chadian": "Africa",
    "Chad": "Africa", "Niger": "Africa", "Angolan": "Africa", "Kenyan": "Africa",
    "Benin": "Africa", "Sierra Leone": "Africa", "Togolese": "Africa",
    "Liberian": "Africa", "Guinea Bissau": "Africa", "Zimbabwe": "Africa",
    "Botswana": "Africa", "Mali": "Africa", "Malagasy": "Africa",
    "Swahili": "Africa", "Cape Verdian": "Africa", "Central African Republic": "Africa",
    "Burkina Faso": "Africa", "Ivory Coast": "Africa", "Zanzanian": "Africa",
    "Mauritian": "Africa", "Sudanese": "Africa", "Guinea": "Africa",
    "Namibian/South African": "Africa",
    # --- North America ---
    "US-American": "North America", "African American": "North America",
    "English-Canadian": "North America", "French-Canadian": "North America",
    "French-American": "North America", "Eskimo": "North America",
    "North American Indian": "North America", "Canada": "North America",
    # --- Mesoamerica & Central America ---
    "Mexican": "Mesoamerica", "Mayan": "Mesoamerica", "Guatemalan": "Mesoamerica",
    "Costa Rican": "Mesoamerica", "Nicaraguan": "Mesoamerica",
    "Panamanian": "Mesoamerica", "Honduran": "Mesoamerica", "Salvadoran": "Mesoamerica",
    # --- South America ---
    "Brazilian": "South America", "Chilean": "South America", "Argentine": "South America",
    "Colombian": "South America", "Peruvian": "South America", "Ecuadorian": "South America",
    "Venezuelan": "South America", "Bolivian": "South America", "Uruguayan": "South America",
    "Paraguayan": "South America", "Guianese": "South America",
    "South American Indian": "South America", "Spanish-American": "South America",
    # --- Caribbean ---
    "West Indies": "Caribbean", "West-Indian": "Caribbean", "Cuban": "Caribbean",
    "Dominican": "Caribbean", "Puerto Rican": "Caribbean",
    # --- Oceania ---
    "Australian": "Oceania", "Polynesian": "Oceania", "Hawaiian": "Oceania",
    "New Zealand": "Oceania", "Micronesian": "Oceania", "Papuan": "Oceania",
}

# Broad-to-fine display order for the region breakdown (Old World W→E, then New).
REGION_ORDER = [
    "Europe", "Near East", "Central Asia", "South Asia", "East Asia",
    "Southeast Asia", "Siberia", "Africa", "North America", "Mesoamerica",
    "South America", "Caribbean", "Oceania",
]

_LEAD_CF = re.compile(r"(?i)^cf\.\s+")


def canonical(label: str) -> str:
    """Canonical people label for a raw attestation head, or "" if it is not a
    people (blank, or a citation fragment carrying a digit)."""
    name = _LEAD_CF.sub("", label.strip().lstrip(".").strip()).strip()
    if not name or any(ch.isdigit() for ch in name):
        return ""
    return _ALIAS.get(name, name)


def region(canon: str) -> str:
    """Macro-region for a canonical people label, or "" if unmapped."""
    return _REGION.get(canon, "")


def parse(text: str) -> list[dict]:
    """Parse the ``provenance`` prose into ``[{people, canon, region, cite}]``.

    Splits on ``;`` into ``head: citation`` groups; a head may be a comma-list of
    peoples sharing the citation, each emitted as its own entry. Segments with no
    colon are continuations of the previous citation (a citation that itself held
    a ``;``), so they are appended to it.
    """
    entries: list[dict] = []
    for seg in text.split(";"):
        if ":" not in seg:
            if entries and seg.strip():  # citation spilled across a ';'
                entries[-1]["cite"] = f"{entries[-1]['cite']};{seg.strip()}".strip()
            continue
        head, cite = seg.split(":", 1)
        cite = cite.strip()
        for raw in head.split(","):
            people = raw.strip()
            canon = canonical(people)
            if not canon:
                continue
            entries.append({"people": canon, "canon": canon, "region": region(canon), "cite": cite})
    return entries


def group_by_region(entries: list[dict]) -> dict:
    """Group parsed entries into ``{total, regions: [{region, count, entries}]}``,
    regions ordered by count (the unmapped "—" bucket always last)."""
    buckets: dict[str, list[dict]] = {}
    for e in entries:
        buckets.setdefault(e["region"] or "—", []).append({"people": e["people"], "cite": e["cite"]})
    rows = [{"region": reg, "count": len(items), "entries": items} for reg, items in buckets.items()]
    rows.sort(key=lambda r: (r["region"] == "—", -r["count"], r["region"]))
    return {"total": len(entries), "regions": rows}


def build_legend(types: list[dict]) -> dict:
    """Aggregate parsed attestations across all types into the ATU culture
    dictionary: canonical people -> ``{count, region}`` (count = number of types
    attesting that people). Mirrors ``culture_dict.build_legend``."""
    counts: Counter = Counter()
    region_of: dict[str, str] = {}
    for t in types:
        seen: set[str] = set()
        for grp in (t.get("attestations_grouped") or {}).get("regions", []):
            for e in grp["entries"]:
                canon = e["people"]
                region_of[canon] = grp["region"] if grp["region"] != "—" else ""
                if canon not in seen:
                    counts[canon] += 1
                    seen.add(canon)
    return {canon: {"count": n, "region": region_of.get(canon, "")}
            for canon, n in counts.most_common()}
