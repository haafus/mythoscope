import json
import sys

# Other tests (test_corpus_*) stub `bs4` into sys.modules; the Berezkin parser
# needs the real library, so drop any stub and import the genuine module here.
sys.modules.pop("bs4", None)
import bs4  # noqa: E402,F401
import pytest  # noqa: E402

from motifs import build_motifs as bm  # noqa: E402
from motifs import crosswalk, parallels, store  # noqa: E402
from motifs.sources import ashliman, atu_regions, berezkin, culture_dict, tmi_notes, trilogy
from motifs.sources import berezkin_bibliography as bbib
from server.services import motifs as svc

# ---------------------------------------------------------------------------
# Berezkin parsing
# ---------------------------------------------------------------------------

class TestBerezkinEntry:
    def test_plain_motif(self):
        e = berezkin.parse_motif_entry("A1. Древнее солнце. .19.21.29.43.-.50.", "a1.html")
        assert e["id"] == "A1"
        assert e["name"] == "Древнее солнце"
        assert e["chapter"] == "A"
        assert e["areas"] == [19, 21, 29, 43, 44, 45, 46, 47, 48, 49, 50]
        assert e["see_also"] == []
        assert e["atu_refs"] == []
        assert e["page"] == "a1.html"

    def test_bare_title_code_is_foreign_not_see_also(self):
        # A bare "A50." in a title is a Thompson equivalence (carried by tmi_refs),
        # not a Berezkin see-also: stripped from the name, never captured.
        e = berezkin.parse_motif_entry("B1. Двое создателей. A50. .13.16.20.", "b1.html")
        assert e["name"] == "Двое создателей"
        assert e["see_also"] == []
        assert e["areas"] == [13, 16, 20]

    def test_thompson_ref_in_title_stripped_cleanly(self):
        # "A736.2" is a Thompson id — its stem must not become a see-also, nor its
        # ".2" tail be left glued to the name.
        e = berezkin.parse_motif_entry("A4. Солнце-женщина, A736.2. .10.52.", "a4.html")
        assert e["name"] == "Солнце-женщина"
        assert e["see_also"] == []

    def test_cyrillic_homoglyph_thompson_ref_stripped(self):
        e = berezkin.parse_motif_entry("K20. Смертный желает звезду, С15.1, C15.1.1. .10.11.", "k20.html")
        assert e["name"] == "Смертный желает звезду"
        assert e["see_also"] == []

    def test_clean_atu_refs_normalises_and_drops_junk(self):
        # Free-text ATU refs from mapsofmyths arrive wrapped/annotated; normalise
        # each to a canonical tale-type id and drop anything not id-shaped.
        clean = berezkin._clean_atu_refs
        assert clean(["(751A)"]) == ["751A"]                 # unwrap parens
        assert clean(["934H(4)"]) == ["934H"]                # drop trailing "(subtype)"
        assert clean(["1600A (el-Shamy 2004)"]) == ["1600A"]  # drop trailing comment
        assert clean(["*597"]) == ["597"]                    # strip leading star
        assert clean(["*303*707"]) == ["303", "707"]         # split "*"-joined combo
        assert clean(["751b*"]) == ["751B*"]                 # upper-case subtype, keep star
        assert clean(["328A*"]) == ["328A*"]                 # a clean ref is untouched
        assert clean(["1525H1"]) == ["1525H1"]               # trailing digit preserved
        assert clean(["the last episode"]) == []             # pure junk dropped
        assert clean(["825", "(825)"]) == ["825"]            # dedup after cleaning

    def test_clean_tmi_refs_normalises_and_drops_junk(self):
        clean = berezkin._clean_tmi_refs
        assert clean(["*A1115"]) == ["A1115"]                 # strip star prefix
        assert clean(["A736.2."]) == ["A736.2"]               # strip trailing dot
        assert clean(["†A2219.2."]) == ["A2219.2"]       # strip dagger + dot
        assert clean(["* A1195"]) == ["A1195"]                # star + space
        assert clean(["D1565.1+E30.1"]) == ["D1565.1", "E30.1"]  # split "+" combo
        assert clean(["A812"]) == ["A812"]                    # a clean id is untouched
        assert clean(["the note"]) == []                      # non-id junk dropped

    def test_see_also_from_definition(self):
        # Berezkin's own cross-refs live in the definition ("см. мотив X"); only ids
        # that resolve to a real motif (and not the motif itself) are kept.
        motifs = [
            {"id": "A4", "definition": "Солнце-женщина (см. мотив A6; ср. A2)."},
            {"id": "A6", "definition": "нет ссылок"},
            {"id": "B11", "definition": "как в см. мотивы B12, B13 и B11."},
            {"id": "B12", "definition": ""}, {"id": "B13", "definition": ""},
        ]
        berezkin._attach_see_also(motifs)
        assert motifs[0]["see_also"] == ["A6"]     # A2 dropped (no such motif); self excluded
        assert motifs[1]["see_also"] == []
        assert motifs[2]["see_also"] == ["B12", "B13"]  # self "B11" excluded

    def test_atu_reference_in_title(self):
        e = berezkin.parse_motif_entry("A8A. Освобождение солнца. ATU 328A*, .27.28.", "a8a.html")
        assert e["name"] == "Освобождение солнца"
        assert e["atu_refs"] == ["328A*"]
        assert e["areas"] == [27, 28]

    def test_paren_introduced_areas(self):
        e = berezkin.parse_motif_entry("A39A. Двенадцать месяцев. ATU 294., (.11.).12.15.-.17.", "a39a.html")
        assert e["name"] == "Двенадцать месяцев"
        assert e["atu_refs"] == ["294"]
        assert e["areas"] == [11, 12, 15, 16, 17]

    def test_foreign_ref_list_stripped_from_name(self):
        # A run of Thompson equivalences (with ".I" artifacts) is cleared from the
        # name and, lacking a "см." marker, contributes no see-also.
        e = berezkin.parse_motif_entry("A21. Светила заброшены в небо. A700.I. A714. A741., .10.12.", "a21.html")
        assert e["name"] == "Светила заброшены в небо"
        assert e["see_also"] == []
        assert e["areas"] == [10, 12]

    def test_atu_comma_list_does_not_leak_into_areas(self):
        # "ATU 311, 312" — both are refs; 312 must not become an area index.
        e = berezkin.parse_motif_entry("L4. Разоблаченный убийца. ATU 311, 312. .10.11.", "l4.html")
        assert e["atu_refs"] == ["311", "312"]
        assert e["areas"] == [10, 11]
        assert e["name"] == "Разоблаченный убийца"

    def test_bare_tale_type_refs_captured(self):
        e = berezkin.parse_motif_entry("J47A. Боб до неба. , 804A. .10.12.", "j47a.html")
        assert e["atu_refs"] == ["804A"]
        assert e["name"] == "Боб до неба"
        assert e["areas"] == [10, 12]

    def test_thompson_notation_stripped(self):
        e = berezkin.parse_motif_entry("H49. Убитый пес. Th .1.4.1; .2.2. .27.", "h49.html")
        assert e["name"] == "Убитый пес"

    def test_bracketed_area_list(self):
        # A distribution wrapped in "[…]" parses transparently: the inner "(…)"
        # still marks a comparative area and the name stays clean.
        e = berezkin.parse_motif_entry("A32de. Безголовый на луне. [(.21.).31.32.35.36.)]", "a32de.html")
        assert e["name"] == "Безголовый на луне"
        assert e["areas"] == [21, 31, 32, 35, 36]

    def test_latin_homoglyph_fixed(self):
        e = berezkin.parse_motif_entry("E30A. Cупруг-эрзац заменен настоящим. .27.28.", "e30a.html")
        assert e["name"] == "Супруг-эрзац заменен настоящим"

    def test_no_code_returns_none(self):
        assert berezkin.parse_motif_entry("Not a motif line", "x.html") is None

    def test_chapter_of(self):
        assert berezkin.chapter_of("A2a1") == "A"
        assert berezkin.chapter_of("B12C") == "B"


class TestBerezkinAreas:
    def test_range_expansion(self):
        e = berezkin.parse_motif_entry("C1. Имя. .1.-.4.9.", "c1.html")
        assert e["areas"] == [1, 2, 3, 4, 9]

    def test_implausible_index_dropped(self):
        # A leaked 4-digit number must not appear as an area.
        nums = berezkin._expand_areas(".5.1730.7.")
        assert 1730 not in nums
        assert nums == [5, 7]


class TestBerezkinAreaDecode:
    def test_parse_area_seq_tracks_parens_and_ranges(self):
        seq = berezkin._parse_area_seq(" .19.21.(.44.).45.-.47.")
        assert seq == [(19, False), (21, False), (44, True), (45, False), (46, False), (47, False)]

    def test_canonical_area_legend_matches_published_key(self):
        legend = berezkin.canonical_area_legend()
        # Numbering runs 10–74 (the published intro.html key).
        assert min(int(k) for k in legend) == 10
        assert max(int(k) for k in legend) == 74
        # Each code decodes to a distinct macro-area — no duplicate labels.
        assert len(set(legend.values())) == len(legend)
        # Spot-check codes that the old voted legend got wrong (27/28 both "Балканы",
        # 58/59 both "Гвиана").
        assert legend["27"] == "Балканы"
        assert legend["28"] == "Средняя Европа"
        assert legend["52"] == "Мезоамерика"
        assert legend["58"] == "Дельта Ориноко"
        assert legend["59"] == "Гвиана"

    def test_canonical_legend_is_a_fresh_copy(self):
        legend = berezkin.canonical_area_legend()
        legend["27"] = "tampered"
        assert berezkin.canonical_area_legend()["27"] == "Балканы"


class TestMapsofmythsEnrichment:
    def test_split_refs(self):
        assert berezkin._split_refs("516, 565; 505/311") == ["516", "565", "505", "311"]
        assert berezkin._split_refs("") == []

    def test_attach_nodes_prefers_and_merges(self, monkeypatch):
        monkeypatch.setattr(berezkin, "load_nodes", lambda: {
            "A2A": {"type": "Cosmology and etiology", "group": "01 Sun and Moon",
                    "group_num": "01", "tmi": "*A720.1", "atu": "565",
                    "traditions": ["6.2.3.1", "26.1.1.1"]},
        })
        motifs = [{"id": "A2a", "atu_refs": ["565"]}]  # lowercase id, title already had ATU
        berezkin._attach_nodes(motifs)
        m = motifs[0]
        assert m["motif_type"] == "Cosmology and etiology"
        assert m["motif_group_num"] == "01"
        assert m["tmi_refs"] == ["A720.1"]           # cleaned: the "*" prefix stripped
        assert m["atu_refs"] == ["565"]              # merged, de-duplicated
        assert m["traditions"] == ["6.2.3.1", "26.1.1.1"]


class TestTmiParsing:
    def test_reunite_quoted_title(self):
        # Source split a quoted catch-word title wrong: opening quote on the name,
        # closing quote leaked to the front of the notes (K553).
        name, notes = trilogy._reunite_quoted_title(
            '"Wait Till I Get Fat', '" Captured person persuades his captor. Halm Aesop No. 231')
        assert name == '"Wait Till I Get Fat"'
        assert notes == "Captured person persuades his captor. Halm Aesop No. 231"
        # Balanced titles and quote-less names are left alone.
        assert trilogy._reunite_quoted_title('"Bear-Skin"', "def") == ('"Bear-Skin"', "def")
        assert trilogy._reunite_quoted_title("Plain Name", '" x') == ("Plain Name", '" x')


