"""Precompute the 'substrate strength' polygons for mockup 62's `substrate` facet.

A 5-class choropleth of how strongly the pre-scriptural indigenous / folk religious
layer survives as *living practice* beneath the nominal majority religion — the mirror
of the `religions` (plurality) facet. This is an illustrative expert estimate, not census
data: strong where recent/shallow conversion left the traditional substrate dominant
(Sub-Saharan Africa, Melanesia), weak in the ancient scriptural cores (Near East, Europe).
Output: substrate_geo.json = {level: path d}.

    python mockups/62-facet-map/build_substrate_geo.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_region_geo as G  # noqa: E402

# level (strong -> weak) -> member countries (NE admin-0 ADMIN names)
LEVEL = {
    "Very strong": [
        "Benin", "Togo", "Guinea-Bissau", "South Sudan", "Central African Republic", "Liberia",
        "Sierra Leone", "Guinea", "Ivory Coast", "Ghana", "Burkina Faso", "Cameroon", "Gabon",
        "Republic of the Congo", "Democratic Republic of the Congo", "Angola", "Zambia", "Zimbabwe",
        "Malawi", "Mozambique", "Nigeria", "Uganda", "Burundi", "Rwanda", "Madagascar",
        "Equatorial Guinea", "Papua New Guinea", "Solomon Islands", "Vanuatu", "East Timor"],
    "Strong": [
        "Kenya", "United Republic of Tanzania", "Namibia", "Botswana", "eSwatini", "Lesotho",
        "Senegal", "Gambia", "Chad", "Mali", "South Africa", "Bolivia", "Guatemala", "Peru",
        "Ecuador", "Haiti", "Mongolia", "Bhutan", "Laos", "Nepal", "Indonesia", "Philippines",
        "Malaysia", "Myanmar", "Fiji", "Samoa", "Tonga", "Brunei", "Kiribati", "Tuvalu",
        "Federated States of Micronesia", "Marshall Islands", "Palau", "New Caledonia"],
    "Moderate": [
        "China", "Japan", "South Korea", "North Korea", "Taiwan", "Vietnam", "India", "Sri Lanka",
        "Thailand", "Cambodia", "Brazil", "Colombia", "Venezuela", "Paraguay", "Mexico",
        "Kazakhstan", "Kyrgyzstan", "Uzbekistan", "Turkmenistan", "Tajikistan", "Cuba",
        "Dominican Republic", "Suriname", "Guyana", "Honduras", "Nicaragua", "Niger", "Mauritania",
        "Comoros", "Djibouti", "Singapore", "Hong Kong S.A.R.", "Macao S.A.R", "French Polynesia"],
    "Weak": [
        "Greece", "Italy", "Spain", "Portugal", "Republic of Serbia", "Bulgaria", "Romania",
        "Ukraine", "Belarus", "Russia", "Moldova", "North Macedonia", "Montenegro",
        "Bosnia and Herzegovina", "Albania", "Croatia", "Poland", "Slovakia", "Hungary", "Slovenia",
        "Lithuania", "Latvia", "Estonia", "Czechia", "Georgia", "Armenia", "Ethiopia", "Eritrea",
        "Chile", "Argentina", "Uruguay", "Panama", "Costa Rica", "El Salvador", "Kosovo", "Cyprus",
        "Azerbaijan", "Belize", "Jamaica", "Trinidad and Tobago", "Barbados", "The Bahamas"],
    "Very weak": [
        "United States of America", "Canada", "United Kingdom", "Ireland", "France", "Germany",
        "Netherlands", "Belgium", "Luxembourg", "Denmark", "Norway", "Sweden", "Finland", "Iceland",
        "Switzerland", "Austria", "Australia", "New Zealand", "Greenland", "Saudi Arabia", "Yemen",
        "Kuwait", "Qatar", "United Arab Emirates", "Oman", "Bahrain", "Iran", "Iraq", "Turkey",
        "Syria", "Jordan", "Lebanon", "Israel", "Palestine", "Egypt", "Libya", "Tunisia", "Algeria",
        "Morocco", "Sudan", "Pakistan", "Afghanistan", "Bangladesh", "Maldives", "Somalia",
        "Somaliland", "Western Sahara", "Malta", "Northern Cyprus"],
}
of_country = {c: lvl for lvl, cs in LEVEL.items() for c in cs}


def main():
    paths = {lvl: [] for lvl in LEVEL}
    unmapped = []
    for f in G.fetch("admin0")["features"]:
        admin = f["properties"].get("ADMIN")
        if admin == "Antarctica":
            continue
        lvl = of_country.get(admin)
        if lvl is None:
            unmapped.append(admin)
            continue
        for poly in G.parts_of(f["geometry"]):
            _, lat = G.centroid(poly)
            if lat < -60:
                continue
            paths[lvl].append(G.path_d(poly))
    out = {lvl: "".join(paths[lvl]) for lvl in LEVEL}
    dest = HERE / "substrate_geo.json"
    dest.write_text(json.dumps(out, ensure_ascii=False))
    print(f"{sum(bool(v) for v in out.values())}/{len(out)} levels filled "
          f"({dest.stat().st_size / 1024:.0f}KB)")
    if unmapped:
        print("UNMAPPED:", ", ".join(sorted(unmapped)))


if __name__ == "__main__":
    main()
