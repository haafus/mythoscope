"""Precompute language-community polygons for mockup 62's three language facets.

Three legible reductions of the ~140-family / ~7000-language mess (see the strata idea
in research/regions.md), all illustrative expert groupings, not a database:

  families  — predominant (indigenous) language family per country; shatter zones bundled
              areally (Papuan, Australian, Indigenous Americas); south India split off as
              Dravidian. ~16 categories.
  langdiv   — 5-class linguistic-diversity / fragmentation (many languages per area).
  zones     — Nichols' spread zones (one family expanded) vs residual / accretion zones.

    python mockups/62-facet-map/build_lang_geo.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_region_geo as G  # noqa: E402

FAMILY = {
    "Indo-European": [
        "Portugal", "Spain", "France", "Ireland", "United Kingdom", "Belgium", "Netherlands",
        "Luxembourg", "Germany", "Denmark", "Norway", "Sweden", "Iceland", "Switzerland", "Austria",
        "Italy", "Poland", "Czechia", "Slovakia", "Slovenia", "Croatia", "Bosnia and Herzegovina",
        "Republic of Serbia", "Montenegro", "North Macedonia", "Bulgaria", "Romania", "Moldova",
        "Ukraine", "Belarus", "Russia", "Lithuania", "Latvia", "Greece", "Albania", "Kosovo",
        "Cyprus", "Armenia", "Iran", "Afghanistan", "Pakistan", "Bangladesh", "Nepal", "Sri Lanka",
        "Maldives", "Tajikistan"],
    "Uralic": ["Finland", "Estonia", "Hungary"],
    "Turkic": ["Turkey", "Azerbaijan", "Kazakhstan", "Uzbekistan", "Turkmenistan", "Kyrgyzstan"],
    "Mongolic": ["Mongolia"],
    "Sino-Tibetan": ["China", "Myanmar", "Bhutan"],
    "Japonic & Koreanic": ["Japan", "South Korea", "North Korea"],
    "Austroasiatic": ["Vietnam", "Cambodia"],
    "Tai-Kadai": ["Thailand", "Laos"],
    "Austronesian": [
        "Indonesia", "Malaysia", "Philippines", "Brunei", "East Timor", "Singapore", "Madagascar",
        "Taiwan", "Fiji", "Solomon Islands", "Vanuatu", "Samoa", "Tonga", "Kiribati", "Tuvalu",
        "Nauru", "Federated States of Micronesia", "Marshall Islands", "Palau", "New Caledonia",
        "French Polynesia", "Comoros"],
    "Papuan (New Guinea)": ["Papua New Guinea"],
    "Australian (Aboriginal)": ["Australia"],
    "Afroasiatic": [
        "Morocco", "Algeria", "Tunisia", "Libya", "Egypt", "Mauritania", "Western Sahara", "Sudan",
        "Somalia", "Somaliland", "Djibouti", "Eritrea", "Ethiopia", "Israel", "Palestine",
        "Saudi Arabia", "Yemen", "Jordan", "Syria", "Lebanon", "Iraq", "Kuwait", "Qatar",
        "United Arab Emirates", "Oman", "Bahrain", "Malta", "Niger"],
    "Nilo-Saharan": ["South Sudan", "Chad"],
    "Niger-Congo": [
        "Senegal", "Gambia", "Guinea", "Guinea-Bissau", "Sierra Leone", "Liberia", "Ivory Coast",
        "Ghana", "Togo", "Benin", "Nigeria", "Cameroon", "Central African Republic", "Gabon",
        "Republic of the Congo", "Democratic Republic of the Congo", "Angola", "Zambia", "Zimbabwe",
        "Malawi", "Mozambique", "Kenya", "Uganda", "Rwanda", "Burundi", "United Republic of Tanzania",
        "South Africa", "Namibia", "Botswana", "Lesotho", "eSwatini", "Burkina Faso", "Mali",
        "Equatorial Guinea"],
    "Indigenous Americas": [
        "Canada", "United States of America", "Greenland", "Mexico", "Guatemala", "Belize",
        "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama", "Colombia", "Venezuela",
        "Guyana", "Suriname", "Ecuador", "Peru", "Bolivia", "Paraguay", "Chile", "Argentina",
        "Uruguay", "Brazil", "Cuba", "Haiti", "Dominican Republic"],
}
of_family = {c: fam for fam, cs in FAMILY.items() for c in cs}
INDIA_DRAVIDIAN = {"Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh", "Telangana", "Puducherry"}

DIV = {
    "Very high": ["Papua New Guinea", "Indonesia", "Nigeria", "India", "China", "Mexico", "Cameroon",
                  "Australia", "Democratic Republic of the Congo", "Chad", "United Republic of Tanzania",
                  "Vanuatu", "Nepal", "Philippines", "Sudan", "Myanmar", "Brazil"],
    "High": ["Vietnam", "Laos", "Malaysia", "Ethiopia", "Kenya", "South Sudan", "Ghana", "Ivory Coast",
             "Benin", "Colombia", "Peru", "Bolivia", "Ecuador", "Venezuela", "Angola", "Mozambique",
             "Russia", "Solomon Islands", "Central African Republic", "Guinea", "Iran", "Pakistan",
             "Afghanistan", "Thailand", "Uganda"],
    "Low": ["France", "Germany", "Spain", "Italy", "United Kingdom", "Poland", "Ukraine", "Argentina",
            "Chile", "Japan", "Morocco", "Algeria", "Egypt", "Saudi Arabia", "Kazakhstan",
            "Uzbekistan", "Netherlands", "Sweden", "Norway", "Romania", "Turkey"],
    "Very low": ["Iceland", "Ireland", "Portugal", "Hungary", "Finland", "North Korea", "South Korea",
                 "Cuba", "Haiti", "Dominican Republic", "Rwanda", "Burundi", "Somalia", "eSwatini",
                 "Lesotho", "Uruguay", "Yemen", "Qatar", "Bahrain", "Denmark", "Armenia"],
}
of_div = {c: lvl for lvl, cs in DIV.items() for c in cs}

ZONE = {
    "Residual / accretion zone": [
        "Papua New Guinea", "Vanuatu", "Solomon Islands", "Nepal", "Bhutan", "Myanmar", "Mexico",
        "Guatemala", "Colombia", "Ecuador", "Peru", "Bolivia", "Venezuela", "Brazil", "Guyana",
        "Suriname", "Nigeria", "Cameroon", "Ghana", "Ivory Coast", "Benin", "Togo", "Guinea",
        "Guinea-Bissau", "Sierra Leone", "Liberia", "Ethiopia", "South Sudan", "Sudan", "Chad",
        "Georgia", "Armenia"],
    "Spread zone": [
        "Portugal", "Spain", "France", "Ireland", "United Kingdom", "Belgium", "Netherlands",
        "Germany", "Denmark", "Norway", "Sweden", "Iceland", "Austria", "Poland", "Czechia",
        "Slovakia", "Bulgaria", "Romania", "Ukraine", "Belarus", "Russia", "Lithuania", "Latvia",
        "Greece", "Finland", "Estonia", "Hungary", "Turkey", "Kazakhstan", "Uzbekistan",
        "Turkmenistan", "Kyrgyzstan", "Mongolia", "Morocco", "Algeria", "Tunisia", "Libya", "Egypt",
        "Saudi Arabia", "Yemen", "Jordan", "Syria", "Iraq", "Iran", "Afghanistan", "Pakistan",
        "Bangladesh", "Thailand", "Laos", "Vietnam", "Cambodia", "Angola", "Zambia", "Zimbabwe",
        "Botswana", "Namibia", "South Africa", "Mozambique", "Madagascar", "Argentina", "Chile",
        "Uruguay", "Somalia"],
}
of_zone = {c: z for z, cs in ZONE.items() for c in cs}


def build():
    fam, div, zone = defaultdict(list), defaultdict(list), defaultdict(list)
    for f in G.fetch("admin0")["features"]:
        admin = f["properties"].get("ADMIN")
        if admin == "Antarctica":
            continue
        for poly in G.parts_of(f["geometry"]):
            _, lat = G.centroid(poly)
            if lat < -60:
                continue
            d = G.path_d(poly)
            div[of_div.get(admin, "Moderate")].append(d)
            zone[of_zone.get(admin, "Intermediate")].append(d)
            if admin != "India" and admin in of_family:
                fam[of_family[admin]].append(d)
    for f in G.fetch("admin1")["features"]:
        if f["properties"].get("admin") != "India":
            continue
        prov = f["properties"].get("name")
        key = "Dravidian" if prov in INDIA_DRAVIDIAN else "Indo-European"
        for poly in G.parts_of(f["geometry"]):
            fam[key].append(G.path_d(poly))
    for name, d in (("families_geo.json", fam), ("langdiv_geo.json", div), ("zones_geo.json", zone)):
        (HERE / name).write_text(json.dumps({k: "".join(v) for k, v in d.items()}, ensure_ascii=False))
    print("families:", len(fam), "| langdiv:", len(div), "| zones:", len(zone))


if __name__ == "__main__":
    build()
