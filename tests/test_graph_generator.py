import json

from graphs.graph_generator import (
    generate_ages_graph,
    generate_beings_graph,
    generate_realms_graph,
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

    def test_edge_carries_relation(self, tmp_path):
        generate_beings_graph(
            [{"Name": "A"}, {"Name": "B"}],
            [{"Subject": "A", "Object": "B", "Relation": "loves"}],
            tmp_path,
        )
        edges = _load(tmp_path / "beings.json")["edges"]
        assert edges == [{"source": "A", "target": "B", "relation": "loves"}]


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