class TestAtuStructure:
    def test_division_parse(self):
        assert trilogy._split_division("Supernatural Adversaries 300-399") == ("Supernatural Adversaries", 300, 399)
        assert trilogy._split_division("No range here") == ("No range here", None, None)
        assert trilogy._atu_sort_key("313A") > trilogy._atu_sort_key("313")

    def test_families_and_division_fill(self):
        rows = [
            {"atu_id": "313", "chapter": "Magic", "division": "Supernatural Adversaries 300-399",
             "tale_name": "x", "tale_type": "y"},
            {"atu_id": "313A", "chapter": "Magic", "division": "", "tale_name": "x", "tale_type": "y"},
            {"atu_id": "1525", "chapter": "Realistic", "division": "Stories 1525-1724",
             "tale_name": "x", "tale_type": "y"},
        ]
        by = {t["id"]: t for t in trilogy._parse_atu(rows, {}, {})[0]}
        assert by["313"]["division"] == "Supernatural Adversaries" and by["313"]["division_range"] == [300, 399]
        assert by["313"]["parent"] is None and "313A" in by["313"]["subtypes"]
        assert by["313A"]["parent"] == "313"
        assert by["313A"]["division"] == "Supernatural Adversaries"  # filled from the range containing 313

    def test_apparatus_fields_and_mojibake(self):
        rows = [
            {"atu_id": "1", "chapter": "Animal", "division": "Wild Animals 1-99",
             "tale_name": "x", "tale_type": "y",
             "litvar": "Krohn 1889, 46ï¿½54; Dï¿½hnhardt 1907ff. IV, 225ï¿½230",
             "provenance": "Finnish: Rausmaa 1982ff. V, Nos. 1ï¿½6; German: Moser-Rath 1964",
             "remarks": "Documented 1178 in the Roman de Renart."},
        ]
        t = trilogy._parse_atu(rows, {}, {})[0][0]
        # digit–digit mojibake becomes an en-dash; a known scholar name is repaired
        # from the dictionary (Dähnhardt); the triple garbage never survives.
        assert t["references"] == "Krohn 1889, 46–54; Dähnhardt 1907ff. IV, 225–230"
        assert t["attestations"].startswith("Finnish: Rausmaa 1982ff. V, Nos. 1–6;")
        assert t["remarks"] == "Documented 1178 in the Roman de Renart."
        assert "ï¿½" not in (t["references"] + t["attestations"])
        # Attestations are parsed into a per-region grouping (Finnish + German -> Europe).
        g = t["attestations_grouped"]
        assert g["total"] == 2
        assert g["regions"] == [{"region": "Europe", "count": 2, "entries": [
            {"people": "Finnish", "cite": "Rausmaa 1982ff. V, Nos. 1–6"},
            {"people": "German", "cite": "Moser-Rath 1964"},
        ]}]


class TestAshliman:
    def test_type_page_padding_override_and_star(self):
        assert ashliman._type_page("1") == "type0001.html"
        assert ashliman._type_page("510A") == "type0510A.html"
        assert ashliman._type_page("954") == "alibaba.html"      # curated override
        assert ashliman._type_page("779J*") == "type0779J.html"  # override removed -> derived, star dropped
        assert ashliman._type_page("2034F") == "type2034F.html"  # star dropped, no override

    def test_parse_variants_filters_noise_and_dedupes(self):
        html = (
            '<a href="#contents">table of contents</a>'
            '<a href="#grimm">Cinderella</a> (Germany) '
            '<a href="#birch">The Wonderful Birch</a> (Russia) '
            '<a href="#jack">How Jack Went to Seek His Fortune, version 1</a> '  # 'version' is NOT noise
            '<a href="#links">Links to related sites</a> '                       # nav noise
            '<a href="#f1">{footnote 1}</a> '                                    # footnote noise
            '<a href="#xt">Tales of types 243A and 1422</a> '                    # cross-type noise
            '<a href="#grimm">Cinderella</a>'                                    # duplicate anchor
        )
        out = ashliman.parse_variants(html, "https://x/type0510A.html")
        titles = [v["title"] for v in out]
        assert titles == ["Cinderella", "The Wonderful Birch",
                          "How Jack Went to Seek His Fortune, version 1"]
        assert out[0]["url"] == "https://x/type0510A.html#grimm"

    def test_canon(self):
        assert ashliman.canon("0510a") == "510A"     # leading zeros stripped, upper-cased
        assert ashliman.canon("1") == "1"
        assert ashliman.canon("779J*") == "779J*"     # letter + star kept
        assert ashliman.canon("1585*") == "1585*"     # star is significant…
        assert ashliman.canon("1585") == "1585"       # …so 1585 != 1585*
        assert ashliman.canon("") is None

    def test_attach_target(self):
        known = {"170", "333", "47A", "47B", "433B", "20A", "20C", "778", "779J*"}
        assert ashliman.attach_target("170A", known) == "170"     # subtype -> parent present
        assert ashliman.attach_target("333A", known) == "333"
        assert ashliman.attach_target("47E", known) == "47A"      # parent absent -> lowest sibling
        assert ashliman.attach_target("433C", known) == "433B"
        assert ashliman.attach_target("20", known) == "20A"       # base absent, children present
        assert ashliman.attach_target("778J", known) == "778"
        assert ashliman.attach_target("676", known) is None       # orphan: no relative indexed

    def test_probe_filename_and_atu_range(self):
        assert ashliman._probe_filename("510A") == "type0510A.html"
        assert ashliman._probe_filename("1") == "type0001.html"
        assert ashliman._probe_filename("779J*") == "type0779J.html"   # star never in a filename
        assert ashliman._atu_range("676") is True
        assert ashliman._atu_range("3000") is False                    # Christiansen migratory legend


