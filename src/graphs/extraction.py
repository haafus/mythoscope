import json

from llm import LLMProcessor

from .normalize import is_empty, norm_name


def extract_from_chunk(llm: LLMProcessor, chunk: str, prompts: dict) -> tuple[dict[str, list], bool]:
    """Extract all entity types from one chunk.

    Calls run sequentially (relations depend on extracted characters); chunk-level
    parallelism is handled by the caller, and the LLM client's rate governor is the
    real throttle. FatalLLMError / DailyLimitReached propagate to stop the run.

    Returns ``(results, complete)``. ``complete`` is False when any call returned
    None (a failed, non-fatal call) — the caller should skip caching such a chunk
    so it is retried on a later run rather than frozen as an empty result.
    """
    chars = llm.ask_json(prompts["beings"], chunk)
    relations_content = (
        f"DOCUMENT 1 (Text):\n{chunk}\n\n"
        f"DOCUMENT 2 (Characters):\n{json.dumps(chars or [], ensure_ascii=False)}"
    )
    rels = llm.ask_json(prompts["relations"], relations_content)
    locs = llm.ask_json(prompts["locations"], chunk)
    times = llm.ask_json(prompts["time"], chunk)

    complete = None not in (chars, rels, locs, times)
    results = {
        "beings": chars if isinstance(chars, list) else [],
        "relations": rels if isinstance(rels, list) else [],
        "locations": locs if isinstance(locs, list) else [],
        "times": times if isinstance(times, list) else [],
    }
    return results, complete


def _flatten_items(value):
    """Yield individual non-empty items from a scalar or list attribute value."""
    for item in value if isinstance(value, list) else [value]:
        if not is_empty(item):
            yield item


def deduplicate_entities(entities: list[dict]) -> list[dict]:
    """Merge entities sharing a normalized name, collecting distinct attribute values.

    Each attribute accumulates its distinct values (order-preserving) across all
    copies: one value stays scalar, several become a list. Linear in the number of
    values — set-based membership, no string concatenation or list scans.
    """
    grouped: dict[str, dict] = {}
    for ent in entities:
        name = ent.get("Name") or ent.get("name") or ent.get("NAME")
        if not name:
            continue
        norm = norm_name(name)
        rec = grouped.get(norm)
        if rec is None:
            rec = {"name": str(name).strip(), "attrs": {}}
            grouped[norm] = rec
        for key, value in ent.items():
            if norm_name(key) == "name":
                continue
            for item in _flatten_items(value):
                items, seen = rec["attrs"].setdefault(key, ([], set()))
                marker = item if isinstance(item, (str, int, float, bool)) else str(item)
                if marker not in seen:
                    seen.add(marker)
                    items.append(item)

    result = []
    for rec in grouped.values():
        out = {"Name": rec["name"]}
        for key, (items, _seen) in rec["attrs"].items():
            if items:
                out[key] = items[0] if len(items) == 1 else items
        result.append(out)
    return result


def deduplicate_relations(relations: list[dict]) -> list[dict]:
    unique_relations = set()
    deduplicated = []
    for rel in relations:
        subj = norm_name(rel.get("Subject", rel.get("subject", "")))
        obj = norm_name(rel.get("Object", rel.get("object", "")))
        r_type = norm_name(rel.get("Relation", rel.get("relation", "")))

        if not subj or not obj:
            continue

        identifier = (subj, obj, r_type)
        if identifier not in unique_relations:
            unique_relations.add(identifier)
            deduplicated.append(rel)

    return deduplicated
