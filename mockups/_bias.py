"""Attestation-intensity (sampling) weights, shared by the bias-aware mockups.

Tradition coverage a(t) = #motifs recorded spans 1..738 (median ~74), so densely-catalogued
corpora dominate any raw count. `coverage_weights` gives each tradition
w(t) = min(cap, median_a / a(t)): it downweights over-catalogued traditions and upweights
thin ones (capped so a tiny corpus can't explode), moving every count toward
one-tradition-one-vote. This is the §5 control mockup 20 prototyped, factored out so mockup
24's sweep and any later refactor share one definition.
"""
from collections import Counter

import numpy as np

CAP = 2.0


def attestation_counts(motifs, traditions):
    c = Counter()
    for r in motifs:
        for t in (r.get("traditions") or []):
            if t in traditions:
                c[t] += 1
    return c


def coverage_weights(motifs, traditions, cap=CAP):
    """Return ({tid: w(t)}, median_coverage)."""
    c = attestation_counts(motifs, traditions)
    if not c:
        return {}, 0.0
    med = float(np.median(list(c.values())))
    return {t: min(cap, med / c[t]) for t in c}, med
