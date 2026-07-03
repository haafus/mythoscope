import json
import sys

# Other tests (test_corpus_*) stub `bs4` into sys.modules; the Berezkin parser
# needs the real library, so drop any stub and import the genuine module here.
sys.modules.pop("bs4", None)
import bs4  # noqa: E402,F401
import pytest  # noqa: E402

from motifs import build_motifs as bm  # noqa: E402
from motifs import crosswalk, store  # noqa: E402
from motifs.sources import berezkin, berezkin_bibliography as bbib, trilogy
from motifs.sources import culture_dict, tmi_notes
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
        assert m["tmi_refs"] == ["*A720.1"]
        assert m["atu_refs"] == ["565"]              # merged, de-duplicated
        assert m["traditions"] == ["6.2.3.1", "26.1.1.1"]


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
        by = {t["id"]: t for t in trilogy._parse_atu(rows, {}, {})}
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
        t = trilogy._parse_atu(rows, {}, {})[0]
        # digit–digit mojibake becomes an en-dash; a known scholar name is repaired
        # from the dictionary (Dähnhardt); the triple garbage never survives.
        assert t["references"] == "Krohn 1889, 46–54; Dähnhardt 1907ff. IV, 225–230"
        assert t["attestations"].startswith("Finnish: Rausmaa 1982ff. V, Nos. 1–6;")
        assert t["remarks"] == "Documented 1178 in the Roman de Renart."
        assert "ï¿½" not in (t["references"] + t["attestations"])

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
        # dropped leading capital (no marker), repaired only as a whole word
        assert f("Yakut: rgis 1967") == "Yakut: Ėrgis 1967"
        assert f("Serbian: ajkanovi 1927") == "Serbian: Čajkanović 1927"
        assert f("Bergisch 1900") == "Bergisch 1900"               # substring never touched

    def test_wikidata_parse_bindings(self):
        from motifs.sources import atu_wikidata as wd
        rows = [
            {"atu": {"value": "510A"}, "item": {"value": "http://www.wikidata.org/entity/Q11841"},
             "isType": {"value": "true"}, "l_de": {"value": "Aschenputtel"}, "l_ru": {"value": "Золушка"},
             "image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Cinderella.jpg"},
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
        assert e["image"].startswith("https://commons.wikimedia.org")   # http → https
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

    def test_sub_division_hierarchy(self):
        rows = [
            {"atu_id": "1", "chapter": "Animal", "division": "Wild Animals 1-99",
             "sub_division": "The Clever Fox (Other Animal) 1-69", "tale_name": "x", "tale_type": "y"},
            {"atu_id": "300", "chapter": "Magic", "division": "Supernatural Adversaries 300-399",
             "sub_division": "", "tale_name": "x", "tale_type": "y"},
        ]
        types = trilogy._parse_atu(rows, {}, {})
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

    def test_aft_example_tales(self):
        rows = [
            {"atu_id": "275", "tale_title": "The Hare and the Tortoise", "provenance": "Greece",
             "source": "Aesop", "notes": "NA", "text": "Once upon a time…"},
            {"atu_id": "275", "tale_title": "A Race", "provenance": "England",
             "source": "Jacobs 1894", "notes": "", "text": "…"},
            {"atu_id": "999", "tale_title": "", "provenance": "x", "source": "y", "text": "z"},
        ]
        tales = trilogy._parse_aft(rows)
        assert "999" not in tales                                     # no title → dropped
        assert [t["title"] for t in tales["275"]] == ["A Race", "The Hare and the Tortoise"]  # by provenance
        assert tales["275"][0]["provenance"] == "England"
        assert "text" not in tales["275"][0]                         # full text never stored
        assert tales["275"][1]["notes"] == ""                        # "NA" cleaned to empty
        # wired onto the type via _parse_atu
        rows_df = [{"atu_id": "275", "chapter": "Animal", "division": "Wild Animals 1-99",
                    "tale_name": "x", "tale_type": "y"}]
        t = trilogy._parse_atu(rows_df, {}, {}, tales)[0]
        assert len(t["tales"]) == 2

    def test_repair_atu_name_mid_bracket(self):
        r = trilogy._repair_atu_name
        # name truncated inside "[Cat, Frog, etc.]" — tail rejoined, re-split outside brackets
        n, s = r("The Animal Bride (previously The Mouse [Cat, Frog, etc", "] as Bride). A father decides.")
        assert n == "The Animal Bride (previously The Mouse [Cat, Frog, etc.] as Bride)"
        assert s == "A father decides."
        # a balanced name is left untouched
        assert r("The Theft of Fish", "A fox steals.") == ("The Theft of Fish", "A fox steals.")
        # source brackets themselves unbalanced (no depth-0 period) → left as-is, no mangling
        assert r("A (b (c", "no close here") == ("A (b (c", "no close here")

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
        rels = [(l["rel"], l["id"]) for l in out]
        # ⇔ (both) first, then ascending by number
        assert rels == [("both", "300"), ("appears", "301A"), ("cited", "314")]
        assert next(l for l in out if l["id"] == "314")["aath"] == "532"

    def test_summary_html_linkifies(self, monkeypatch):
        monkeypatch.setattr(svc, "_by_id",
                            lambda idx: {"B261": {}, "S222": {}} if idx == "tmi" else {"400": {}, "537": {}})
        out = svc._atu_summary_html("War [B261] then Type 400, Cf. Type 537; also X999 and Type 999. Tom & Jerry")
        assert 'data-index="tmi" data-id="B261"' in out
        assert 'data-index="atu" data-id="400"' in out and 'data-index="atu" data-id="537"' in out
        assert "X999" in out and 'data-id="X999"' not in out   # unknown motif → plain text
        assert 'data-id="999"' not in out                      # unknown type → plain text
        assert "&amp;" in out                                  # prose is escaped

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

    def test_notes_culture_label_with_parenthetical(self):
        # A culture label with a sub-area in parens must still be a citation, not
        # leak into the definition (A1.2 'Grandfather As Creator').
        out = tmi_notes.parse_notes(
            "S. Am. Indian (Paressi): Métraux BBAE CXLIII (3) 359, (Guarayú): Métraux RMLP XXXIII 147.")
        assert out["definition"] == ""
        assert "S. Am. Indian (Paressi)" in out["cultures"]

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
        out = trilogy._parse_atu(df, seq, combos)
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

    def test_direct_berezkin_tmi(self):
        # tmi_refs (from mapsofmyths) become a direct Berezkin<->TMI bridge; a ref
        # is cleaned (*, trailing dot) and kept only if it exists in the TMI index.
        berezkin = [{"id": "A2A", "tmi_refs": ["*A720.1", "A1052.", "Z999"]}]
        cw = crosswalk.build({}, {"A720.1", "A1052"}, berezkin, set())
        assert cw["berezkin_to_tmi"] == {"A2A": ["A720.1", "A1052"]}   # Z999 dropped (not in TMI)
        assert cw["tmi_to_berezkin"]["A720.1"] == ["A2A"]
        assert cw["tmi_to_berezkin"]["A1052"] == ["A2A"]


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
        assert "see_also" in d["links"] and "atu_related" in d["links"]

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
        assert [l["level"] for l in s["levels"]] == sorted(l["level"] for l in s["levels"])
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
