"""The motifs stage — the folklore-index mini-pipeline (Berezkin / TMI / ATU → crosswalk →
parallels → semantic). Key = singleton.

Still a monolithic adapter over ``build_motifs``, but now with a coarse **input** fingerprint
(raw scrape cache + config + algo version) so it rebuilds only when its inputs change instead
of every run. It is slated to be split into the per-source stages (``motifs:source:*`` →
``crosswalk`` → ``parallels`` → ``semantic``) the spec describes (pipeline §2.2); the driver
wiring does not change when it is.
"""

from __future__ import annotations

from motifs import store
from motifs.build_motifs import build_motifs
from motifs.fingerprint import motifs_fingerprint

from ..stage import Stage

_KEY = "motifs"


class MotifsStage(Stage):
    name = "motifs"
    store = None  # singleton — never orphaned within the pipeline

    def inputs(self) -> list[Stage]:
        return []  # its sources are external scrapes, not the corpus

    def desired(self) -> dict[str, str]:
        return {_KEY: motifs_fingerprint()}

    def actual(self) -> dict[str, str]:
        fp_path = store.motifs_dir() / ".fp"
        if store.is_built() and fp_path.exists():
            return {_KEY: fp_path.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        build_motifs()

    def delete(self, keys: set[str]) -> None:
        pass  # singleton; never an orphan key