class TestAtuRegions:
    def test_canonical_folds_variants(self):
        assert atu_regions.canonical("Indian") == "India"          # bare Indian = India in Uther
        assert atu_regions.canonical("cf. Japanese") == "Japanese"  # drop compare prefix
        assert atu_regions.canonical(".Australian") == "Australian"  # strip stray dot
        assert atu_regions.canonical("") == ""                      # blank token → dropped
        # A citation fragment is kept (not a people, so unmapped → "—" bucket).
        assert atu_regions.canonical("No. 65") == "No. 65"
        assert atu_regions.region(atu_regions.canonical("No. 65")) == ""

    def test_region_mapping(self):
        assert atu_regions.region("Uzbek") == "Central Asia"
        assert atu_regions.region("Egyptian") == "Near East"
        assert atu_regions.region("Yakut") == "Siberia"
        assert atu_regions.region("Latvian") == "Europe"
        assert atu_regions.region("Nonexistent") == ""

    def test_parse_and_group(self):
        text = "Finnish: Aaa 1; German, Dutch: Bbb 2; Uzbek: Ccc 3; No. 9: junk"
        parsed = atu_regions.parse(text)
        # The citation fragment "No. 9" is kept as an unmapped entry, not dropped.
        assert [(e["people"], e["region"]) for e in parsed] == [
            ("Finnish", "Europe"), ("German", "Europe"),
            ("Dutch", "Europe"), ("Uzbek", "Central Asia"), ("No. 9", "")]
        grouped = atu_regions.group_by_region(parsed)
        assert grouped["total"] == 5
        assert [(r["region"], r["count"]) for r in grouped["regions"]] == [
            ("Europe", 3), ("Central Asia", 1), ("—", 1)]

    def test_unmapped_sorts_to_dash_bucket_last(self):
        grouped = atu_regions.group_by_region(atu_regions.parse("Klingon: X 1; German: Y 2"))
        assert grouped["regions"][-1]["region"] == "—"

    def test_period_glued_peoples_split_when_both_mapped(self):
        # A period-glued pair of mapped peoples becomes two entries sharing the cite.
        parsed = atu_regions.parse("Palestinian. Iraqi: El-Shamy 2004")
        assert [(e["people"], e["region"], e["cite"]) for e in parsed] == [
            ("Palestinian", "Near East", "El-Shamy 2004"),
            ("Iraqi", "Near East", "El-Shamy 2004")]
        # Not split when a half is unmapped: "No. 65" stays one "—" entry.
        assert [e["people"] for e in atu_regions.parse("No. 65: x")] == ["No. 65"]

    def test_build_legend_counts_types(self):
        types = [
            {"attestations_grouped": atu_regions.group_by_region(
                atu_regions.parse("German: A 1; Uzbek: B 2"))},
            {"attestations_grouped": atu_regions.group_by_region(
                atu_regions.parse("German: C 3"))},
        ]
        legend = atu_regions.build_legend(types)
        assert legend["German"] == {"count": 2, "region": "Europe"}
        assert legend["Uzbek"] == {"count": 1, "region": "Central Asia"}

    def test_mojibake_dictionary_repairs(self):
        f = trilogy._fix_mojibake
        M = trilogy._MOJIBAKE
        assert f(f"Delarue/Ten{M}ze") == "Delarue/Ténèze"          # French è
        assert f(f"K{M}hler/Bolte") == "Köhler/Bolte"              # German ö
        assert f(f"Pol{M}vka") == "Polívka"                        # Czech í
        assert f(f"O{M}Sullivan") == "O'Sullivan"                  # apostrophe
        assert f(f"Ga{M}par{M}kov{M}") == "Gašparíková"            # multi-diacritic
        assert f(f"pp. 998{M}1005") == "pp. 998–1005"              # page range → en-dash
        assert f(f"Nos. 400A{M}C") == "Nos. 400A–C"                # type-id range → en-dash
        assert f(f"400A{M}400D") == "400A–400D"                    # type-id range (both sides)
        assert f(f"III, XI{M}XXVIII, IV") == "III, XI–XXVIII, IV"  # roman-numeral range
        assert f(f"(S. R{M}hle)") == "(S. R�hle)"                  # lost diacritic in a name → marker
        assert f(f"unknown {M} name") == "unknown � name"          # unrecognised → marker
        # a standalone leading Ó lost too: the longer key heals both mojibakes
        assert f(f"Irish: {M} S{M}illeabh{M}in") == "Irish: Ó Súilleabháin"
        assert f(f"S{M}illeabh{M}in") == "Súilleabháin"     # bare form still handled
        assert f(f"Nos. *1855B{M}*1855F") == "Nos. *1855B–*1855F"  # starred type range
        assert f(f"168a{M}b") == "168a–b"                   # lowercase type range
        # dropped leading capital (no marker), repaired only as a whole word
        assert f("Yakut: rgis 1967") == "Yakut: Ėrgis 1967"
        assert f("Serbian: ajkanovi 1927") == "Serbian: Čajkanović 1927"
        assert f("Bergisch 1900") == "Bergisch 1900"               # substring never touched

    def test_wikidata_parse_bindings(self):
        from motifs.sources import atu_wikidata as wd
        rows = [
            {"atu": {"value": "510A"}, "item": {"value": "http://www.wikidata.org/entity/Q11841"},
             "isType": {"value": "true"}, "l_de": {"value": "Aschenputtel"}, "l_ru": {"value": "Золушка"},
             "arts": {"value": "en=https://en.wikipedia.org/wiki/Cinderella|ru=https://ru.wikipedia.org/wiki/Золушка"},
             "cats": {"value": "Grimms' fairy tales=KHM 21|The Types of the Folktale=510A"}},
            {"atu": {"value": "510A"}, "item": {"value": "http://www.wikidata.org/entity/Q999"},
             "isType": {"value": "false"},
             "arts": {"value": "en=https://en.wikipedia.org/wiki/Katie_Woodencloak"}},
            {"atu": {"value": "99999"}, "item": {"value": "x"}, "isType": {"value": "true"},
             "l_en": {"value": "Not in our index"}},
        ]
        out = wd.parse_bindings(rows, {"510A"})
        assert "99999" not in out                                   # unknown id dropped
        e = out["510A"]
        assert e["names"]["de"] == ["Aschenputtel"] and e["names"]["ru"] == ["Золушка"]
        assert e["wikidata"] == "Q11841"                            # from the tale-type item
        titles = {(w["lang"], w["title"]) for w in e["wikipedia"]}
        assert {("en", "Cinderella"), ("ru", "Золушка"), ("en", "Katie Woodencloak")} <= titles
        assert e["concordances"] == {"KHM": ["21"]}                 # prefix stripped; AaTh==id dropped
        assert wd._norm_atu("283В*") == "283B*"                     # Cyrillic homoglyph folded

    def test_list_filters_by_division(self, monkeypatch):
        monkeypatch.setattr(svc, "_records", lambda idx: [
            {"id": "300", "chapter": "Magic", "division": "Supernatural Adversaries", "name": "a"},
            {"id": "1200", "chapter": "Jokes", "division": "Stories About A Fool", "name": "b"},
        ])
        monkeypatch.setattr(svc, "_list_item", lambda idx, r: {"id": r["id"]})
        out = svc.list_motifs("atu", division="Supernatural Adversaries")
        assert [i["id"] for i in out["items"]] == ["300"] and out["total"] == 1

    def test_search_matches_former_name_and_ids(self, monkeypatch):
        monkeypatch.setattr(svc, "_records", lambda idx: [
            {"id": "1891", "name": "Catching a Rabbit",
             "former_name": "The Great Rabbit-Catch", "former_ids": ["1891A*", "1893"]},
            {"id": "300", "name": "The Dragon-Slayer", "former_name": "", "former_ids": []},
        ])
        monkeypatch.setattr(svc, "_list_item", lambda idx, r: {"id": r["id"]})
        def hits(q):
            return [i["id"] for i in svc.list_motifs("atu", q=q)["items"]]
        assert hits("great rabbit") == ["1891"]      # by the pre-2004 name
        assert hits("1891a*") == ["1891"]            # by an old number
        assert hits("dragon") == ["300"]             # ordinary name match still works

    def test_sub_division_hierarchy(self):
        rows = [
            {"atu_id": "1", "chapter": "Animal", "division": "Wild Animals 1-99",
             "sub_division": "The Clever Fox (Other Animal) 1-69", "tale_name": "x", "tale_type": "y"},
            {"atu_id": "300", "chapter": "Magic", "division": "Supernatural Adversaries 300-399",
             "sub_division": "", "tale_name": "x", "tale_type": "y"},
        ]
        types = trilogy._parse_atu(rows, {}, {})[0]
        by = {t["id"]: t for t in types}
        assert by["1"]["sub_division"] == "The Clever Fox (Other Animal)"
        assert by["1"]["sub_division_range"] == [1, 69]
        assert by["300"]["sub_division"] == "" and by["300"]["sub_division_range"] is None
        subs = trilogy._atu_subdivisions(types)
        assert subs == [{"chapter": "Animal Tales", "division": "Wild Animals",
                         "name": "The Clever Fox (Other Animal)", "start": 1, "end": 69, "count": 1}]

    def test_list_filters_by_sub_division(self, monkeypatch):
        monkeypatch.setattr(svc, "_records", lambda idx: [
            {"id": "1", "sub_division": "The Clever Fox (Other Animal)", "name": "a"},
            {"id": "70", "sub_division": "Other Wild Animals", "name": "b"},
        ])
        monkeypatch.setattr(svc, "_list_item", lambda idx, r: {"id": r["id"]})
        out = svc.list_motifs("atu", sub_division="Other Wild Animals")
        assert [i["id"] for i in out["items"]] == ["70"] and out["total"] == 1

    def test_repair_atu_name(self):
        r = trilogy._repair_atu_name
        # a clean label splits at the first sentence period
        assert r("The Theft of Fish", "A fox steals.") == ("The Theft of Fish", "A fox steals.")
        # abbreviation Trilogy wrongly split on ("St.") — reunited, not a boundary
        assert r("St", "Peter and the Nuts. A tale.") == ("St. Peter and the Nuts", "A tale.")
        # "etc" is not an abbreviation: at depth 0 its period ends the title (type 572*)
        assert r("The Striking Axe, etc", "A man acts.") == ("The Striking Axe, etc", "A man acts.")
        # decimal inside a motif code is not a boundary; the seam re-inserts no space
        assert r("The Great Kettle [X1030", "1]. Cf.") == ("The Great Kettle [X1030.1]", "Cf.")
        # the label ends where a (previously …) apparatus block begins — it drops to
        # the summary, even for a period-class title
        assert r("The Animal Bride (previously The Mouse [Cat, Frog, etc", "] as Bride). A father decides.") \
            == ("The Animal Bride", "(previously The Mouse [Cat, Frog, etc.] as Bride). A father decides.")
        # (Including … Type N) merge-note (capital I + a type id) also ends the label
        assert r("The String of Chickens (Including the previous Type 1876", ") A husband acts.") \
            == ("The String of Chickens", "(Including the previous Type 1876.) A husband acts.")
        # a word-variant "(Jackal)" is not apparatus and does not cut
        assert r("The Fox (Jackal) as Schoolmaster", "He teaches.") \
            == ("The Fox (Jackal) as Schoolmaster", "He teaches.")
        # lowercase prose "(including …)" is not a merge-note and does not cut
        assert r("Wedding Feast (including honey)", "Guests arrive.") \
            == ("Wedding Feast (including honey)", "Guests arrive.")
        # quoted catch-phrase title: prose after the closing quote drops to the summary
        assert r("'The Barn is Burning!' A master acts", "") == ("'The Barn is Burning!'", "A master acts")
        # declarative quoted title whose closing quote Trilogy orphaned into the summary
        assert r("'No", "' A king rules.") == ("'No.'", "A king rules.")
        # doubled apostrophe (source artifact) collapsed before quote detection
        assert r("The Hen ''What was I''", "A note.") == ("The Hen 'What was I'", "A note.")
        # balanced one-line title with no plot period → reunited, summary empty
        assert r("St", "Christopher and the Christ Child") == ("St. Christopher and the Christ Child", "")
        # unclosed '(' with no apparatus keyword and no depth-0 period: no boundary
        # exists, so Trilogy's raw column split is preserved untouched
        assert r("A Tale (see note", "with no ending period") \
            == ("A Tale (see note", "with no ending period")

    def test_apply_title_override(self):
        o = trilogy._apply_title_override
        # run-on label cut at the curated title; leaked tail folds to the summary front
        assert o("66A*", "The Fox Buys himself a Pipe and goes into the barn to smoke",
                 "The hay begins to burn.") \
            == ("The Fox Buys himself a Pipe", "and goes into the barn to smoke. The hay begins to burn.")
        # all-in-name case (summary empty): the whole tail becomes the summary
        assert o("860", "Nuts of 'Ay ay ay!' A princess is offered nuts.", "") \
            == ("Nuts of 'Ay ay ay!'", "A princess is offered nuts.")
        # an id not in the table, or a name that doesn't start with the label: untouched
        assert o("510A", "Cinderella", "A young woman.") == ("Cinderella", "A young woman.")
        assert o("66A*", "Some other name", "x") == ("Some other name", "x")

    def test_heal_accents(self):
        h = trilogy._heal_accents
        # accented letters flattened to a bare apostrophe, from the curated list
        assert h("The Hard-hearted Fianc'e") == "The Hard-hearted Fiancée"
        assert h("M'nchhausen Tales") == "Münchhausen Tales"
        assert h("Sleeping Beauty (Dornr'schen)") == "Sleeping Beauty (Dornröschen)"
        assert h("the two fianc'es meet") == "the two fiancées meet"   # inflection via substring
        # a genuine apostrophe (possessive / old-French elision) is left untouched
        assert h("The Emperor's New Clothes") == "The Emperor's New Clothes"
        assert h("Peau d'asne") == "Peau d'asne"                       # archaic spelling, not damage
        assert h("no apostrophe here") == "no apostrophe here"

    def test_extract_defining_motifs(self):
        e = trilogy._extract_defining_motifs
        # code trailing the label → extracted, name cleaned
        assert e("115", "The Hungry Fox Waits [J2066.1]", "The fox is told.") \
            == ("The Hungry Fox Waits", "The fox is told.", ["J2066.1"])
        # multiple codes in one bracket → a list
        assert e("210", "Rooster and Needle [B296, F1025]", "They journey.") \
            == ("Rooster and Needle", "They journey.", ["B296", "F1025"])
        # code leading the summary after apparatus → extracted, summary tidied
        assert e("1336A", "Not Recognizing Own Reflection",
                 "(previously Man does not Recognize [Mirror]) [J1791.7]. A man.") \
            == ("Not Recognizing Own Reflection",
                "(previously Man does not Recognize [Mirror]). A man.", ["J1791.7"])
        # an inline code (after prose, no heading code) is left in place
        assert e("931A", "Parricide", "A man kills his parents [Q211.1, S22]") \
            == ("Parricide", "A man kills his parents [Q211.1, S22]", [])
        # a quote-class end-of-summary code is extracted only for the curated ids
        assert e("1446", "'Let them Eat Cake!'", "The queen answered [J2227]") \
            == ("'Let them Eat Cake!'", "The queen answered", ["J2227"])
        # a word-variant aside "[Bear]" is not a code and is never extracted
        assert e("2D", "The New Tail [Bear]", "A wolf turns.") \
            == ("The New Tail [Bear]", "A wolf turns.", [])

    def test_extract_apparatus(self):
        a = trilogy._extract_apparatus
        # leading name + merge note stripped; name → former_name, ids → former_ids
        assert a("(previously The Buried Tail). (Including the previous Type 64.) A fox flees.") \
            == ("A fox flees.", "The Buried Tail", ["64"])
        # a trailing "(Previously Type X)" note is stripped, its id kept
        assert a("A man demands payment [J1551.10]. (Previously Type 1804A.)") \
            == ("A man demands payment [J1551.10].", "", ["1804A"])
        # a block embedded mid-sentence stays in place, but its id is still collected
        assert a("Fools carry light in a sieve (previously Type 1245*) or a sack.") \
            == ("Fools carry light in a sieve (previously Type 1245*) or a sack.", "", ["1245*"])
        # "cf. Type Y" inside a block is a cross-ref, not a former id
        assert a("(Previously Type 1*, cf. Type 223.) A fox pretends to be dead.") \
            == ("A fox pretends to be dead.", "", ["1*"])
        # a nested paren in the old name is handled by the balanced scanner
        assert a("(previously The Doves (etc.)). A thrush teaches.") \
            == ("A thrush teaches.", "The Doves (etc.)", [])
        # "Types X and Y" list; "(including honey)" prose is not apparatus
        assert a("(Including the previous Types 924A and 924B.) A feast (including honey).") \
            == ("A feast (including honey).", "", ["924A", "924B"])
        # an unbalanced "(previously …" (source defect) is left untouched
        assert a("(previously Learned by Keeping Inn (Bath-house). A couple adopts.") \
            == ("(previously Learned by Keeping Inn (Bath-house). A couple adopts.", "", [])

    def test_atu_aliases_and_stubs(self):
        def d(i, nm, tt):
            return {"atu_id": i, "chapter": "x", "division": "d", "tale_name": nm, "tale_type": tt}
        rows = [
            d("1699A", "Cf. Type 1699", ""),                          # a stub → alias + dropped
            d("1699", "Clever X", "(previously Type 1699A.) A plot."),  # its target
            d("223", "Live Type", "A plot."),                         # a live type…
            d("1", "The Theft", "(Previously Type 223.) A fox."),     # …referenced as previously
        ]
        types, aliases = trilogy._parse_atu(rows, {}, {})
        ids = {t["id"] for t in types}
        assert "1699A" not in ids               # stub is dropped as a page
        assert aliases["1699A"] == "1699"        # …and folded into the redirect map
        assert "223" not in aliases              # a live type is never aliased away
        assert "1699A" not in aliases.values()   # (target is the current id, not the stub)

    def test_atu_inline_aath_concordance(self, monkeypatch):
        atu_types = [
            {"id": "330", "name": "The Smith and the Devil", "concordances": {"AaTh": ["330A"]}},
            {"id": "531", "name": "The Clever Horse", "concordances": {}},
        ]
        by = {t["id"]: t for t in atu_types}
        monkeypatch.setattr(svc.store, "cached", lambda key, factory: factory())
        monkeypatch.setattr(svc, "_records", lambda idx: atu_types if idx == "atu" else [])
        monkeypatch.setattr(svc, "_by_id", lambda idx: by if idx == "atu" else {})
        monkeypatch.setattr(svc, "_link", lambda idx, mid: {
            "index": idx, "id": mid, "exists": mid in by, "name": by.get(mid, {}).get("name", "")})
        out = svc._resolve_atu_inline(["531", "330A", "999"])
        assert out[0]["id"] == "531" and out[0]["exists"] and "aath" not in out[0]  # real ATU id
        assert out[1]["id"] == "330" and out[1]["aath"] == "330A"                   # remapped via concordance
        assert out[2]["id"] == "999" and out[2]["missing_reason"] == "aath"         # orphan AaTh number

    def test_merge_atu_relations(self):
        # 300: appears + cited -> both; 314: cited only (with aath); 301A: appears only
        ref = [
            {"index": "atu", "id": "300", "exists": True, "name": "A"},
            {"index": "atu", "id": "314", "exists": True, "name": "C", "aath": "532"},
        ]
        out = svc._merge_atu_relations(["301A", "300"], ref)
        rels = [(r["rel"], r["id"]) for r in out]
        # ⇔ (both) first, then ascending by number
        assert rels == [("both", "300"), ("appears", "301A"), ("cited", "314")]
        assert next(r for r in out if r["id"] == "314")["aath"] == "532"

    def test_summary_html_linkifies(self, monkeypatch):
        monkeypatch.setattr(svc, "_by_id",
                            lambda idx: {"B261": {}, "S222": {}} if idx == "tmi"
                            else {"400": {}, "537": {}, "510A": {}, "510B": {}})
        out = svc._atu_summary_html("War [B261] then Type 400, Cf. Type 537; also X999 and Type 999. Tom & Jerry")
        assert 'data-index="tmi" data-id="B261"' in out
        assert 'data-index="atu" data-id="400"' in out and 'data-index="atu" data-id="537"' in out
        assert "X999" in out and 'data-id="X999"' not in out   # unknown motif → plain text
        assert 'data-id="999"' not in out                      # unknown type → plain text
        assert "&amp;" in out                                  # prose is escaped
        # a "Types N and M" list (not just comma-separated) linkifies every member
        out2 = svc._atu_summary_html("See esp. Types 510A and 510B.")
        assert 'data-id="510A"' in out2 and 'data-id="510B"' in out2
        # "J1141ff" ('and following') links the base motif, keeps the ff as text
        monkeypatch.setattr(svc, "_by_id",
                            lambda idx: {"B261": {}} if idx == "tmi" else {})
        out3 = svc._atu_summary_html("the judgements [B261ff]")
        # the motif-only bracket is unwrapped; base motif links, 'ff' stays as text
        assert 'data-id="B261"' in out3 and "[" not in out3 and out3.endswith("ff</p>")
        # a motif range ("S222'S226", mojibake apostrophe) reads as "S222–S226": both
        # endpoints link, the dash is restored, and the motif-only bracket is unwrapped
        monkeypatch.setattr(svc, "_by_id",
                            lambda idx: {"S222": {}, "S226": {}} if idx == "tmi" else {})
        out4 = svc._atu_summary_html("sold to the devil [S222'S226].")
        assert 'data-id="S222"' in out4 and 'data-id="S226"' in out4
        assert "–" in out4 and "'" not in out4 and "[" not in out4

    def test_summary_blocks_wraps_enumeration_as_ordered_list(self, monkeypatch):
        monkeypatch.setattr(svc, "_by_id", lambda idx: {})
        # A "(1)…(N)" run becomes preamble + <ol>; the markers turn into the list
        # numbering and every bit of item text (incl. apparatus) is kept.
        out = svc._atu_summary_html("Exists in forms: (1) first form. (2) second one. "
                                    "(3) third (Previously Type 9*.)")
        assert "<ol" in out and out.count("<li>") == 3
        assert '<p class="motif-text">Exists in forms:</p>' in out
        assert "<li>first form.</li>" in out and "(Previously Type 9*.)" in out
        assert "(1)" not in out and "(3)" not in out          # markers → numbering
        # a lone / non-sequential marker is NOT a list — stays inline as text
        plain = svc._atu_summary_html("On the (7) th day only.")
        assert "<ol" not in plain and "(7)" in plain and plain.startswith('<p class="motif-text">')

    def test_summary_blocks_multiple_lists_and_trailing_text(self, monkeypatch):
        monkeypatch.setattr(svc, "_by_id", lambda idx: {})
        # Several runs (each restarting at "(1)") each become their own <ol>, with
        # the prose between them kept in a paragraph (period-joined items).
        multi = svc._atu_summary_html(
            "Heads: (1) alpha. (2) beta. Then a turn of events. "
            "Tails: (1) gamma. (2) delta.")
        assert multi.count("<ol") == 2
        assert "<li>alpha.</li>" in multi and "<li>gamma.</li>" in multi
        # the inter-run prose survives (glued to the run's last item, losslessly)
        assert "Then a turn of events." in multi
        # A comma-joined list (single sentence) peels its trailing prose into a
        # following paragraph, so the last item doesn't swallow the rest.
        trail = svc._atu_summary_html(
            "He meets: (1) a wolf, (2) a fish, (3) a river. "
            "God answers and he is rewarded.")
        assert trail.count("<ol") == 1 and trail.count("<li>") == 3
        assert "<li>a river.</li>" in trail
        assert '<p class="motif-text">God answers and he is rewarded.</p>' in trail

    def test_clean_tmi_ref(self):
        assert svc._clean_tmi_ref("*A2211.1") == "A2211.1"
        assert svc._clean_tmi_ref("A1313.3.1.") == "A1313.3.1"
        # A Roman/stick "I" in a dotted sub-segment is the digit 1.
        assert svc._clean_tmi_ref("A700.I") == "A700.1"
        assert svc._clean_tmi_ref("A724.I.I.") == "A724.1.1"
        assert svc._clean_tmi_ref("I72A") == "I72A"  # chapter letter left alone

    def test_tradition_distribution_groups_by_region(self):
        cat = {
            "6.2.3.1": {"name": "Abor", "areal_path": [["6", "TIBET"], ["6.2", "NE INDIA"]]},
            "6.2.3.2": {"name": "Adi", "areal_path": [["6", "TIBET"]]},
            "26.1.1.1": {"name": "Ainu", "areal_path": [["26", "EAST ASIA"]]},
        }
        dist = svc._berezkin_tradition_distribution(["6.2.3.1", "6.2.3.2", "26.1.1.1"], cat)
        assert dist["total"] == 3
        assert dist["regions"][0] == {"region": "TIBET", "count": 2, "traditions": ["Abor", "Adi"]}
        assert {r["region"] for r in dist["regions"]} == {"TIBET", "EAST ASIA"}


