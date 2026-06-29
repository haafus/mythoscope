import json
import sys

# Other tests (test_corpus_*) stub `bs4` into sys.modules; the Berezkin parser
# needs the real library, so drop any stub and import the genuine module here.
sys.modules.pop("bs4", None)
import bs4  # noqa: E402,F401
import pytest  # noqa: E402

from motifs import crosswalk, store  # noqa: E402
from motifs.sources import berezkin, trilogy
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

    def test_parse_area_headers_flags_comparative(self):
        html = (
            '<p class="NormalMai">( <b>Ср. Бантуязычная Африка.</b> [cmp]: src.</p>'
            '<p class="NormalMai"><b>Меланезия.</b> <u>Газель</u> [x]: y.</p>'
        )
        assert berezkin.parse_area_headers(html) == [
            ("Бантуязычная Африка", True),
            ("Меланезия", False),
        ]

    def test_build_area_legend_aligns_clean_motifs(self):
        # Parenthetical index (44) and comparative header are both excluded, so the
        # remaining indices align 1:1 with the remaining headers.
        motifs = [
            {"id": "M1", "area_seq": [[19, False], [21, False], [44, True]]},
            {"id": "M2", "area_seq": [[19, False], [21, False]]},
        ]
        headers = {
            "M1": [("Бантуязычная Африка", False), ("Меланезия", False), ("Cmp", True)],
            "M2": [("Бантуязычная Африка", False), ("Меланезия", False)],
        }
        assert berezkin.build_area_legend(motifs, headers) == {
            "19": "Бантуязычная Африка",
            "21": "Меланезия",
        }

    def test_build_area_legend_skips_count_mismatch(self):
        motifs = [{"id": "X", "area_seq": [[1, False], [2, False]]}]
        headers = {"X": [("OnlyOneHeader", False)]}
        assert berezkin.build_area_legend(motifs, headers) == {}


class TestBerezkinIndexHtml:
    def test_parse_index_and_chapters(self):
        html = """
        <ul><p>A. СОЛНЦЕ И ЛУНА</p>
          <li><a target="right" href="a1.html">A1. Древнее солнце. .19.21.</a></li>
          <li><a target="right" href="b1.html">B1. Двое создателей. A50. .13.</a></li>
          <li><a href="other.htm">junk</a></li>
        </ul>
        """
        motifs, chapters = berezkin.parse_index(html)
        assert chapters == {"A": "СОЛНЦЕ И ЛУНА"}
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
        "areas": {"11": "Бантуязычная Африка", "12": "Западная Африка"},
        "motifs": [
            {"id": "A39A", "chapter": "A", "name": "Двенадцать месяцев", "areas": [11, 12],
             "see_also": [], "atu_refs": ["294"], "definition": "def"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "tmi.json").write_text(json.dumps({
        "label": "Thompson (TMI)",
        "motifs": [{"id": "S31", "chapter": "S", "chapter_name": "Cruelty", "name": "Cruel stepmother",
                    "notes": "", "level": 2, "parent": "S30"}],
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


class TestService:
    def test_indexes(self, tiny_db):
        idx = {i["index"]: i for i in svc.list_indexes()}
        assert set(idx) == {"berezkin", "tmi", "atu"}
        assert idx["atu"]["count"] == 2
        assert idx["berezkin"]["chapters"][0]["label"] == "A — СОЛНЦЕ И ЛУНА"

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
        atu = d["links"]["atu"]
        assert atu[0]["id"] == "294" and atu[0]["name"] == "The Months" and atu[0]["exists"] is True

    def test_atu_detail_resolves_tmi_and_berezkin(self, tiny_db):
        d = svc.get_motif("atu", "294")
        assert d["links"]["tmi"][0]["name"] == "Cruel stepmother"
        assert d["links"]["berezkin"][0]["id"] == "A39A"

    def test_tmi_detail_back_links(self, tiny_db):
        d = svc.get_motif("tmi", "S31")
        assert sorted(link["id"] for link in d["links"]["atu"]) == ["294", "510A"]

    def test_missing_motif(self, tiny_db):
        assert svc.get_motif("atu", "nope") is None
