"""Generic build engine (Part 3 / Stage IV).

A build is a DAG of **stages**, each a pure function of its inputs whose staleness is
decidable offline from fingerprints. One generic :mod:`~pipeline.driver` derives every
operation — ``status``, ``build``, ``clean`` — as a diff of two ``{key: fp}`` maps
(:meth:`Stage.desired` vs :meth:`Stage.actual`), so there is no per-store bespoke path.

See ``docs/proposals/pipeline-and-incrementality.md`` §2.
"""

from .driver import CleanReport, StagePlan, build, clean, plan, status, topo_order
from .pipeline import build_pipeline
from .stage import Stage, Store

__all__ = [
    "Stage", "Store", "StagePlan", "CleanReport",
    "plan", "status", "build", "clean", "topo_order", "build_pipeline",
]