class TestBerezkinIndexHtml:
    def test_parse_index_and_chapters(self):
        html = """
        <ul><p>A. СОЛНЦЕ И ЛУНА</p>
          <li><a target="right" href="a1.html">A1. Древнее солнце. .19.21.</a></li>
          <ul><b>K. ПРИКЛЮЧЕНИЯ I(1): ДЕЯНИЯ ГЕРОЕВ</b>
          <li><a target="right" href="b1.html">B1. Двое создателей. A50. .13.</a></li>
          <li><a href="other.htm">junk</a></li>
        </ul>
        """
        motifs, chapters = berezkin.parse_index(html)
        # headers in both <p> and <b>, names may carry colons/parens
        assert chapters == {"A": "СОЛНЦЕ И ЛУНА", "K": "ПРИКЛЮЧЕНИЯ I(1): ДЕЯНИЯ ГЕРОЕВ"}
        assert [m["id"] for m in motifs] == ["A1", "B1"]

    def test_definition(self):
        html = '<p class="NormalLin">A1. Древнее солнце.</p><p class="NormalLis"> Краткое определение. </p>'
        assert berezkin.parse_definition(html) == "Краткое определение."


# ---------------------------------------------------------------------------
# Trilogy parsing
# ---------------------------------------------------------------------------

