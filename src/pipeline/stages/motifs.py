"""The motifs stage — the folklore-index mini-pipeline (Berezkin / TMI / ATU → crosswalk →
parallels → semantic). Key = singleton.

TEMPORARY monolithic adapter over ``build_motifs``. Motifs has no offline fingerprint gate
(it re-parses its scrape cache every run), so this stage is reported *stale-until-built* and
rebuilt on every ``build`` — exactly today's behaviour. It is slated to be split into the
per-source stages (``motifs:source:*`` → ``crosswalk`` → ``parallels`` → ``semantic``) the
spec describes (pipeline §2.2); the driver wiring does not change when it is.
"""

from __future__ import annotations

from motifs import store
from motifs.build_motifs import build_motifs

from ..stage import Stage

_KEY = "motifs"


class MotifsStage(Stage):
    name = "motifs"
    store = None  # singleton — never orphaned within the pipeline

    def inputs(self) -> list[Stage]:
        return []  # its sources are external scrapes, not the corpus

    def desired(self) -> dict[str, str]:
        # No offline gate yet → a sentinel that never equals actual(), so build always runs.
        return {_KEY: "rebuild"}

    def actual(self) -> dict[str, str]:
        return {_KEY: "built"} if store.is_built() else {}

    def build(self, keys: set[str]) -> None:
        build_motifs()

    def delete(self, keys: set[str]) -> None:
        pass  # singleton; never an orphan key
