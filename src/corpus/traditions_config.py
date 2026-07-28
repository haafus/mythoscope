"""The region → tradition tree and fail-loud build-time validation.

`config/traditions.json` is the **single source of truth** (§2.9) for the region set: its
top-level keys ARE the regions (canon order = key order; regions.md §4 is the human reference).
Rename or reorder regions by editing that file alone — there is no second hardcoded copy to keep
in sync. This module owns only the *structural* validation that replaces the old silent `.get()`
degradations (§2.12): an ambiguous or dangling tradition reference **fails the build**.
"""

from __future__ import annotations

import json
from pathlib import Path


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

    - a tradition name appearing under two regions (ambiguous resolve);
    - a name used as both a region and a tradition (one flat namespace at resolve);
    - a book pointing at a tradition absent from the tree.

    The region set itself is not checked against a list — the tree's keys *are* the regions
    (source of truth §2.9); a mistyped region name shows as that name in the UI, never a silent
    grey default.
    """
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
