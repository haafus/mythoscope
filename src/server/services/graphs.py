import json

from graphs.store import GRAPH_TYPES, graph_dir


def get_graph_data(text_id: str, graph_type: str) -> dict | None:
    if graph_type not in GRAPH_TYPES:
        return None
    try:
        # Shared with the build path + confined under graphs_dir: a hostile id
        # (e.g. '../../secret') is rejected rather than read from outside the tree.
        book_dir = graph_dir(text_id)
    except ValueError:
        return None
    json_path = book_dir / f"{graph_type}.json"
    if not json_path.exists():
        return None
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)