class TestTrilogy:
    def test_parse_tmi(self):
        rows = [
            {"id": "A1.1", "chapter_id": "A", "chapter_name": "Myths", "motif_name": "Sun-God",
             "notes": "n", "level": "3", "level_2": "A1", "level_3": "A1.1"},
            {"id": "NA", "motif_name": "skip"},
        ]
        out = trilogy._parse_tmi(rows)
        assert len(out) == 1
        assert out[0]["id"] == "A1.1"
        assert out[0]["parent"] == "A1"
        assert out[0]["chapter"] == "A"

    def test_parse_tmi_strips_notes_bleed(self):
        # A736.1.1's notes run on into serialized later rows ("<code>. †<code>.").
        rows = [{"id": "A736.1.1", "chapter_id": "A", "motif_name": "x", "level": "4",
                 "notes": "Real note. --Eskimo: Thompson 6; (Chaco): Mé"
                          "A736.1.2. †A736.1.2. Sun-brother. India: Thompson-Balys."}]
        out = trilogy._parse_tmi(rows)
        assert out[0]["notes"] == "Real note. --Eskimo: Thompson 6; (Chaco): Mé"

    def test_parse_tmi_keeps_genuine_dagger_crossref(self):
        rows = [{"id": "A736.1.3", "chapter_id": "A", "motif_name": "x", "level": "4",
                 "notes": "(Cf. †A736.1.1.). --India: Thompson-Balys."}]
        out = trilogy._parse_tmi(rows)
        assert out[0]["notes"] == "(Cf. †A736.1.1.). --India: Thompson-Balys."

    def test_notes_splits_definition_and_cultures(self):
        out = tmi_notes.parse_notes(
            "The creator is half man and half woman. "
            "--*Lang Myth I 200f. --Greek: Eisler 396; Egyptian: Maspero 141; "
            "Indian (Hindu): Keith 75.")
        assert out["definition"] == "The creator is half man and half woman."
        assert out["cultures"]["Greek"] == ["Eisler 396"]
        assert out["cultures"]["Egyptian"] == ["Maspero 141"]
        assert out["cultures"]["Indian (Hindu)"] == ["Keith 75"]
        assert "*Lang Myth I 200f" in out["references"]

    def test_notes_no_definition_when_starts_with_citation(self):
        out = tmi_notes.parse_notes("Greek: Fox 4; India: *Thompson-Balys.")
        assert out["definition"] == ""
        assert out["cultures"]["Greek"] == ["Fox 4"]
        assert out["cultures"]["India"] == ["*Thompson-Balys"]

    def test_notes_no_definition_when_starts_with_culture_less_citation(self):
        # A citation without a culture label heads the bibliography, so _BIB_START
        # skips it — but a bibliographic locus (No. 7, roman+page, ff., a bare
        # 'Author Work Page') marks it as a citation, not a definition (J21.22,
        # A941.1, A139.7). The whole note is then bibliography.
        out = tmi_notes.parse_notes("Nouvelles de Sens No. 7; Irish myth: *Cross; Italian: Rotunda.")
        assert out["definition"] == ""
        assert "Nouvelles de Sens No. 7" in out["references"]
        assert out["cultures"]["Irish myth"] == ["*Cross"]
        assert tmi_notes.parse_notes(
            "Malten Jahrb. d. kaiserlichen deutschen archäologischen Inst. XXIX 185.")["definition"] == ""
        assert tmi_notes.parse_notes("Gaster Thespis 211, 389, 397.")["definition"] == ""
        # A real prose definition with an incidental number is NOT mistaken for a citation.
        assert tmi_notes.parse_notes(
            "At 300 miles all women miscarry.")["definition"] == "At 300 miles all women miscarry."

    def test_notes_trims_trailing_citation(self):
        # A citation glued onto the end of a prose definition is peeled into references.
        out = tmi_notes.parse_notes(
            "Captured person persuades his captor to fatten him. Wienert FFC LVI 52; Halm Aesop No. 231")
        assert out["definition"] == "Captured person persuades his captor to fatten him."
        assert "Halm Aesop No. 231" in out["references"]
        assert tmi_notes.parse_notes(
            "Braved the wolf, who tore his legs. Dh III 46.")["definition"] == "Braved the wolf, who tore his legs."
        # A trailing *prose* sentence — even a bare noun list, or prose that runs into
        # the citation without a full stop — is left intact.
        assert tmi_notes.parse_notes(
            "Seven thrones on top of one another. Stone, cedar, iron, gold. Gaster Thespis 135ff."
        )["definition"] == "Seven thrones on top of one another. Stone, cedar, iron, gold."
        assert tmi_notes.parse_notes(
            "They hear the reapers. Larks move, for they now know it will be done Pauli No. 683."
        )["definition"].endswith("it will be done Pauli No. 683.")

    def test_notes_force_bibliography_override(self):
        # A curated override treats the whole note as bibliography for a citation the
        # heuristic can't tell from prose (English-titled: 'The Review of Religion').
        cite = "Krappe The Review of Religion (1941)"
        assert tmi_notes.parse_notes(cite, "A112.1")["definition"] == ""      # overridden id
        assert cite in tmi_notes.parse_notes(cite, "A112.1")["references"]     # kept, not lost
        assert tmi_notes.parse_notes(cite, "ZZ99")["definition"] == cite       # other id: heuristic keeps it
        assert tmi_notes.parse_notes(cite)["definition"] == cite               # no id: unchanged

    def test_notes_culture_label_with_parenthetical(self):
        # A culture label with a sub-area in parens must still be a citation, not
        # leak into the definition (A1.2 'Grandfather As Creator').
        out = tmi_notes.parse_notes(
            "S. Am. Indian (Paressi): Métraux BBAE CXLIII (3) 359, (Guarayú): Métraux RMLP XXXIII 147.")
        assert out["definition"] == ""
        assert "S. Am. Indian (Paressi)" in out["cultures"]

    def test_notes_cf_propagates_across_the_whole_list(self):
        # A single 'Cf.' introduces the whole comma-list, so every ref is
        # "compare", not just the first (TMI Q227 regression).
        out = tmi_notes.parse_notes("(Cf. †Q286.1, †Q421.2, †Q428.3)")
        assert out["see_also"]["cf"] == ["Q286.1", "Q421.2", "Q428.3"]
        assert out["see_also"]["ref"] == []

    def test_notes_bare_dagger_is_see_also_not_cf(self):
        # A bare '†X' (no Cf.) is "see also"; a following 'Cf. †…' list is compare.
        out = tmi_notes.parse_notes("†A1. Cf. †B2, †C3")
        assert out["see_also"]["ref"] == ["A1"]
        assert out["see_also"]["cf"] == ["B2", "C3"]

    def test_notes_dagger_glued_to_citation_is_dropped(self):
        # A '†X' glued to a source as '… Ursule (†B211.20)' is a bibliographic
        # tag, not a cross-reference — it must not leak into see_also (B211.2.2).
        out = tmi_notes.parse_notes(
            "German: Grimm No. 60; French-Canadian: Gautier (†B211.20); Moreno: Esdras (†B211.15).")
        assert out["see_also"] == {"cf": [], "ref": []}

    def test_notes_cf_list_continues_across_and_and_range(self):
        # A 'Cf.' list stays "compare" across an 'and' connector, a range dash,
        # and a '[b]' footnote marker on the Cf.
        out = tmi_notes.parse_notes("Cf. [b] †A1--†A2 and †A3")
        assert out["see_also"]["cf"] == ["A1", "A2", "A3"]
        assert out["see_also"]["ref"] == []

    def test_notes_culture_label_with_hyphen_and_comma_list(self):
        # A multi-culture label with a hyphenated name must be recognised as a
        # citation, not leak into the definition (A13.4.1 'Snake As Creator').
        out = tmi_notes.parse_notes("Mono-Alu, Fauru, Buin: Wheeler 67.")
        assert out["definition"] == ""
        assert out["cultures"]["Mono-Alu, Fauru, Buin"] == ["Wheeler 67"]

    def test_notes_run_on_after_definition_keeps_prose(self):
        # A missing space gluing a label to the prose ('growing. Lithuanian:') must
        # not let the label swallow the sentence — the definition is preserved.
        out = tmi_notes.parse_notes(
            "Devil sows stones; God sends cold to prevent their growing. Lithuanian: Balys.")
        assert out["definition"] == "Devil sows stones; God sends cold to prevent their growing"

    def test_notes_culture_after_leading_xref(self):
        # A leading '(Cf. †…)' xref, once stripped, leaves a stray '.'; the culture
        # after it must still parse, not fall through to references (A15.3.1 'Inca').
        out = tmi_notes.parse_notes("(Cf. †A1.2.). Inca: Rowe BBAE CXLIII (2) 316.")
        assert out["cultures"] == {"Inca": ["Rowe BBAE CXLIII (2) 316"]}
        assert out["see_also"]["cf"] == ["A1.2"]

    def test_notes_extracts_see_also_and_cf(self):
        out = tmi_notes.parse_notes("Hero deceives the ogre. (Cf. †A116.2). See †K1611.")
        assert out["see_also"]["cf"] == ["A116.2"]
        assert out["see_also"]["ref"] == ["K1611"]

    def test_notes_extracts_inline_atu_types(self):
        out = tmi_notes.parse_notes("Wonder tale. *Types 403, 425, 480; BP I 42ff.")
        assert out["atu_inline"] == ["403", "425", "480"]

    def test_notes_empty(self):
        out = tmi_notes.parse_notes("")
        assert out == {"definition": "", "cultures": {}, "references": [],
                       "see_also": {"cf": [], "ref": []}, "atu_inline": []}

    def test_parse_tmi_attaches_parsed_note_fields(self):
        rows = [{"id": "A12", "chapter_id": "A", "motif_name": "x", "level": "2",
                 "notes": "Both male and female. --Greek: Eisler 396. (Cf. †A1.)"}]
        out = trilogy._parse_tmi(rows)[0]
        assert out["definition"] == "Both male and female."
        assert out["cultures"] == {"Greek": ["Eisler 396"]}
        assert out["see_also"]["cf"] == ["A1"]

    def test_notes_drops_prose_and_genre_noise(self):
        # A capitalised prose word before a colon whose "citation" carries no
        # source token is not a culture and must be dropped ('Answer', 'Decision').
        out = tmi_notes.parse_notes(
            "Greek: Frazer 12; Decision: he must guess the riddle correctly.")
        assert out["cultures"] == {"Greek": ["Frazer 12"]}
        # A genre label heading a real citation block is dropped by name.
        out = tmi_notes.parse_notes("Fable: Halm Aesop No. 173; BP III 290.")
        assert out["cultures"] == {}

    def test_culture_canonical_merges_alias_and_strips_sub(self):
        assert culture_dict.canonical("Icel.") == ("Icelandic", "")
        assert culture_dict.canonical("Africa (Angola)") == ("Africa", "Angola")
        assert culture_dict.canonical("England") == ("English", "")
        # A leading 'Cf.' compare-prefix is stripped, folding into the real culture.
        assert culture_dict.canonical("Cf. Greek") == ("Greek", "")
        assert culture_dict.canonical("Am. Indian.") == ("American Indian", "")

    def test_culture_legend_aggregates_aliases_regions_subs(self):
        motifs = [
            {"cultures": {"Icelandic": ["a"], "Greek": ["b"]}},
            {"cultures": {"Icel.": ["c"], "Africa (Angola)": ["d"], "Africa (Ekoi)": ["e"]}},
        ]
        legend = culture_dict.build_legend(motifs)
        assert legend["Icelandic"]["count"] == 2          # merged across alias
        assert legend["Icelandic"]["aliases"] == ["Icel."]
        assert legend["Icelandic"]["region"] == "Europe"
        assert legend["Africa"]["count"] == 1             # counted once per motif
        assert legend["Africa"]["subs"] == ["Angola", "Ekoi"]
        assert legend["Greek"]["region"] == "Europe"

    def test_tmi_chapters_map(self):
        motifs = [
            {"chapter": "A", "chapter_name": "Myths"},
            {"chapter": "A", "chapter_name": "Myths"},  # dup letter -> kept once
            {"chapter": "B", "chapter_name": "Animals"},
            {"chapter": "C", "chapter_name": ""},        # no name -> skipped
        ]
        assert trilogy._tmi_chapters(motifs) == {"A": "Myths", "B": "Animals"}

    def test_tmi_sort_key_parent_before_child_and_numeric(self):
        ids = ["A10", "A1.4", "A1", "A100", "C12.5.8", "A2", "C12.5"]
        ordered = sorted(ids, key=trilogy.tmi_sort_key)
        assert ordered == ["A1", "A1.4", "A2", "A10", "A100", "C12.5", "C12.5.8"]

    def test_finalize_tmi_repairs_defects(self):
        out = {m["id"]: m for m in trilogy._finalize_tmi([
            {"id": "A0", "name": "Creator", "level": 0, "parent": ""},
            {"id": "A0", "name": "Creator (alt)", "level": 0, "parent": ""},   # dup code
            {"id": "A52", "name": "Angels", "level": 1, "parent": "A0"},
            {"id": "A52.0.1", "name": "Orphan", "level": 0, "parent": ""},     # dotted, no parent
            {"id": "A100", "name": "Deity", "level": 0, "parent": ""},
            {"id": "A110", "name": "Origin", "level": 5, "parent": "A100"},    # odd source level
        ])}
        # duplicate code: first keeps it, second gets a letter sub-index; both flagged
        assert "A0" in out and "A0b" in out
        assert out["A0"]["duplicate"] and out["A0b"]["duplicate"] and out["A0b"]["code"] == "A0"
        # no synthetic grouping nodes
        assert "A52.0" not in out
        assert not any(m.get("synthetic") for m in out.values())
        # orphan reattached to the nearest existing ancestor; .0 chain level computed
        assert out["A52.0.1"]["parent"] == "A52"
        assert out["A52.0.1"]["level"] == 2  # A52 (source 1) + 1
        # ordinary motifs keep their source level verbatim (no recomputation)
        assert out["A110"]["level"] == 5
        # the duplicate source_level field is gone
        assert "source_level" not in out["A52.0.1"]

    def test_parse_atu_seq_orders_and_dedups(self):
        rows = [
            {"atu_id": "510A", "motif_order": "2", "motif": "R221"},
            {"atu_id": "510A", "motif_order": "1", "motif": "S31"},
            {"atu_id": "510A", "motif_order": "3", "motif": "S31"},  # dup
        ]
        assert trilogy._parse_atu_seq(rows) == {"510A": ["S31", "R221"]}

    def test_parse_atu_combines_sources(self):
        df = [{"atu_id": "510A", "chapter": "Magic", "division": "d", "tale_name": "Cinderella",
               "tale_type": "summary"}]
        seq = {"510A": ["S31"]}
        combos = {"510A": ["510B"]}
        out = trilogy._parse_atu(df, seq, combos)[0]
        assert out[0]["motifs"] == ["S31"]
        assert out[0]["combos"] == ["510B"]
        assert out[0]["name"] == "Cinderella"


