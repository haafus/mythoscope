#!/usr/bin/env python3
"""Build a decoding key for the abbreviated citations in TMI ``notes``.

Thompson cites sources in a private shorthand (``Beckwith Myth 42``, ``BP III``,
``FFC CXX``). This resolves that shorthand to full titles and live book links by:

1. parsing the digitised *Motif-Index* bibliography at folkmasa.org (the English
   list — full author + title + an online-book URL per entry);
2. adding a curated supplement for the high-frequency foreign works the English
   list omits (Bolte-Polívka, Dähnhardt, Chauvin, …), with verified links;
3. annotating every entry with how often it is cited across the built TMI data.

Outputs ``outputs/motifs/tmi_bibliography.json`` and ``docs/tmi-bibliography-key.md``.
Run: ``python scripts/build_tmi_bibliography.py`` (re-fetches unless the raw page
is already cached under ``outputs/motifs/raw/``).
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "outputs" / "motifs" / "raw" / "folkmasa_bibliography.html"
TMI = ROOT / "outputs" / "motifs" / "tmi.json"
# Tracked package-data asset so the server can resolve citation links at runtime.
OUT_JSON = ROOT / "src" / "motifs" / "data" / "tmi_bibliography.json"
OUT_DOC = ROOT / "docs" / "tmi-bibliography-key.md"
SOURCE_URL = "https://folkmasa.org/motiv/motif_bib.htm"

# High-frequency works absent from the English list (mostly German/French), with
# a full title and a verified open-access link. Keyed by the citation shorthand.
CURATED = {
    "BP": ("Bolte, J. & Polívka, G. Anmerkungen zu den Kinder- und Hausmärchen "
           "der Brüder Grimm. 5 vols. Leipzig, 1913–32.",
           "https://archive.org/details/AnmerkungenZuDenKinder-UndHausmaerchenDerGebruederGrimm1"),
    "Dh": ("Dähnhardt, O. Natursagen: eine Sammlung naturdeutender Sagen, "
           "Märchen, Fabeln und Legenden. 4 vols. Leipzig, 1907–12.",
           "https://archive.org/details/natursageneinesa01dhuoft"),
    "Chauvin": ("Chauvin, V. Bibliographie des ouvrages arabes ou relatifs aux "
                "Arabes publiés dans l'Europe chrétienne de 1810 à 1885. 12 vols. "
                "Liège, 1892–1922.",
                "https://archive.org/details/bibliographiedes05chauuoft"),
    "Wesselski Hodscha Nasreddin": (
        "Wesselski, A. Der Hodscha Nasreddin. 2 vols. Weimar, 1911.",
        "https://archive.org/details/derhodschanasred01wess"),
    "Wienert": ("Wienert, W. Die Typen der griechisch-römischen Fabel (FFC 56). "
                "Helsinki, 1925. — source of the ET (Ethische Typen) and ST "
                "(Stofftypen) numbers.",
                "https://archive.org/search?query=Wienert+Typen+griechisch-r%C3%B6mischen+Fabel"),
    "Grimm": ("Grimm, J. & W. Kinder- und Hausmärchen (cited by tale number). "
              "Berlin, 1857.",
              "https://www.gutenberg.org/ebooks/2591"),
    "Kristensen Danske Sagn": (
        "Kristensen, E. T. Danske Sagn. 6 vols. Aarhus, 1892–1901.",
        "https://archive.org/search?query=Kristensen+Danske+Sagn"),
    "Balys Index": ("Balys, J. Motif-Index of Lithuanian Narrative Folk-Lore "
                    "(Tautosakos Darbai II). Kaunas, 1936.",
                    "https://archive.org/search?query=Balys+Motif-Index+Lithuanian"),
    "Neuman": ("Neuman (Noy), D. Motif-Index of Talmudic-Midrashic Literature. "
               "Diss., Indiana University, 1954. (cited as 'Jewish: Neuman')",
               "https://archive.org/search?query=Neuman+Motif-Index+Talmudic"),
    "Eberhard": ("Eberhard, W. & Boratav, P. N. Typen türkischer Volksmärchen "
                 "(FFC). — and Eberhard, Typen chinesischer Volksmärchen (FFC 120).",
                 "https://archive.org/search?query=Eberhard+Typen+chinesischer+Volksm%C3%A4rchen"),
    # --- tail: FFC monographs, regional collections, and classic texts ---
    "Boggs": ("Boggs, R. S. Index of Spanish Folktales (FFC 90). Helsinki, 1930.",
              "https://en.wikisource.org/wiki/Index_of_Spanish_Folktales"),
    "Halm Aesop": ("Halm, K. Fabulae Aesopicae Collectae. Leipzig, 1875.",
                   "https://archive.org/details/fabulaeaesopica00aesogoog"),
    "Jegerlehner Oberwallis": (
        "Jegerlehner, J. Sagen und Märchen aus dem Oberwallis. Basel, 1913.",
        "https://catalog.hathitrust.org/Record/001675073"),
    "Sob": ("Zong In-Sob. Folk Tales from Korea. London, 1952. "
            "(cited as 'Korean: Zong in-Sob')",
            "https://archive.org/search?query=Zong+In-Sob+Folk+Tales+from+Korea"),
    "Wessman": ("Wessman, V. E. V. Finlands svenska folkdiktning (FFC / SLS). Helsingfors.",
                "https://www.folklorefellows.fi/ffc-catalogue/"),
    "Aarne": ("Aarne, A. Comparative folktale-type monographs in FF Communications "
              "(e.g. FFC 8, 23, 25, 33).",
              "https://www.folklorefellows.fi/ffc-catalogue/"),
    "Rasmussen": ("Rasmussen, K. Report of the Fifth Thule Expedition 1921–24 "
                  "(Intellectual Culture of the Iglulik / Netsilik / Copper Eskimos). "
                  "Copenhagen, 1929–32.",
                  "https://archive.org/details/intellectualcult00rasm"),
    "Holmberg Siberian": (
        "Holmberg (Harva), U. Finno-Ugric, Siberian (The Mythology of All Races IV). "
        "Boston, 1927.",
        "https://archive.org/details/finnougricsiberi0000unoh"),
    "Fansler": ("Fansler, D. S. Filipino Popular Tales (MAFLS 12). Lancaster, 1921.",
                "https://www.gutenberg.org/ebooks/8299"),
    "Espinosa": ("Espinosa, A. M. Cuentos populares españoles. 3 vols. Stanford, 1923–26.",
                 "https://onlinebooks.library.upenn.edu/webbin/book/lookupid?key=ha000869997"),
    "Espinosa Jr.": ("Espinosa, J. M. Spanish Folk-Tales from New Mexico (MAFLS 30). 1937.",
                     "https://archive.org/search?query=Espinosa+Spanish+Folk-Tales+New+Mexico"),
    "Gorion Born Judas": (
        "bin Gorion (Berdichevsky), M. J. Der Born Judas. 6 vols. Leipzig, 1916–23.",
        "https://archive.org/details/derbornjudaslege06berd"),
    "Andrejev": ("Andrejev, N. P. Index of Ukrainian Folktale Types (FFC 69). 1927.",
                 "https://www.folklorefellows.fi/ffc-catalogue/"),
    "Loorits": ("Loorits, O. Estonian folk-narrative monographs in FF Communications.",
                "https://www.folklorefellows.fi/ffc-catalogue/"),
    "Vries": ("de Vries, J. Die Märchen von klugen Rätsellösern (FFC 73). Helsinki, 1928.",
              "https://www.folklorefellows.fi/ffc-catalogue/"),
    "Herrmann Saxo": (
        "Herrmann, P. Erläuterungen zu den ersten neun Büchern der dänischen "
        "Geschichte des Saxo Grammaticus. 2 vols. Leipzig, 1901–22.",
        "https://archive.org/search?query=Herrmann+Saxo+Grammaticus+Erl%C3%A4uterungen"),
    "Parsons": ("Parsons, E. C. Folk-Lore of the Sea Islands / Antilles (MAFLS).",
                "https://archive.org/search?query=Parsons+Folk-Lore+Antilles+Memoirs"),
    "Cent Nouvelles Nouvelles": (
        "Les Cent Nouvelles Nouvelles (15th-c. French tale collection).",
        "https://archive.org/search?query=Cent+Nouvelles+Nouvelles"),
    "Heptameron": ("Marguerite de Navarre. The Heptameron.",
                   "https://www.gutenberg.org/ebooks/17701"),
    "Bolte": ("Bolte, J. — co-author of BP (Bolte & Polívka); see BP.",
              "https://archive.org/details/AnmerkungenZuDenKinder-UndHausmaerchenDerGebruederGrimm1"),
    "Newman": ("Newman / Neuman, D. Motif-Index of Talmudic-Midrashic Literature. "
               "Indiana University, 1954. (variant spelling of Neuman)",
               "https://archive.org/search?query=Neuman+Motif-Index+Talmudic"),
    "Boas": ("Boas, F. Tsimshian Mythology (RBAE 31), 1916; The Eskimo of Baffin "
             "Land and Hudson Bay (BAM XV), 1901–07; and many papers in JAFL/BAM/RBAE.",
             "https://archive.org/search?query=Boas+Tsimshian+Mythology"),
}

# Series acronyms worth spelling out even when used bare (some are also in the
# English list, but the expansion is handy in one place).
SERIES = {
    "FFC": "FF Communications (Folklore Fellows). Helsinki, 1910 ff.",
    "JAFL": "Journal of American Folk-Lore. 1888 ff.",
    "MAFLS": "Memoirs of the American Folk-Lore Society.",
    "BBAE": "Bulletin of the Bureau of American Ethnology (Smithsonian).",
    "RBAE": "Annual Report of the Bureau of American Ethnology.",
    "BAM": "Bulletin of the American Museum of Natural History.",
    "PMLA": "Publications of the Modern Language Association of America.",
    "RTP": "Revue des traditions populaires. Paris, 1886–1919.",
    "RMLP": "Revista do Museu Paulista. São Paulo.",
    "ET": "Wienert, Ethische Typen (see Wienert FFC 56).",
    "ST": "Wienert, Stofftypen (see Wienert FFC 56).",
    "DF": "Danmarks Folkeminder. Copenhagen, 1908 ff.",
    "MSFO": "Mémoires de la Société Finno-Ougrienne. Helsinki.",
    "BMB": "Bernice P. Bishop Museum Bulletin. Honolulu.",
    "JE": "Publications of the Jesup North Pacific Expedition (Mem. AMNH).",
    "FL": "Folk-Lore. London, 1890 ff.",
    "CColl": "Colorado College Publication, Language Series.",
    "MAGW": "Mitteilungen der Anthropologischen Gesellschaft in Wien.",
}


def fetch_html() -> str:
    if not RAW.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:  # noqa: S310
            RAW.write_bytes(resp.read())
    return RAW.read_bytes().decode("windows-1255", "replace")


def parse_entries(html: str) -> list[dict]:
    """Each bibliography entry: full text, its abbrev/author keys, and book URLs."""
    from bs4 import BeautifulSoup

    paras = [" ".join(p.get_text(" ", strip=True).split()) for p in BeautifulSoup(html, "html.parser").find_all("p")]
    paras = [p for p in paras if p]

    is_url = re.compile(r"^https?://")
    is_new = re.compile(r"^[*☉]?\s*[A-ZÀ-Ý][A-Za-zÀ-ý.'\-]+\s*,| = ")
    entries: list[dict] = []
    cur: dict | None = None
    for p in paras:
        if is_url.match(p):
            if cur:
                cur["urls"].append(p)
        elif is_new.search(p) and len(p) > 12:
            cur = {"text": p, "urls": []}
            entries.append(cur)
        elif cur:
            cur["text"] += " " + p

    url_token = re.compile(r"https?://\S+")
    for e in entries:
        # Some entries inline their URL in the citation text; pull those out too.
        inline = url_token.findall(e["text"])
        text = url_token.sub("", e["text"]).lstrip("*☉ ").strip(" .")
        keys = []
        if " = " in text:
            keys.append(text.split(" = ", 1)[0].strip(" *☉"))
        m = re.match(r"^([A-ZÀ-Ý][A-Za-zÀ-ý.'\-]+)", text)
        if m and m.group(1) not in keys:
            keys.append(m.group(1))
        e["keys"] = keys
        e["text"] = text
        # A URL paragraph may trail an annotation ("…01somauoft (Vol. I)"); split it.
        e["urls"] = [_split_url(u) for u in e["urls"] + inline]
    return entries


def _split_url(raw: str) -> dict:
    url, _, label = raw.strip().partition(" ")
    return {"url": url, "label": label.strip(" ()") or ""}


def corpus_counts() -> dict[str, int]:
    """How often each citation head (author / abbrev) appears across TMI notes."""
    from collections import Counter

    motifs = json.loads(TMI.read_text())["motifs"]
    head = Counter()
    head_re = re.compile(r"([A-Z][A-Za-z.'\-]+(?:[ -][A-Z][A-Za-z.'\-]+){0,2})\s+(?=[IVXLC]{1,5}\b|\d|No\.)")
    for m in motifs:
        for h in head_re.findall(m.get("notes", "")):
            head[h] += 1
    return head


def count_for(keys: list[str], heads: dict[str, int]) -> int:
    """Sum corpus hits for an entry: any head equal to, or starting with, a key."""
    total = 0
    for h, c in heads.items():
        if any(h == k or h.startswith(k + " ") for k in keys):
            total += c
    return total


def build() -> dict:
    entries = parse_entries(fetch_html())
    heads = corpus_counts()

    records = []
    for e in entries:
        records.append({
            "keys": e["keys"],
            "citation": e["text"],
            "urls": e["urls"],
            "uses": count_for(e["keys"], heads),
            "source": "folkmasa",
        })
    for key, (citation, url) in CURATED.items():
        keys = list(dict.fromkeys([key, key.split()[0]]))
        records.append({
            "keys": keys,
            "citation": citation,
            "urls": [{"url": url, "label": ""}],
            "uses": count_for(keys, heads),
            "source": "curated",
        })

    records.sort(key=lambda r: (-r["uses"], r["keys"][0].lower() if r["keys"] else ""))
    return {"source_url": SOURCE_URL, "series": SERIES, "entries": records}


def write_doc(data: dict) -> None:
    lines = [
        "# TMI bibliography key",
        "",
        "Decodes the abbreviated citations in Thompson Motif-Index `notes` into full",
        "titles and live book links. Generated by `scripts/build_tmi_bibliography.py`.",
        "",
        f"English bibliography parsed from <{data['source_url']}>; foreign works added",
        "as a curated supplement. `uses` = approximate citation count in the built TMI data.",
        "",
        "## Series & journal acronyms",
        "",
    ]
    for ab, full in sorted(data["series"].items()):
        lines.append(f"- **{ab}** — {full}")
    lines += ["", "## Works (most-cited first)", "",
              "| uses | shorthand | full citation | link |", "|---:|---|---|---|"]
    for r in data["entries"]:
        short = ", ".join(f"`{k}`" for k in r["keys"])
        link = " · ".join(f"[{u['label'] or i + 1}]({u['url']})" for i, u in enumerate(r["urls"])) or "—"
        cite = r["citation"].replace("|", "\\|")
        tag = "" if r["source"] == "folkmasa" else " ✚"
        lines.append(f"| {r['uses']} | {short}{tag} | {cite} | {link} |")
    lines += ["", "✚ = curated supplement (not in the English bibliography).", ""]
    OUT_DOC.write_text("\n".join(lines))


if __name__ == "__main__":
    data = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    write_doc(data)
    n = len(data["entries"])
    linked = sum(1 for r in data["entries"] if r["urls"])
    print(f"{n} entries ({linked} with a book link) -> {OUT_DOC.relative_to(ROOT)}, {OUT_JSON.relative_to(ROOT)}")
