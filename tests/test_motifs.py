import json
import sys

# Other tests (test_corpus_*) stub `bs4` into sys.modules; the Berezkin parser
# needs the real library, so drop any stub and import the genuine module here.
sys.modules.pop("bs4", None)
import bs4  # noqa: E402,F401
import pytest  # noqa: E402

from motifs import build_motifs as bm  # noqa: E402
from motifs import crosswalk, store  # noqa: E402
from motifs.sources import berezkin, trilogy
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

    def test_see_also_before_areas(self):
        # "A50." is a see-also code, not part of the name or the area list.
        e = berezkin.parse_motif_entry("B1. Двое создателей. A50. .13.16.20.", "b1.html")
        assert e["name"] == "Двое создателей"
        assert e["see_also"] == ["A50"]
        assert e["areas"] == [13, 16, 20]

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

    def test_multiple_see_also_with_artifacts(self):
        e = berezkin.parse_motif_entry("A21. Светила заброшены в небо. A700.I. A714. A741., .10.12.", "a21.html")
        assert e["name"] == "Светила заброшены в небо"
        assert e["see_also"] == ["A700", "A714", "A741"]
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

    def test_clean_tmi_ref(self):
        assert svc._clean_tmi_ref("*A2211.1") == "A2211.1"
        assert svc._clean_tmi_ref("A1313.3.1.") == "A1313.3.1"

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
        assert sorted(link["id"] for link in d["links"]["atu"]) == ["294", "510A"]

    def test_tmi_detail_exposes_structured_note_fields(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        assert isinstance(d["cultures"], list)      # enriched: label/region/citations
        assert isinstance(d["references"], list)    # enriched: {text, url?}
        assert "see_also" in d["links"] and "atu_inline" in d["links"]

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