# ---------------------------------------------------------------------------
# Berezkin bibliography
# ---------------------------------------------------------------------------

class TestBerezkinBibliography:
    BIBLIO = (
        '<p class="NormalMai">Elwin, Verrier</p>'
        '<p class="NormalYur1">1958a Myths of the North-East Frontier of India. Shillong. 448 p.</p>'
        '<p class="NormalYur1">1958b Second work.</p>'
        '<p class="NormalMai">Pechuël-Loesche, Eduard</p>'
        '<p class="NormalYur1">1907 Volkskunde von Loango. Stuttgart. 480 p.</p>'
        '<p class="NormalMai">Сем, Юрий Александрович</p>'
        '<p class="NormalYur1">1986 Первый.</p>'
        '<p class="NormalMai">Сем, Татьяна Юрьевна</p>'
        '<p class="NormalYur1">1986 Второй.</p>'
    )

    def test_parse_bibliography_author_year_grouping(self):
        b = bbib.parse_bibliography(self.BIBLIO)
        assert b["Elwin 1958a"]["author"] == "Elwin, Verrier"
        assert b["Elwin 1958a"]["title"].startswith("Myths of the North-East")
        assert "Elwin 1958b" in b
        assert b["Pechuël-Loesche 1907"]["title"].startswith("Volkskunde")

    def test_parse_bibliography_flags_homonyms(self):
        # same surname+year for two authors: kept once, collision recorded
        assert bbib.parse_bibliography(self.BIBLIO)["Сем 1986"].get("homonyms")

    def test_parse_refs_filters_and_keeps_hyphen(self):
        refs = bbib.parse_refs("Pechuël-Loesche 1907: 135; Meier 1909 в Luomala 1940: 39; ATU 294")
        pairs = [(a, y) for _, a, y in refs]
        assert ("Pechuël-Loesche", "1907") in pairs      # hyphenated surname kept whole
        assert ("Meier", "1909") in pairs and ("Luomala", "1940") in pairs  # nested "в" -> both
        assert all(a != "ATU" for a, _ in pairs)

    def _index(self, *entries):
        idx = {}
        for key, author, year in entries:
            idx.setdefault(year[:4], []).append((key, bbib._fold(author), bbib._year_norm(year)))
        return idx

    def test_resolve_status(self):
        index = self._index(("Pechuël-Loesche 1907", "Pechuël-Loesche, Eduard", "1907"),
                            ("Сем 1986", "Сем, Юрий Александрович", "1986"),
                            ("Сем 1986#2", "Сем, Татьяна Юрьевна", "1986"))
        assert bbib._resolve("Pechuël-Loesche", "1907", index)["status"] == "resolved"
        assert bbib._resolve("Сем", "1986", index)["status"] == "ambiguous"
        assert bbib._resolve("Nobody", "1999", index)["status"] == "unresolved"

    def test_resolve_diacritics(self):
        index = self._index(("Galvão 1949", "Galvão, Eduardo", "1949"))
        # citation carries a plain-letter surname; the bibliography has diacritics
        assert bbib._resolve("Galvao", "1949", index)["status"] == "resolved"

    def test_resolve_latin_cyrillic_year_suffix(self):
        # citation "2011b" (Latin b) resolves the bibliography's Cyrillic "2011б"
        index = self._index(("Ганиева 2011а", "Ганиева, Ф.А.", "2011а"),
                            ("Ганиева 2011б", "Ганиева, Ф.А.", "2011б"))
        r = bbib._resolve("Ганиева", "2011b", index)
        assert r["status"] == "resolved" and r["key"] == "Ганиева 2011б"

    def test_parse_bibliography_keeps_colliding_multiauthor_work(self):
        # two different works share surname+year; a citation of the second author
        # (Kroeber) must resolve, not be shadowed by the solo Dorsey entry.
        html = (
            '<p class="NormalMai">Dorsey, George Amos</p>'
            '<p class="NormalYur1">1903 The Arapaho Sun Dance. Chicago.</p>'
            '<p class="NormalMai">Dorsey, George A., and Alfred Luis Kroeber</p>'
            '<p class="NormalYur1">1903 Traditions of the Arapaho. Chicago.</p>'
        )
        b = bbib.parse_bibliography(html)
        assert "Dorsey 1903" in b and "Dorsey 1903 #2" in b
        index = {"1903": [(k, bbib._fold(e["author"]), bbib._year_norm(e["year"]))
                          for k, e in b.items()]}
        assert bbib._resolve("Kroeber", "1903", index)["status"] == "resolved"

    def test_parse_attestations_region_and_cf(self):
        idx = bbib.region_index({"19": "Меланезия", "11": "Бантуязычная Африка"})
        html = ('<p class="NormalMai">Меланезия. Апатани [сюжет]: Elwin 1958a: 38.</p>'
                '<p class="NormalMai">(Ср. Бантуязычная Африка. Фьоти [сюжет]: Pechuël-Loesche 1907: 135)</p>')
        regs = bbib.parse_attestations(html, idx)
        assert regs[0]["area_code"] == "19" and regs[0]["cf"] is False
        assert regs[0]["cites"][0]["surname"] == "Elwin" and regs[0]["cites"][0]["year"] == "1958a"
        assert regs[1]["cf"] is True and regs[1]["area_code"] == "11"  # comparative "(Ср. …)" block

    def test_region_of_normalizes_dash_case_and_order(self):
        idx = bbib.region_index({"34": "Южная Сибирь – Монголия", "20": "Полинезия – Микронезия"})
        # hyphen instead of en-dash
        assert bbib._region_of("Южная Сибирь - Монголия. Алтайцы: X 1990", idx)[0] == "34"
        # reversed word order
        assert bbib._region_of("Микронезия – Полинезия. Палау: Y 1991", idx)[0] == "20"


# Cross-walk
# ---------------------------------------------------------------------------

