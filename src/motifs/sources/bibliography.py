"""Decoding key for the abbreviated citations in Thompson Motif-Index ``notes``.

Thompson cites sources in a private shorthand (``Beckwith Myth 42``, ``BP III``,
``FFC CXX``). This resolves that shorthand to full titles and live book links by
(1) parsing the digitised *Motif-Index* bibliography at folkmasa.org, (2) adding a
curated supplement of high-frequency foreign works the English list omits, and
(3) annotating each entry with its citation frequency across the built TMI data.

``refresh()`` is a pipeline step run after the TMI index is built: it fetches the
folkmasa page into the resumable raw cache and writes
``outputs/motifs/tmi_bibliography.json`` (not committed — the server reads it from
there). The standalone ``scripts/build_tmi_bibliography.py`` also regenerates the
human-readable ``docs/motifs/tmi-bibliography-key.md``.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

from settings import settings

from ..refresh import Fetchable
from .fetch import fetch_text, raw_dir

logger = logging.getLogger(__name__)

SOURCE_URL = "https://folkmasa.org/motiv/motif_bib.htm"
OUT_FILE = "tmi_bibliography.json"

# High-frequency works absent from the English list (mostly German/French), with a
# full title and a verified open-access link. Keyed by the citation shorthand.
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
    "Thompson-Balys": (
        "Thompson, S. & Balys, J. The Oral Tales of India (Indiana University "
        "Publications, Folklore Series 10). Bloomington, 1958.",
        "https://archive.org/details/oraltalesofindia0000stit"),
    "Boberg": ("Boberg, I. M. Motif-Index of Early Icelandic Literature "
               "(Bibliotheca Arnamagnæana 27). Copenhagen, 1966. (tagged 'Icel.: Boberg')",
               "https://archive.org/search?query=Boberg+Motif-Index+Early+Icelandic"),
}

# Series acronyms worth spelling out even when used bare.
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


def _split_url(raw: str) -> dict:
    url, _, label = raw.strip().partition(" ")
    return {"url": url, "label": label.strip(" ()") or ""}


def parse_entries(html: str) -> list[dict]:
    """Each bibliography entry: full text, its abbrev/author keys, and book URLs."""
    from bs4 import BeautifulSoup

    paras = [" ".join(p.get_text(" ", strip=True).split())
             for p in BeautifulSoup(html, "html.parser").find_all("p")]
    paras = [p for p in paras if p]

    is_url = re.compile(r"^https?://")
    is_new = re.compile(r"^\*?\s*[A-ZÀ-Ý][A-Za-zÀ-ý.'\-]+\s*,| = ")
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
        inline = url_token.findall(e["text"])
        text = url_token.sub("", e["text"]).lstrip("* ").strip(" .")
        keys = []
        if " = " in text:
            keys.append(text.split(" = ", 1)[0].strip(" *"))
        m = re.match(r"^([A-ZÀ-Ý][A-Za-zÀ-ý.'\-]+)", text)
        if m and m.group(1) not in keys:
            keys.append(m.group(1))
        e["keys"] = keys
        e["text"] = text
        e["urls"] = [_split_url(u) for u in e["urls"] + inline]
    return entries


def _corpus_counts(tmi_records: list[dict]) -> Counter:
    """How often each citation head (author / abbrev) appears across TMI notes."""
    head: Counter = Counter()
    head_re = re.compile(r"([A-Z][A-Za-z.'\-]+(?:[ -][A-Z][A-Za-z.'\-]+){0,2})\s+(?=[IVXLC]{1,5}\b|\d|No\.)")
    for m in tmi_records:
        for h in head_re.findall(m.get("notes", "")):
            head[h] += 1
    return head


def _count_for(keys: list[str], heads: Counter) -> int:
    return sum(c for h, c in heads.items() if any(h == k or h.startswith(k + " ") for k in keys))


def build(html: str, tmi_records: list[dict]) -> dict:
    """The bibliography key: folkmasa entries + curated supplement + usage counts."""
    heads = _corpus_counts(tmi_records)
    records = []
    for e in parse_entries(html):
        records.append({"keys": e["keys"], "citation": e["text"], "urls": e["urls"],
                        "uses": _count_for(e["keys"], heads), "source": "folkmasa"})
    for key, (citation, url) in CURATED.items():
        keys = list(dict.fromkeys([key, key.split()[0]]))
        records.append({"keys": keys, "citation": citation, "urls": [{"url": url, "label": ""}],
                        "uses": _count_for(keys, heads), "source": "curated"})
    records.sort(key=lambda r: (-r["uses"], r["keys"][0].lower() if r["keys"] else ""))
    return {"source_url": SOURCE_URL, "series": SERIES, "entries": records}


def out_path() -> Path:
    return Path(settings.motifs_dir) / OUT_FILE


def fetchables() -> list[Fetchable]:
    """The one folkmasa bibliography page."""
    return [Fetchable("folkmasa_bibliography.html", SOURCE_URL, raw_dir() / "folkmasa_bibliography.html")]


def refresh(tmi_records: list[dict], *, force: bool = False) -> dict:
    """Pipeline step: fetch folkmasa, build the key, write it to outputs/motifs/."""
    cache = Path(settings.motifs_dir) / "raw" / "folkmasa_bibliography.html"
    html = fetch_text(SOURCE_URL, cache, encoding="windows-1255", force=force)
    data = build(html, tmi_records)
    out_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    linked = sum(1 for r in data["entries"] if r["urls"])
    logger.info("bibliography: %d citation entries (%d with a book link) from folkmasa + curated",
                len(data["entries"]), linked)
    return {"entries": len(data["entries"]), "linked": linked}
