"""Precompute the predominant-religion polygons for mockup 62's `religions` facet.

A country-level choropleth of the world's widespread religions, draped over the same
Natural Earth admin-0 borders as the regions `areas` facet. Split countries are assigned
by plurality — this is the modern *overlay* stratum (great scriptural religions), not the
deep indigenous layer the regions map colours. Output: religions_geo.json = {religion: d}.

    python mockups/62-facet-map/build_religions_geo.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_region_geo as G  # noqa: E402  (reuse fetch / parts_of / centroid / path_d)

# ordered religion categories (label -> member countries, NE admin-0 ADMIN names)
RELIGION = {
    "Catholic Christianity": [
        "Mexico", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama",
        "Colombia", "Venezuela", "Ecuador", "Peru", "Bolivia", "Paraguay", "Chile", "Argentina",
        "Uruguay", "Brazil", "Cuba", "Dominican Republic", "Haiti", "Puerto Rico",
        "Portugal", "Spain", "France", "Italy", "Ireland", "Belgium", "Luxembourg", "Austria",
        "Poland", "Czechia", "Slovakia", "Hungary", "Slovenia", "Croatia", "Lithuania", "Malta",
        "Andorra", "Monaco", "San Marino", "Liechtenstein",
        "Angola", "Democratic Republic of the Congo", "Republic of the Congo", "Rwanda", "Burundi",
        "Equatorial Guinea", "Gabon", "Cabo Verde", "São Tomé and Principe", "Seychelles",
        "Philippines", "East Timor", "Vatican",
        "Aruba", "Curaçao", "Dominica", "Saint Lucia", "Grenada",
        "Saint Vincent and the Grenadines"],
    "Orthodox Christianity": [
        "Russia", "Ukraine", "Belarus", "Moldova", "Romania", "Bulgaria", "Republic of Serbia",
        "Montenegro", "North Macedonia", "Greece", "Cyprus", "Georgia", "Armenia", "Ethiopia",
        "Eritrea"],
    "Protestant / other Christian": [
        "United States of America", "Canada", "United Kingdom", "Germany", "Netherlands", "Denmark",
        "Norway", "Sweden", "Finland", "Iceland", "Estonia", "Latvia", "Switzerland", "Greenland",
        "Australia", "New Zealand", "Fiji", "Papua New Guinea", "Solomon Islands", "Vanuatu",
        "Samoa", "Tonga", "New Caledonia", "Federated States of Micronesia", "Marshall Islands",
        "Palau", "Kiribati", "Tuvalu", "Nauru", "Cook Islands", "Niue", "French Polynesia",
        "American Samoa", "Guam", "Northern Mariana Islands", "Wallis and Futuna",
        "Antigua and Barbuda", "Saint Kitts and Nevis", "Bermuda", "Cayman Islands",
        "Turks and Caicos Islands", "British Virgin Islands", "United States Virgin Islands",
        "Anguilla", "Montserrat", "Sint Maarten", "Saint Martin", "Saint Barthelemy",
        "Faroe Islands", "Isle of Man", "Jersey", "Guernsey", "Aland", "Falkland Islands",
        "Saint Pierre and Miquelon", "Saint Helena",
        "South Africa", "Namibia", "Botswana", "Zimbabwe", "Zambia", "Malawi", "Lesotho", "eSwatini",
        "Kenya", "Uganda", "United Republic of Tanzania", "Ghana", "Liberia", "Cameroon",
        "Central African Republic", "Mozambique", "Madagascar",
        "Jamaica", "Trinidad and Tobago", "Guyana", "Suriname", "Belize", "The Bahamas", "Barbados"],
    "Sunni Islam": [
        "Morocco", "Algeria", "Tunisia", "Libya", "Egypt", "Sudan", "Mauritania", "Mali", "Niger",
        "Chad", "Senegal", "The Gambia", "Guinea", "Guinea-Bissau", "Burkina Faso", "Sierra Leone",
        "Somalia", "Somaliland", "Djibouti", "Comoros", "Western Sahara", "Nigeria", "Ivory Coast",
        "Gambia", "Northern Cyprus",
        "Saudi Arabia", "Yemen", "Jordan", "Palestine", "Syria", "Kuwait", "Qatar",
        "United Arab Emirates", "Oman", "Lebanon", "Turkey", "Afghanistan", "Pakistan", "Bangladesh",
        "Turkmenistan", "Uzbekistan", "Tajikistan", "Kyrgyzstan", "Kazakhstan",
        "Indonesia", "Malaysia", "Brunei", "Maldives",
        "Kosovo", "Albania", "Bosnia and Herzegovina"],
    "Shia Islam": ["Iran", "Iraq", "Azerbaijan", "Bahrain"],
    "Judaism": ["Israel"],
    "Hinduism": ["India", "Nepal", "Mauritius"],
    "Buddhism": ["Thailand", "Myanmar", "Cambodia", "Laos", "Sri Lanka", "Bhutan", "Mongolia"],
    "East Asian (folk / syncretic)": [
        "China", "Japan", "North Korea", "South Korea", "Taiwan", "Vietnam", "Singapore",
        "Hong Kong S.A.R.", "Macao S.A.R"],
    # the few states where indigenous/ethnic religion is still plurality or the defining stratum —
    # the West-African Vodun/animist belt and South Sudan (elsewhere it survives only as substrate)
    "Ethnic / traditional": ["Benin", "Togo", "South Sudan"],
}
of_country = {c: rel for rel, cs in RELIGION.items() for c in cs}


def main():
    paths = {rel: [] for rel in RELIGION}
    unmapped = []
    for f in G.fetch("admin0")["features"]:
        admin = f["properties"].get("ADMIN")
        if admin == "Antarctica":
            continue
        rel = of_country.get(admin)
        if rel is None:
            unmapped.append(admin)
            continue
        for poly in G.parts_of(f["geometry"]):
            _, lat = G.centroid(poly)
            if lat < -60:
                continue
            paths[rel].append(G.path_d(poly))
    out = {rel: "".join(paths[rel]) for rel in RELIGION}
    dest = HERE / "religions_geo.json"
    dest.write_text(json.dumps(out, ensure_ascii=False))
    print(f"{sum(bool(v) for v in out.values())}/{len(out)} religions filled "
          f"({dest.stat().st_size / 1024:.0f}KB)")
    if unmapped:
        print("UNMAPPED:", ", ".join(sorted(unmapped)))


if __name__ == "__main__":
    main()