class TestCrosswalk:
    def test_atu_tmi_and_berezkin(self):
        seq = {"510A": ["S31", "R221"]}
        tmi_ids = {"S31", "R221"}
        berezkin_motifs = [{"id": "A39A", "atu_refs": ["294"]}, {"id": "Z1", "atu_refs": []}]
        atu_ids = {"510A", "294"}
        cw = crosswalk.build(seq, tmi_ids, berezkin_motifs, atu_ids)
        assert cw["atu_to_tmi"]["510A"] == ["S31", "R221"]
        assert cw["tmi_to_atu"]["S31"] == ["510A"]
        assert cw["berezkin_to_atu"] == {"A39A": ["294"]}
        assert cw["atu_to_berezkin"]["294"] == ["A39A"]
        assert cw["linked_tmi_count"] == 2

    def test_defining_maps_and_alias_resolution(self):
        # Defining motifs give a separate ATU<->TMI link (kept apart from the
        # constituent one) — only codes present in the TMI index are linked.
        seq = {"115": ["J2066"]}
        tmi_ids = {"J2066", "J2066.1", "Q2"}
        atu_ids = {"115", "480"}
        atu_defining = {"115": ["J2066.1"], "480": ["Q2", "GONE"]}  # GONE not in TMI
        # A Berezkin ref to a pre-2004 number is resolved through the alias map.
        berezkin_motifs = [{"id": "M1", "atu_refs": ["403C"]}]
        aliases = {"403C": "480"}
        cw = crosswalk.build(seq, tmi_ids, berezkin_motifs, atu_ids,
                             atu_defining, aliases)
        assert cw["atu_to_tmi_defining"]["115"] == ["J2066.1"]
        assert cw["atu_to_tmi_defining"]["480"] == ["Q2"]      # GONE filtered out
        assert cw["tmi_to_atu_defining"]["J2066.1"] == ["115"]
        # constituent and defining stay distinct
        assert cw["tmi_to_atu"]["J2066"] == ["115"]
        assert "J2066" not in cw["tmi_to_atu_defining"]
        # old number 403C resolves to the current type 480 via the alias map
        assert cw["atu_to_berezkin"]["480"] == ["M1"]

    def test_inferred_closure_uses_low_fanout_pivots_with_provenance(self):
        # atu_seq: A1 has its own motif; T1..T3 all use the SAME motif m2 (m2 is
        # high fan-out → 3 types); T9 uses m3 (low fan-out → 1 type).
        atu_seq = {"A1": ["mx"], "T1": ["m2"], "T2": ["m2"], "T3": ["m2"], "T9": ["m3"]}
        tmi_ids = {"m", "m2", "m3", "md", "mx"}
        atu_ids = {"A1", "T1", "T2", "T3", "T9"}
        defining = {"A1": ["md"]}                       # A1's ~1:1 defining motif
        berezkin = [
            {"id": "BX", "tmi_refs": ["m"], "atu_refs": ["A1"]},  # bridges A1 <-> m (closure A)
            {"id": "BY", "tmi_refs": ["m3"]},                     # -> T9 via m3 (closure D, ok)
            {"id": "BZ", "tmi_refs": ["m2"]},                     # m2 in 3 types -> excluded (fan-out)
        ]
        cw = crosswalk.build(atu_seq, tmi_ids, berezkin, atu_ids, defining)
        inf = cw["inferred"]
        # A: ATU A1 <-> TMI m, bridged by Berezkin BX — stored both ways.
        assert {"index": "tmi", "id": "m", "via_index": "berezkin", "via_id": "BX"} in inf["atu"]["A1"]
        assert {"index": "atu", "id": "A1", "via_index": "berezkin", "via_id": "BX"} in inf["tmi"]["m"]
        # C: Berezkin BX <-> TMI md via A1's defining motif.
        assert any(e["id"] == "md" and e["via_id"] == "A1" for e in inf["berezkin"]["BX"])
        # D: Berezkin BY <-> ATU T9 via the low-fan-out motif m3.
        assert {"index": "atu", "id": "T9", "via_index": "tmi", "via_id": "m3"} in inf["berezkin"]["BY"]
        # fan-out guard: m2 sits in 3 types (> cap), so BZ gets no inferred link.
        assert "BZ" not in inf["berezkin"]
        assert cw["inferred_count"] == len({tuple(sorted(((s, k), (e["index"], e["id"]))))
                                            for s, byid in inf.items()
                                            for k, es in byid.items() for e in es})

    def test_inline_note_and_summary_maps_are_symmetric(self):
        # Both inline relations are stored in both directions so an edge shows on
        # both indexes' pages.
        tmi_ids = {"J2066", "K550", "Z81"}
        atu_ids = {"115", "122"}
        # A TMI note cites "Type N": 115 straight through, 900 is a pre-2004 number
        # remapped via the AaTh concordance, 9999 is an orphan (no edge).
        tmi_notes = {"K550": ["122", "900"], "J2066": ["115"], "Z81": ["9999"]}
        aath_to_atu = {"900": ["122"]}
        # ATU summaries name TMI codes in prose (with the "ff" shorthand on 122).
        atu_summaries = {"115": "The fox waits [J2066] in vain.",
                         "122": "Escape by naming K550ff; cf. missing X999."}
        cw = crosswalk.build({}, tmi_ids, [], atu_ids, {}, {},
                             tmi_notes, aath_to_atu, atu_summaries)
        # notes: forward + inverse
        assert cw["tmi_to_atu_note"]["K550"] == ["122"]         # 900→122 dedups with direct 122
        assert cw["tmi_to_atu_note"]["J2066"] == ["115"]
        assert "Z81" not in cw["tmi_to_atu_note"]                # orphan 9999 dropped
        assert cw["atu_to_tmi_note"]["122"] == ["K550"]
        assert cw["atu_to_tmi_note"]["115"] == ["J2066"]
        # summaries: forward + inverse; ff shorthand resolves to the base code
        assert cw["atu_to_tmi_summary"]["115"] == ["J2066"]
        assert cw["atu_to_tmi_summary"]["122"] == ["K550"]      # K550ff → K550; X999 not in TMI
        assert cw["tmi_to_atu_summary"]["J2066"] == ["115"]
        assert cw["tmi_to_atu_summary"]["K550"] == ["122"]

    def test_summary_range_expands_to_index_members(self):
        # A summary cites a motif *range* with a mojibake en-dash ("J1759'J1763").
        # The crosswalk expands it to every TMI id the range spans (not just the two
        # endpoints), so the range's constituent members link back to the type.
        tmi_ids = {"J1759", "J1760", "J1761", "J1763", "J1799", "K1"}
        atu_summaries = {"1319": "one thing is mistaken for another [J1759'J1763]."}
        cw = crosswalk.build({}, tmi_ids, [], {"1319"}, atu_summaries=atu_summaries)
        # every in-index member of [J1759, J1763] is credited, in Thompson order;
        # J1799 sits past the upper endpoint and is left out.
        assert cw["atu_to_tmi_summary"]["1319"] == ["J1759", "J1760", "J1761", "J1763"]
        assert cw["tmi_to_atu_summary"]["J1761"] == ["1319"]     # interior member links back
        assert "J1799" not in cw["tmi_to_atu_summary"]

    def test_summary_range_upper_endpoint_may_omit_letter(self):
        # "X1030'1036" — the upper endpoint drops the letter; it inherits X.
        tmi_ids = {"X1030", "X1031", "X1036", "X1200"}
        cw = crosswalk.build({}, tmi_ids, [], {"1960E"},
                             atu_summaries={"1960E": "a huge farm [X1030'1036]."})
        assert cw["atu_to_tmi_summary"]["1960E"] == ["X1030", "X1031", "X1036"]

    def test_direct_berezkin_tmi(self):
        # tmi_refs (from mapsofmyths) become a direct Berezkin<->TMI bridge; a ref
        # is cleaned (*, trailing dot) and kept only if it exists in the TMI index.
        berezkin = [{"id": "A2A", "tmi_refs": ["*A720.1", "A1052.", "Z999"]}]
        cw = crosswalk.build({}, {"A720.1", "A1052"}, berezkin, set())
        assert cw["berezkin_to_tmi"] == {"A2A": ["A720.1", "A1052"]}   # Z999 dropped (not in TMI)
        assert cw["tmi_to_berezkin"]["A720.1"] == ["A2A"]
        assert cw["tmi_to_berezkin"]["A1052"] == ["A2A"]


# Textual parallels (heuristic suggestion layer)
# ---------------------------------------------------------------------------

class TestParallels:
    def test_build_finds_unlinked_lookalikes(self):
        bz = [{"id": "B1", "name": "The Clever Fox", "definition": "The fox is clever."},
              {"id": "B9", "name": "The Distant Star", "definition": "A distant star shines."}]
        tmi = [{"id": "K1", "name": "Clever Fox", "definition": "A fox is clever."},
               {"id": "K2", "name": "Clever Wolf", "definition": "A wolf is clever."},
               {"id": "Z9", "name": "Distant Star", "definition": "A distant star."}]
        atu = [{"id": "1", "name": "The Clever Fox", "summary": "A clever fox tricks a wolf."},
               {"id": "9", "name": "The Distant Star", "summary": "A distant star shines above."}]
        # ATU 1 <-> TMI K1 is already a recorded cross-walk link -> must be subtracted.
        cw = {"atu_to_tmi": {"1": ["K1"]}, "tmi_to_atu": {"K1": ["1"]}}
        par = parallels.build(bz, tmi, atu, cw)
        assert par is not None
        adj = par["adjacency"]
        # Berezkin B1 is parallel to both ATU 1 and TMI K1 (neither linked to B1).
        b1 = {(e["index"], e["id"]) for e in adj["berezkin"].get("B1", [])}
        assert ("atu", "1") in b1 and ("tmi", "K1") in b1
        # The already-linked ATU 1 <-> K1 pair is excluded from the suggestions,
        # but the unlinked Berezkin parallel to K1 remains.
        k1 = {(e["index"], e["id"]) for e in adj["tmi"].get("K1", [])}
        assert ("atu", "1") not in k1
        assert ("berezkin", "B1") in k1
        # A three-way parallel is detected, with the two missing legs flagged.
        tri = [t for t in par["triangles"]
               if t["berezkin"] == "B1" and t["tmi"] == "K1" and t["atu"] == "1"]
        assert tri and set(tri[0]["missing"]) == {"berezkin-tmi", "berezkin-atu"}
        # Every adjacency entry is tagged with a confidence tier, and the counts are
        # reported per tier (both A and B reach the page layer).
        assert all(e["tier"] in {"A", "B"} for e in adj["berezkin"]["B1"])
        assert "berezkin_atu_A" in par["counts"] and "berezkin_atu_B" in par["counts"]


class TestReasonedParallels:
    def test_groups_are_wellformed(self):
        from motifs import reasoned_parallels as rp
        seen = set()
        for g in rp.GROUPS:
            assert g["confidence"] in {"high", "medium"}
            assert g["title"] and g["note"]
            idxs = {i for i, _ in g["members"]}
            assert idxs <= {"berezkin", "tmi", "atu"}
            assert len(idxs) >= 2 and len(g["members"]) >= 2     # spans ≥2 indexes
            for m in g["members"]:
                assert m not in seen, f"member {m} appears in two groups"
                seen.add(m)
        adj = rp.adjacency()
        assert adj["tmi"].get("A812")          # a known member maps back to its group
        assert set(adj) == {"berezkin", "tmi", "atu"}

    def test_member_ids_exist_when_built(self):
        from motifs import reasoned_parallels as rp
        if not store.load_index("tmi"):
            pytest.skip("indexes not built")
        for index in ("berezkin", "tmi", "atu"):
            data = store.load_index(index)
            ids = {r["id"] for r in data["types" if index == "atu" else "motifs"]}
            for g in rp.GROUPS:
                for i, mid in g["members"]:
                    if i == index:
                        assert mid in ids, f"{index}:{mid} not in index"


