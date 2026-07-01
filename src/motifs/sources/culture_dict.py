"""Dictionary for the culture/region labels that tag citations in TMI notes.

Two layers:
  * inventory  — every distinct label with the number of motifs it tags, built
                 automatically from the parsed ``cultures`` field;
  * normalized — obvious variants merged to a canonical name and tagged with a
                 broad region. Curated for the common labels (the ~150 here
                 cover ~96% of all uses); the long tail stays region "".

``build_legend`` produces the stored ``culture_legend``: canonical label ->
count, region, merged aliases, and any parenthetical sub-areas seen.
"""

from __future__ import annotations

import re
from collections import Counter

# Variant label -> canonical. Only unambiguous synonyms/abbreviations.
_ALIAS = {
    "Icel.": "Icelandic", "England": "English", "Ireland": "Irish",
    "Scotland": "Scottish", "Scotch": "Scottish", "Wales": "Welsh",
    "Esthonian": "Estonian", "Easter Is.": "Easter Island",
    "Am. Negro": "American Negro", "Indonesian": "Indonesia",
    "Melanesian": "Melanesia", "African": "Africa", "Greek myth": "Greek",
    "Filipino": "Philippine",
    # Demonyms / spellings that fold into an already-regioned canonical.
    "China": "Chinese", "Hawaiian": "Hawaii", "Arab": "Arabian",
    "Polynesian": "Polynesia",
    # Case variants (canonical() is case-sensitive) of existing canonicals.
    "Irish Myth": "Irish myth", "Buddhist Myth": "Buddhist myth",
    "Italian novella": "Italian Novella", "English Romance": "English romance",
    "Gold coast": "Gold Coast",
    # "Am. Indian" abbreviation (and its trailing-dot variant) -> American Indian.
    # Handled here rather than by a blanket trailing-"." strip, which would break
    # dotted region keys like "U.S." / "Marshall Is.".
    "Am. Indian": "American Indian", "Am. Indian.": "American Indian",
}

