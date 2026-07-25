"""The stage protocol — the one interface the generic driver reconciles.

A **stage** is the smallest independently-buildable unit whose every artifact is keyed the
same way (a ``document_id`` per book, or a lone ``"singleton"`` key). It exposes two maps of
the **same shape** — ``{key: fingerprint}`` — named by the *state* they describe:

* :meth:`Stage.desired` — the spec: which keys should exist and what fp each should hash to
  now (from config + its inputs' ``desired()`` fps).
* :meth:`Stage.actual` — reality: which keys are built (**both** artifact *and* fp sidecar
  present) and the fp they were built with.

The driver never asks for a single key's fp — it always diffs the whole maps (§2.6).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class Store(Protocol):
    """A *shared* backend (a Chroma DB, a directory tree) that several fan-out stages write
    into. Used only for **level-2 GC**: when a whole stage is removed from the pipeline
    (a dropped model / plot / motif source) it never enters the driver's per-key traversal,
    so its now-unowned artifact is caught by asking the store which ids it holds (§2.7)."""

    def ids(self) -> set[str]:
        """Every artifact id currently present in this backend."""
        ...

    def delete(self, id: str) -> None:
        """Drop one whole fan-out artifact (a collection / a model dir) by id."""
        ...


class Stage(ABC):
    """One atomic stage. Subclasses set :attr:`name` and implement the four methods.

    ``store``/``id`` are only meaningful on fan-out or singleton stages (embeddings,
    projections, motifs) — the id this stage owns inside its shared :class:`Store`, for
    level-2 GC. Per-document stages (corpus, graphs) own their whole directory and leave
    ``store = None``, relying wholly on the per-key (level-1) ``desired``/``actual`` diff.
    """

    name: str
    store: Store | None = None
    id: str = ""

    @abstractmethod
    def inputs(self) -> list[Stage]:
        """Upstream stages this one reads (held references → topological order + wiring)."""

    @abstractmethod
    def desired(self) -> dict[str, str]:
        """What SHOULD exist + the fp each key should hash to now (config + inputs' fps)."""

    @abstractmethod
    def actual(self) -> dict[str, str]:
        """What IS built — a key appears only if its artifact AND its fp sidecar are present."""

    @abstractmethod
    def build(self, keys: set[str]) -> None:
        """(Re)build exactly these keys. Batched; isolates per-key failure (a failed key
        simply gets no fp sidecar, so it stays ``missing`` and is retried next run)."""

    @abstractmethod
    def delete(self, keys: set[str]) -> None:
        """Level-1: drop these KEYS within this stage's own store (chunk rows, doc files) —
        distinct from ``Store.delete(id)``, which drops one whole fan-out artifact."""
