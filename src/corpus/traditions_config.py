"""The region → tradition tree: the 14 canon regions and fail-loud build-time validation.

`config/traditions.json` is the source of truth (§2.9): top-level keys are the 14 canon
regions (regions.md §4 order), each carrying its canon fields + only its texted traditions.
This module owns the canon list and the validation that replaces the old silent `.get()`
degradations (§2.12) — an unknown tradition or a non-canon region **fails the build**.
"""

from __future__ import annotations

import json
from pathlib import Path

# The 14 canon regions in canon order (regions.md §4, the out-of-Africa arc). The config's
# top-level keys must be exactly these (order and membership) — anything else fails the build.
CANON_REGIONS: tuple[str, ...] = (
    "Sub-Saharan Africa",
    "Near East & North Africa",
    "Europe",
    "Caucasus & Iran",
    "Inner Asia",
    "South Asia",
    "Mainland Southeast Asia",
    "East Asia",
    "Austronesia",
    "Papua & Australia",
    "Circumpolar North",
    "Native North America",
    "Mesoamerica & the Andes",
    "Lowland South America",
)


class TraditionsConfigError(ValueError):
    """A build-stopping problem in config/traditions.json or a book's tradition ref."""


def load_traditions_tree(config_dir: Path) -> dict:
    """Read config/traditions.json (the region → tradition tree). Missing/invalid JSON
    raises — the tree is a committed source of truth, not an optional cache."""
    path = Path(config_dir) / "traditions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def flat_traditions(tree: dict) -> dict[str, str]:
    """`{tradition_name: region_name}` — the resolve map the build and serve share."""
    out: dict[str, str] = {}
    for region, node in tree.items():
        for trad in (node.get("traditions") or {}):
            out[trad] = region
    return out


def validate_traditions(tree: dict, corpus_items: list[dict]) -> None:
    """Fail loud on any break the build must not silently degrade over (§2.12):

    - a top-level key that is not one of the 14 canon regions;
    - a tradition name appearing under two regions (ambiguous resolve);
    - a name used as both a region and a tradition (one flat namespace at resolve);
    - a book pointing at a tradition absent from the tree.
    """
    non_canon = [k for k in tree if k not in CANON_REGIONS]
    if non_canon:
        raise TraditionsConfigError(
            f"non-canon region key(s) {non_canon}; each must be one of the 14 canon regions"
        )

    tradition_region: dict[str, str] = {}
    for region, node in tree.items():
        for trad in (node.get("traditions") or {}):
            if trad in tradition_region:
                raise TraditionsConfigError(
                    f"tradition {trad!r} appears under both {tradition_region[trad]!r} and {region!r}"
                )
            tradition_region[trad] = region

    clash = sorted(set(tree) & set(tradition_region))
    if clash:
        raise TraditionsConfigError(f"name(s) used as both a region and a tradition: {clash}")

    missing = sorted(
        {it.get("tradition") for it in corpus_items if it.get("tradition")} - set(tradition_region)
    )
    if missing:
        raise TraditionsConfigError(f"book tradition(s) not in the tree: {missing}")
