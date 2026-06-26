import logging
from pathlib import Path

import networkx as nx

from json_utils import save_json

logger = logging.getLogger(__name__)

# Exact betweenness is O(V·E) and dominates graph generation on large books.
# Above this node count we sample pivots instead — it only feeds a display
# attribute (not node sizing), so an approximation is fine.
_BETWEENNESS_SAMPLE_K = 500


def _norm_key(key) -> str:
    return str(key).strip().lower().replace(" ", "").replace("_", "")


def _field(d: dict, *aliases):
    """First value whose key matches an alias (case/space/underscore-insensitive)."""
    targets = {_norm_key(a) for a in aliases}
    for k, v in d.items():
        if _norm_key(k) in targets:
            return v
    return None


def _norm_name(name) -> str:
    return str(name).strip().lower()


def _is_empty(value) -> bool:
    if value is None or value == "" or value == []:
        return True
    return isinstance(value, str) and value.strip().lower() == "nan"


def _split_multi(value) -> list[str]:
    """Split a list or a ';'/','-separated string into clean items."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [s.strip() for s in value.replace(";", ",").split(",") if s.strip()]
    return []


def _entity_index(entities: list[dict]) -> tuple[dict[str, str], dict[str, dict]]:
    """Build {normalized name -> display name} and {normalized name -> metadata}.

    Metadata keys are Title-Cased (to match the viewer's field names) and list
    values joined to a string.
    """
    display: dict[str, str] = {}
    metadata: dict[str, dict] = {}
    for ent in entities:
        name = _field(ent, "name")
        if name is None or not str(name).strip():
            continue
        norm = _norm_name(name)
        display.setdefault(norm, str(name).strip())
        meta = metadata.setdefault(norm, {})
        for key, value in ent.items():
            if _norm_key(key) == "name" or _is_empty(value):
                continue
            label = str(key).strip().title()
            if label not in meta:
                meta[label] = ", ".join(map(str, value)) if isinstance(value, list) else value
    return display, metadata


def _resolver(display: dict[str, str]):
    """Map a raw name to a canonical node id.

    Known entity names resolve to their display form; unseen names register their
    first-seen form so differently-cased duplicates collapse to a single node.
    """
    canon = dict(display)

    def resolve(name) -> str | None:
        text = str(name).strip()
        if not text:
            return None
        return canon.setdefault(_norm_name(text), text)

    return resolve


def _to_json(
    G: nx.Graph,
    display: dict[str, str],
    metadata: dict[str, dict],
    category: str,
    compute_betweenness: bool = True,
) -> dict:
    degrees = dict(G.degree())
    betweenness: dict = {}
    if compute_betweenness:
        k = _BETWEENNESS_SAMPLE_K if G.number_of_nodes() > _BETWEENNESS_SAMPLE_K else None
        betweenness = nx.betweenness_centrality(G, k=k, seed=0)

    min_deg = min(degrees.values()) if degrees else 0
    max_deg = max(degrees.values()) if degrees else 0

    def size(d):
        if max_deg == min_deg:
            return 4
        return 2 + (d - min_deg) * (6 / (max_deg - min_deg))

    nodes = []
    for node_id in G.nodes():
        norm = _norm_name(node_id)
        name = display.get(norm, node_id)
        node = {
            "id": node_id,
            "display_name": name,
            "Name": name,
            "Category": category if norm in display else "Other",
            "Degree": degrees.get(node_id, 0),
            "size": size(degrees.get(node_id, 0)),
        }
        if compute_betweenness:
            node["BetweennessCentrality"] = betweenness.get(node_id, 0.0)
        for label, value in metadata.get(norm, {}).items():
            if label not in node and not _is_empty(value):
                node[label] = value
        nodes.append(node)

    edges = [
        {"source": u, "target": v, "relation": d.get("relation", "")}
        for u, v, d in G.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}


def _save_graph(data: dict, output_path: Path) -> None:
    save_json(output_path, data, indent=2)
    logger.info(f"Graph saved: {output_path}")


def generate_beings_graph(beings_data: list, relations_data: list, output_dir: Path) -> None:
    display, metadata = _entity_index(beings_data)
    resolve = _resolver(display)

    G = nx.DiGraph()
    for name in display.values():
        G.add_node(name)

    edges_added = 0
    for rel in relations_data:
        subj = resolve(_field(rel, "subject"))
        obj = resolve(_field(rel, "object"))
        if not subj or not obj:
            continue
        G.add_node(subj)
        G.add_node(obj)
        G.add_edge(subj, obj, relation=_field(rel, "relation") or "")
        edges_added += 1

    if not edges_added:
        logger.warning("No valid relations for beings graph.")

    _save_graph(_to_json(G, display, metadata, "Character"), output_dir / "beings.json")


def generate_realms_graph(locations_data: list, output_dir: Path) -> None:
    display, metadata = _entity_index(locations_data)
    resolve = _resolver(display)

    G = nx.Graph()
    for name in display.values():
        G.add_node(name)

    for loc in locations_data:
        name = resolve(_field(loc, "name"))
        if not name:
            continue
        for neighbor_raw in _split_multi(_field(loc, "adjacent to", "adjacent")):
            neighbor = resolve(neighbor_raw)
            if neighbor and neighbor != name:
                G.add_node(neighbor)
                G.add_edge(name, neighbor, relation="adjacent to")

    _save_graph(_to_json(G, display, metadata, "Location"), output_dir / "realms.json")


def generate_ages_graph(times_data: list, output_dir: Path) -> None:
    """Build a timeline: epochs linked in first-appearance (narrative) order.

    ``times_data`` arrives in narrative order (aggregated in chunk order, dedup
    preserves first appearance), so consecutive entries form the sequence. No
    betweenness — on a chain it is positional and uninformative.
    """
    display, metadata = _entity_index(times_data)
    resolve = _resolver(display)

    sequence: list[str] = []
    seen: set[str] = set()
    for t in times_data:
        epoch = resolve(_field(t, "name"))
        if epoch and epoch not in seen:
            seen.add(epoch)
            sequence.append(epoch)

    G = nx.Graph()
    G.add_nodes_from(sequence)
    for a, b in zip(sequence, sequence[1:], strict=False):
        G.add_edge(a, b, relation="followed by")

    _save_graph(
        _to_json(G, display, metadata, "Epoch", compute_betweenness=False),
        output_dir / "ages.json",
    )