# ---------------------------------------------------------------------------
# Read service (against a tiny on-disk database)
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny_db(tmp_path, monkeypatch):
    from settings import settings

    monkeypatch.setattr(settings, "motifs_dir", tmp_path)
    store.clear_cache()

    (tmp_path / "berezkin.json").write_text(json.dumps({
        "label": "Berezkin", "chapters": {"A": "СОЛНЦЕ И ЛУНА"},
        "homepage": "http://areasofmyths.com",
        "areas": {"11": "Бантуязычная Африка", "12": "Западная Африка"},
        "motifs": [
            {"id": "A39A", "chapter": "A", "name": "Двенадцать месяцев", "areas": [11, 12],
             "see_also": [], "atu_refs": ["294"], "definition": "def", "page": "a39a.html"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    # Run the raw rows through the real build-time repair so the stored data
    # mirrors production (corrected parent/level, disambiguated duplicates).
    def _tmi(id, name, level, parent, chapter="S"):
        return {"id": id, "chapter": chapter, "chapter_name": "Cruelty",
                "name": name, "notes": "", "level": level, "parent": parent}

    tmi_motifs = trilogy._finalize_tmi([
        _tmi("S0", "Cruelty", 0, ""),
        _tmi("S30", "Cruel relatives", 1, "S0"),
        _tmi("S31", "Cruel stepmother", 2, "S30"),
        _tmi("S31.1", "Stepmother kills", 3, "S31"),
        # Orphan: empty parent though the id clearly nests under S31 (id-trim).
        _tmi("S31.0.1", "Orphan detail", 0, ""),
        # Duplicate code reused for two distinct motifs.
        _tmi("S33", "Dup one", 2, "S30"),
        _tmi("S33", "Dup two", 2, "S30"),
    ])
    (tmp_path / "tmi.json").write_text(json.dumps({
        "label": "Thompson (TMI)", "chapters": {"S": "Cruelty"}, "motifs": tmi_motifs,
    }), encoding="utf-8")
    (tmp_path / "atu.json").write_text(json.dumps({
        "label": "ATU tale types",
        "types": [
            {"id": "294", "chapter": "Magic", "division": "d", "name": "The Months", "summary": "s",
             "motifs": ["S31"], "combos": []},
            {"id": "510A", "chapter": "Magic", "division": "d", "name": "Cinderella", "summary": "s",
             "motifs": ["S31"], "combos": []},
        ],
    }), encoding="utf-8")
    (tmp_path / "crosswalk.json").write_text(json.dumps({
        "atu_to_tmi": {"294": ["S31"], "510A": ["S31"]},
        "tmi_to_atu": {"S31": ["294", "510A"]},
        "berezkin_to_atu": {"A39A": ["294"]},
        "atu_to_berezkin": {"294": ["A39A"]},
    }), encoding="utf-8")
    (tmp_path / "semantic_parallels.json").write_text(json.dumps({
        "adjacency": {
            "tmi": {"S31": [{"index": "berezkin", "id": "A39A", "sim": 0.81, "also_lexical": False}]},
            "berezkin": {"A39A": [{"index": "tmi", "id": "S31", "sim": 0.81, "also_lexical": False}]},
        }}), encoding="utf-8")
    (tmp_path / "meta.json").write_text(json.dumps({"counts": {"berezkin": 1, "tmi": 1, "atu": 2}}), encoding="utf-8")
    yield tmp_path
    store.clear_cache()


class TestBuildMotifsModes:
    def _setup(self, tmp_path, monkeypatch):
        from settings import settings
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "motifs.json").write_text(json.dumps(
            {"berezkin": {"enabled": False}, "trilogy": {"enabled": True}}))
        monkeypatch.setattr(settings, "config_dir", config_dir)
        monkeypatch.setattr(settings, "motifs_dir", tmp_path / "out")
        store.clear_cache()

    def test_default_rebuilds_from_cache_force_only_refetches(self, tmp_path, monkeypatch):
        self._setup(tmp_path, monkeypatch)
        fetched = []  # records the `force` (re-fetch) flag passed to the source

        def fake_tmi(cfg, *, force=False):
            fetched.append(force)
            return {"motifs": []}

        def fake_atu(cfg, *, force=False):
            return {"types": []}, {}

        monkeypatch.setattr(bm.trilogy, "build_tmi", fake_tmi)
        monkeypatch.setattr(bm.trilogy, "build_atu", fake_atu)

        bm.build_motifs()            # rebuild from cache (no re-fetch)
        assert fetched == [False]
        bm.build_motifs()            # rebuilds again — no skip-if-built
        assert fetched == [False, False]
        bm.build_motifs(force=True)  # re-fetch
        assert fetched == [False, False, True]


class TestService:
    def test_semantic_parallels_resolved(self, tiny_db):
        # The precomputed BGE-M3 layer is resolved to display links with similarity.
        sp = svc.get_motif("tmi", "S31")["semantic_parallels"]
        assert len(sp) == 1
        assert sp[0]["index"] == "berezkin" and sp[0]["id"] == "A39A"
        assert sp[0]["sim"] == 0.81 and sp[0]["name"]  # resolved against the real record

    def test_semantic_parallels_copied_from_committed(self, tmp_path, monkeypatch):
        # When the output copy is absent, the committed data file is copied in.
        from settings import settings
        data_dir = tmp_path / "committed"
        data_dir.mkdir()
        (data_dir / store.SEMANTIC_PARALLELS_FILE).write_text(
            json.dumps({"adjacency": {"tmi": {"X1": [{"index": "atu", "id": "9", "sim": 0.7}]}}}))
        monkeypatch.setattr(store, "DATA_DIR", data_dir)
        monkeypatch.setattr(settings, "motifs_dir", tmp_path / "out")
        store.clear_cache()
        assert not store.semantic_parallels_path().exists()
        loaded = store.load_semantic_parallels()
        assert store.semantic_parallels_path().exists()          # copied into outputs
        assert loaded["adjacency"]["tmi"]["X1"][0]["id"] == "9"
        store.clear_cache()

    def test_indexes(self, tiny_db):
        idx = {i["index"]: i for i in svc.list_indexes()}
        assert set(idx) == {"berezkin", "tmi", "atu"}
        assert idx["atu"]["count"] == 2
        assert idx["berezkin"]["chapters"][0]["label"] == "A — Солнце и луна"  # all-caps -> sentence case

    def test_list_filter_and_search(self, tiny_db):
        res = svc.list_motifs("atu", q="cinderella")
        assert res["total"] == 1 and res["items"][0]["id"] == "510A"
        assert res["items"][0]["badge"] == "1 motifs"

    def test_berezkin_detail_links(self, tiny_db):
        d = svc.get_motif("berezkin", "A39A")
        assert d["areas"] == [
            {"id": 11, "name": "Бантуязычная Африка"},
            {"id": 12, "name": "Западная Африка"},
        ]
        assert d["definition"] == "def"
        assert d["source_url"] == "http://areasofmyths.com/a39a.html"
        atu = d["links"]["atu"]
        assert atu[0]["id"] == "294" and atu[0]["name"] == "The Months" and atu[0]["exists"] is True

    def test_atu_detail_resolves_tmi_and_berezkin(self, tiny_db):
        d = svc.get_motif("atu", "294")
        assert d["links"]["tmi"][0]["name"] == "Cruel stepmother"
        assert d["links"]["berezkin"][0]["id"] == "A39A"

    def test_tmi_detail_back_links(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        assert sorted(link["id"] for link in d["links"]["atu_related"]) == ["294", "510A"]

    def test_tmi_detail_exposes_structured_note_fields(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        assert isinstance(d["cultures"], list)      # enriched: label/region/citations
        assert isinstance(d["references"], list)    # enriched: {text, url?}
        assert "related" in d["links"] and "atu_related" in d["links"]

    def test_substantive_flag(self):
        assert svc._substantive({"notes": "x" * 150}) is True       # notes >= 150 bytes
        assert svc._substantive({"notes": "x" * 149}) is False
        assert svc._substantive({"cultures": {"a": [], "b": [], "c": []}}) is True  # >= 3 cultures
        assert svc._substantive({"notes": "x" * 40, "cultures": {"a": []}}) is False

    def test_tmi_detail_and_list_expose_substantive(self, tiny_db):
        assert "substantive" in svc.get_motif("tmi", "S31")
        items = svc.list_motifs("tmi", chapter="S")["items"]
        assert all("substantive" in it and "sub_subtree" in it for it in items)

    def test_tier_subtree_keeps_ancestors(self, tiny_db):
        # S31 has a substantive descendant chain; its L0 root S0 is subtree-relevant
        # even though S0 itself isn't substantive.
        relevant = svc._tier_relevant("sub")
        assert "S0" in relevant or not any(svc._substantive(r) for r in svc._records("tmi"))

    def test_list_motifs_tier_filter(self, tiny_db):
        base = svc.list_motifs("tmi")["total"]
        sub = svc.list_motifs("tmi", tier="sub")
        assert sub["total"] <= base
        assert all(it["substantive"] for it in sub["items"])  # every returned item matches the tier

    def test_stats_overview(self, tiny_db):
        s = svc.stats("tmi")
        assert s["totals"]["count"] == len(svc._records("tmi"))
        assert {c["label"] for c in s["composition"]} == {"substantive", "scaffold", "variation"}
        assert sum(c["count"] for c in s["composition"]) == s["totals"]["count"]
        assert [lv["level"] for lv in s["levels"]] == sorted(lv["level"] for lv in s["levels"])
        assert "regions" in s and "top_cultures" in s and "see_also_hubs" in s and "top_sources" in s
        # Berezkin and ATU have their own dashboards (cards + chart panels).
        for ix in ("berezkin", "atu"):
            st = svc.stats(ix)
            assert st["cards"] and st["panels"]
            assert all("id" in p and "title" in p for p in st["panels"])

    def test_notes_size_label(self):
        assert svc._notes_size("") == ""
        assert svc._notes_size("x" * 42) == "42b"
        assert svc._notes_size("x" * 99) == "99b"
        assert svc._notes_size("x" * 100) == "0.1k"   # >= 100 bytes -> kilobytes
        assert svc._notes_size("x" * 1259) == "1.2k"

    def test_resolve_citation_strips_leading_stars(self):
        assert svc._resolve_citation("*Thompson-Balys")["text"] == "Thompson-Balys"
        assert svc._resolve_citation("** Bolte-Polivka")["text"] == "Bolte-Polivka"
        assert svc._resolve_citation("Fox 4")["text"] == "Fox 4"  # unchanged

    def test_resolve_citation_links_known_works(self):
        # Against the built bibliography key (outputs/motifs/tmi_bibliography.json),
        # produced by the pipeline; skip when the DB hasn't been built.
        if not svc._bibliography_index():
            pytest.skip("bibliography key not built (run `mytho motifs`)")
        assert "archive.org" in svc._resolve_citation("BP III").get("url", "")
        assert "Fire" in svc._resolve_citation("**Frazer Fire").get("title", "")  # multi-work author
        assert "url" not in svc._resolve_citation("Nonexistentauthor 5")

    def test_tmi_breadcrumbs_broadest_first(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        assert [b["id"] for b in d["breadcrumbs"]] == ["S0", "S30"]
        assert all(b["exists"] for b in d["breadcrumbs"])

    def test_tmi_breadcrumbs_recovered_via_id_trim(self, tiny_db):
        # S31.0.1 has an empty parent; the chain is recovered by trimming the id.
        d = svc.get_motif("tmi", "S31.0.1")
        assert [b["id"] for b in d["breadcrumbs"]] == ["S0", "S30", "S31"]

    def test_tmi_direct_children_one_level(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        ids = {c["id"] for c in d["children"]}
        assert ids == {"S31.1", "S31.0.1"}  # direct children only, no synthetic node
        assert d["children_truncated"] is False
        assert not any(m.get("synthetic") for m in svc.list_motifs("tmi")["items"])

    def test_tmi_list_has_level_badge(self, tiny_db):
        by = {i["id"]: i for i in svc.list_motifs("tmi")["items"]}
        # recursive descendant count first, then level (S31 -> S31.1, S31.0.1)
        assert by["S31"]["badge"] == "2 · L2" and by["S31"]["level"] == 2
        assert by["S31.0.1"]["badge"] == "L3"  # leaf -> no count

    def test_tmi_list_level_filter(self, tiny_db):
        res = svc.list_motifs("tmi", chapter="S", level=0)
        assert [i["id"] for i in res["items"]] == ["S0"]  # only the root

    def test_tmi_list_flags_leaves(self, tiny_db):
        by = {i["id"]: i for i in svc.list_motifs("tmi")["items"]}
        assert by["S31"]["leaf"] is False        # has children (S31.1, S31.0.1)
        assert by["S31.1"]["leaf"] is True        # no children

    def test_tmi_duplicate_codes_distinguishable(self, tiny_db):
        by = {i["id"]: i for i in svc.list_motifs("tmi")["items"]}
        assert by["S33"]["duplicate"] and by["S33b"]["duplicate"]
        # both variants are independently openable with their own content
        assert svc.get_motif("tmi", "S33")["name"] == "Dup one"
        assert svc.get_motif("tmi", "S33b")["name"] == "Dup two"
        assert svc.get_motif("tmi", "S33b")["code"] == "S33"

    def test_missing_motif(self, tiny_db):
        assert svc.get_motif("atu", "nope") is None