# Canonical label -> broad region. Anything absent keeps region "" but is still
# counted in the inventory.
_REGION = {
    "India": "South Asia", "Hindu": "South Asia", "Buddhist myth": "South Asia",
    "Chinese": "East Asia", "Japanese": "East Asia", "Korean": "East Asia",
    "Indonesia": "Southeast Asia", "Philippine": "Southeast Asia",
    "Siberian": "Siberia", "Koryak": "Siberia",
    "Jewish": "Near East", "Hebrew": "Near East", "Persian": "Near East",
    "Babylonian": "Near East", "Arabian": "Near East", "Egyptian": "Near East",
    "Armenian": "Near East",
    "Irish myth": "Europe", "Irish": "Europe", "Icelandic": "Europe",
    "Greek": "Europe", "Lithuanian": "Europe", "Spanish": "Europe",
    "Spanish Exempla": "Europe", "English": "Europe", "German": "Europe",
    "Breton": "Europe", "French": "Europe", "Italian": "Europe",
    "Italian Novella": "Europe", "Finnish": "Europe", "Danish": "Europe",
    "Russian": "Europe", "Welsh": "Europe", "Scottish": "Europe",
    "Norse": "Europe", "Norwegian": "Europe", "Swedish": "Europe",
    "Dutch": "Europe", "Flemish": "Europe", "Estonian": "Europe",
    "Livonian": "Europe", "Lappish": "Europe", "Slavic": "Europe",
    "Germanic": "Europe", "Roman": "Europe", "Rumanian": "Europe",
    "Prussian": "Europe", "Gascon": "Europe", "Tirol": "Europe",
    "Swiss": "Europe", "English romance": "Europe",
    "Africa": "Africa", "Ekoi": "Africa", "Bushman": "Africa",
    "Hottentot": "Africa", "Congo": "Africa", "Benga": "Africa",
    "Ila": "Africa", "Gold Coast": "Africa",
    "N. Am. Indian": "North America", "Eskimo": "North America",
    "Calif. Indian": "North America", "Tahltan": "North America",
    "Kaska": "North America", "Ojibwa": "North America",
    "Cherokee": "North America", "Pawnee": "North America",
    "Navaho": "North America", "Quileute": "North America",
    "American Indian": "North America", "U.S.": "North America",
    "North Carolina": "North America", "New York": "North America",
    "Missouri French": "North America", "French Canadian": "North America",
    "Canada": "North America", "American Negro": "North America",
    "Aztec": "Mesoamerica", "Maya": "Mesoamerica",
    "S. Am. Indian": "South America", "Argentina": "South America",
    "West Indies": "Caribbean", "Jamaica": "Caribbean", "Bahama": "Caribbean",
    "Cape Verde Islands": "Caribbean",
    "Hawaii": "Oceania", "Maori": "Oceania", "Tonga": "Oceania",
    "Tuamotu": "Oceania", "Marquesas": "Oceania", "Tahiti": "Oceania",
    "Samoa": "Oceania", "Easter Island": "Oceania", "Oceanic": "Oceania",
    "Polynesia": "Oceania", "Melanesia": "Oceania", "Papua": "Oceania",
    "New Guinea": "Oceania", "New Hebrides": "Oceania",
    "Cook Islands": "Oceania", "Marshall Is.": "Oceania", "Fiji": "Oceania",
    "New Zealand": "Oceania", "Australian": "Oceania",
    # Long-tail single cultures, curated from the region-less inventory.
    "Ibo": "Africa", "Madagascar": "Africa", "Zulu": "Africa",
    "Kaffir": "Africa", "Liberian": "Africa", "Mpongwe": "Africa",
    "Angola": "Africa", "Zanzibar": "Africa", "South Africa": "Africa",
    "East Africa": "Africa", "Fjort": "Africa",
    "Mono": "Oceania", "Buin": "Oceania", "New Britain": "Oceania",
    "German New Guinea": "Oceania", "Hivaoa": "Oceania", "Mangaia": "Oceania",
    "Banks Is.": "Oceania", "Society Islands": "Oceania",
    "Zuñi": "North America", "Seneca": "North America", "Pueblo": "North America",
    "Sinkyone": "North America", "Louisiana Creole": "North America",
    "Quiché": "Mesoamerica", "Mixtec": "Mesoamerica",
    "Chile": "South America", "Chibcha": "South America", "Inca": "South America",
    "Haiti": "Caribbean", "Jamaica Negro": "Caribbean", "Carib": "Caribbean",
    "Celtic": "Europe", "Lettish": "Europe", "Austrian": "Europe",
    "Czech": "Europe", "Scandinavian": "Europe", "Hungarian": "Europe",
    "Sicilian": "Europe",
    "Borneo": "Southeast Asia", "Sumatra": "Southeast Asia",
    "Burmese": "Southeast Asia", "Batak": "Southeast Asia",
    "Malay": "Southeast Asia", "Java": "Southeast Asia",
    "Buriat": "Siberia", "Cheremis": "Siberia",
    "Assyrian": "Near East",
}

_SUB_RE = re.compile(r"\s*\(([^)]*)\)")


def canonical(label: str) -> tuple[str, str]:
    """``(canonical macro label, sub-area or "")`` for a raw culture label."""
    sub = _SUB_RE.search(label)
    macro = _SUB_RE.sub("", label).strip()
    macro = re.sub(r"(?i)^cf\.\s+", "", macro).strip()  # drop a leading 'Cf.' compare prefix
    return _ALIAS.get(macro, macro), (sub.group(1).strip() if sub else "")


def build_legend(motifs: list[dict]) -> dict:
    """Aggregate parsed ``cultures`` into the canonical culture dictionary."""
    counts: Counter = Counter()
    aliases: dict[str, set] = {}
    subs: dict[str, set] = {}
    for m in motifs:
        seen: set[str] = set()
        for raw in (m.get("cultures") or {}):
            canon, sub = canonical(raw)
            macro = _SUB_RE.sub("", raw).strip()
            if not canon:
                continue
            if canon not in seen:  # count each culture once per motif
                counts[canon] += 1
                seen.add(canon)
            if macro != canon:
                aliases.setdefault(canon, set()).add(macro)
            if sub:
                subs.setdefault(canon, set()).add(sub)

    legend: dict[str, dict] = {}
    for canon, n in counts.most_common():
        entry = {"count": n, "region": _REGION.get(canon, "")}
        if canon in aliases:
            entry["aliases"] = sorted(aliases[canon])
        if canon in subs:
            entry["subs"] = sorted(subs[canon])
        legend[canon] = entry
    return legend
