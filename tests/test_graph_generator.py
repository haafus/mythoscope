import json

from graphs.graph_generator import (
    generate_ages_graph,
    generate_beings_graph,
    generate_realms_graph,
    top_mentioned_names,
)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestBeingsGraph:
    def test_isolated_character_kept(self, tmp_path):
        beings = [{"Name": "Lonely", "Description": "no links"}, {"Name": "A"}, {"Name": "B"}]
        relations = [{"Subject": "A", "Object": "B", "Relation": "knows"}]
        generate_beings_graph(beings, relations, tmp_path)
        ids = {n["id"] for n in _load(tmp_path / "beings.json")["nodes"]}
        assert "Lonely" in ids  # character without relations stays in the graph
        assert {"A", "B"} <= ids

    def test_relation_name_matches_being_case_insensitively(self, tmp_path):
        beings = [{"Name": "Moses", "Description": "prophet"}]
        relations = [{"Subject": "moses", "Object": "pharaoh", "Relation": "confronts"}]
        generate_beings_graph(beings, relations, tmp_path)
        nodes = {n["id"]: n for n in _load(tmp_path / "beings.json")["nodes"]}
        assert "moses" not in nodes  # collapsed into canonical "Moses"
        assert nodes["Moses"]["Description"] == "prophet"  # metadata attached despite casing
        assert nodes["Moses"]["Category"] == "Character"
        assert nodes["pharaoh"]["Category"] == "Other"  # not an extracted being

    def test_trailing_period_stripped_from_values_and_list_items(self, tmp_path):
        beings = [
            {"Name": "Thor", "Description": "God of thunder.",
             "Roles": ["Son of Odin.", "Protector of mankind."]},
        ]
        generate_beings_graph(beings, [], tmp_path)
        node = {n["id"]: n for n in _load(tmp_path / "beings.json")["nodes"]}["Thor"]
        assert node["Description"] == "God of thunder"                 # scalar: trailing dot gone
        assert node["Roles"] == "Son of Odin, Protector of mankind"    # list: per-item, no stray dots

    def test_na_placeholder_names_dropped(self, tmp_path):
        # LLM null-placeholders must not become nodes: neither as an entity name nor as a
        # relation endpoint (a relation with Object="N/A" otherwise spawns an "N/A" node).
        beings = [{"Name": "Thor"}, {"Name": "N/A"}, {"Name": "null"}]
        relations = [
            {"Subject": "Thor", "Object": "N/A", "Relation": "fights"},
            {"Subject": "none", "Object": "Thor", "Relation": "knows"},
        ]
        generate_beings_graph(beings, relations, tmp_path)
        data = _load(tmp_path / "beings.json")
        ids = {n["id"] for n in data["nodes"]}
        assert ids == {"Thor"}                      # N/A / null / none never materialise
        assert data["edges"] == []                  # both edges had a null endpoint → dropped

    def test_edge_carries_relation(self, tmp_path):
        generate_beings_graph(
            [{"Name": "A"}, {"Name": "B"}],
            [{"Subject": "A", "Object": "B", "Relation": "loves"}],
            tmp_path,
        )
        edges = _load(tmp_path / "beings.json")["edges"]
        assert edges == [{"source": "A", "target": "B", "relation": "loves"}]

    def test_empty_container_metadata_dropped(self, tmp_path):
        beings = [{"Name": "A", "Attributes": {}, "Epithets": [], "Roles": "  "}]
        generate_beings_graph(beings, [], tmp_path)
        node = {n["id"]: n for n in _load(tmp_path / "beings.json")["nodes"]}["A"]
        assert "Attributes" not in node  # empty dict must not survive as "{}"
        assert "Epithets" not in node and "Roles" not in node

    def test_dict_metadata_flattened_to_values(self, tmp_path):
        beings = [{"Name": "God", "Attributes": [
            "Merciful", {"Power": "Omnipotent", "Promise": "Faithful"}, "Just",
        ]}]
        generate_beings_graph(beings, [], tmp_path)
        node = {n["id"]: n for n in _load(tmp_path / "beings.json")["nodes"]}["God"]
        # dict elements contribute their values, not a raw "{'Power': ...}" fragment
        assert node["Attributes"] == "Merciful, Omnipotent, Faithful, Just"
        assert "{" not in node["Attributes"]


class TestTopMentioned:
    def test_picks_most_mentioned(self):
        unique = [{"Name": "Zeus"}, {"Name": "Hera"}, {"Name": "Minor"}]
        raw = ([{"Name": "Zeus"}] * 3) + ([{"Name": "Hera"}] * 2) + [{"Name": "Minor"}]
        assert top_mentioned_names(unique, raw, 2) == {"zeus", "hera"}

    def test_none_when_no_limit_or_already_small(self):
        unique = [{"Name": "A"}, {"Name": "B"}]
        assert top_mentioned_names(unique, unique, None) is None
        assert top_mentioned_names(unique, unique, 5) is None

    def test_keep_restricts_beings_graph(self, tmp_path):
        beings = [{"Name": "Zeus"}, {"Name": "Hera"}, {"Name": "Minor"}]
        relations = [
            {"Subject": "Zeus", "Object": "Hera", "Relation": "married"},
            {"Subject": "Zeus", "Object": "Minor", "Relation": "knows"},
        ]
        generate_beings_graph(beings, relations, tmp_path, keep={"zeus", "hera"})
        data = _load(tmp_path / "beings.json")
        assert {n["id"] for n in data["nodes"]} == {"Zeus", "Hera"}  # Minor dropped
        assert data["edges"] == [{"source": "Zeus", "target": "Hera", "relation": "married"}]


class TestRealmsGraph:
    def test_adjacency_edge(self, tmp_path):
        locs = [{"Name": "Egypt", "Adjacent To": "Canaan; Midian"}, {"Name": "Canaan"}]
        generate_realms_graph(locs, tmp_path)
        data = _load(tmp_path / "realms.json")
        pairs = {frozenset((e["source"], e["target"])) for e in data["edges"]}
        assert frozenset(("Egypt", "Canaan")) in pairs
        assert frozenset(("Egypt", "Midian")) in pairs


class TestAgesGraph:
    def test_links_consecutive_epochs_in_order(self, tmp_path):
        times = [{"Name": "Creation"}, {"Name": "Flood"}, {"Name": "Exodus"}]
        generate_ages_graph(times, tmp_path)
        data = _load(tmp_path / "ages.json")
        pairs = {frozenset((e["source"], e["target"])) for e in data["edges"]}
        assert pairs == {frozenset(("Creation", "Flood")), frozenset(("Flood", "Exodus"))}
        assert frozenset(("Creation", "Exodus")) not in pairs  # a chain, not a clique
        assert all(e["relation"] == "followed by" for e in data["edges"])

    def test_no_betweenness_and_keeps_metadata(self, tmp_path):
        generate_ages_graph([{"Name": "A", "KeyActors": "God"}, {"Name": "B"}], tmp_path)
        node = next(n for n in _load(tmp_path / "ages.json")["nodes"] if n["id"] == "A")
        assert "BetweennessCentrality" not in node
        assert node["Degree"] == 1
        assert node["Keyactors"] == "God"  # actor info stays as node metadata
