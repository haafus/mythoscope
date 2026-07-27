"""The generic driver: topological order, the desired/actual diff, and two-level clean.

Exercised with fake stages/stores so the driver's logic is tested in isolation from any real
build. Real stages get their own per-stage tests as they are ported."""

import pytest

from pipeline import build, clean, plan, status, topo_order
from pipeline.stage import Stage


class FakeStage(Stage):
    def __init__(self, name, desired, actual, deps=(), store=None, id=""):
        self.name = name
        self.store = store
        self.id = id
        self._desired = dict(desired)
        self._actual = dict(actual)
        self._deps = list(deps)
        self.built = []   # records each build(keys) call
        self.deleted = []  # records each delete(keys) call

    def inputs(self):
        return self._deps

    def desired(self):
        return dict(self._desired)

    def actual(self):
        return dict(self._actual)

    def build(self, keys):
        self.built.append(set(keys))
        # Simulate a successful build: the keys become actual with their desired fp.
        for k in keys:
            self._actual[k] = self._desired[k]

    def delete(self, keys):
        self.deleted.append(set(keys))
        for k in keys:
            self._actual.pop(k, None)


class FakeStore:
    def __init__(self, ids):
        self._ids = set(ids)
        self.deleted = []

    def ids(self):
        return set(self._ids)

    def delete(self, id):
        self.deleted.append(id)
        self._ids.discard(id)


# --- topological order ---------------------------------------------------------------------

def test_topo_places_dependencies_before_dependents():
    a = FakeStage("a", {}, {})
    b = FakeStage("b", {}, {}, deps=[a])
    c = FakeStage("c", {}, {}, deps=[b])
    order = [s.name for s in topo_order([c, b, a])]
    assert order.index("a") < order.index("b") < order.index("c")


def test_topo_tie_breaks_by_declaration_order():
    # corpus → {embeddings, graphs}; embeddings → projections. Declaration order mirrors the
    # real registry, and the walk must reproduce it exactly (embeddings before graphs, etc.).
    corpus = FakeStage("corpus", {}, {})
    emb = FakeStage("embeddings", {}, {}, deps=[corpus])
    proj = FakeStage("projections", {}, {}, deps=[emb])
    graphs = FakeStage("graphs", {}, {}, deps=[corpus])
    motifs = FakeStage("motifs", {}, {})
    order = [s.name for s in topo_order([corpus, emb, proj, graphs, motifs])]
    assert order == ["corpus", "embeddings", "projections", "graphs", "motifs"]


def test_topo_detects_cycle():
    a = FakeStage("a", {}, {})
    b = FakeStage("b", {}, {}, deps=[a])
    a._deps = [b]  # a ↔ b
    with pytest.raises(ValueError, match="cycle"):
        topo_order([a, b])


def test_topo_rejects_input_outside_pipeline():
    stray = FakeStage("stray", {}, {})
    a = FakeStage("a", {}, {}, deps=[stray])
    with pytest.raises(ValueError, match="not in the pipeline"):
        topo_order([a])


# --- the diff ------------------------------------------------------------------------------

def test_plan_classifies_missing_stale_orphan():
    s = FakeStage(
        "s",
        desired={"keep": "fp1", "edit": "fp2new", "new": "fp3"},
        actual={"keep": "fp1", "edit": "fp2old", "gone": "fpX"},
    )
    p = plan(s)
    assert p.missing == {"new"}
    assert p.stale == {"edit"}
    assert p.orphans == {"gone"}
    assert not p.clean


def test_plan_clean_when_desired_equals_actual():
    s = FakeStage("s", {"a": "1", "b": "2"}, {"a": "1", "b": "2"})
    assert plan(s).clean


def test_status_returns_plans_in_topo_order():
    a = FakeStage("a", {}, {})
    b = FakeStage("b", {}, {}, deps=[a])
    assert [p.stage.name for p in status([b, a])] == ["a", "b"]


# --- build ---------------------------------------------------------------------------------

def test_build_only_touches_missing_and_stale():
    s = FakeStage("s", {"keep": "1", "new": "2", "edit": "3new"}, {"keep": "1", "edit": "3old"})
    build([s])
    assert s.built == [{"new", "edit"}]   # keep (up-to-date) is untouched


def test_build_noop_when_current():
    s = FakeStage("s", {"a": "1"}, {"a": "1"})
    build([s])
    assert s.built == []


def test_force_rebuilds_every_desired_key():
    s = FakeStage("s", {"a": "1", "b": "2"}, {"a": "1", "b": "2"})
    build([s], force=True)
    assert s.built == [{"a", "b"}]


def test_sample_caps_every_stage_and_leaves_rest_missing():
    # --sample N caps each stage to N keys; the rest stay `missing` (never orphan).
    s = FakeStage("corpus", {"a": "1", "b": "2", "c": "3"}, {})
    build([s], sample=2)
    assert len(s.built[0]) == 2
    assert len(s.actual()) == 2
    assert plan(s).orphans == set()
    assert len(plan(s).missing) == 1


def test_sample_is_noop_on_single_key_stage():
    s = FakeStage("motifs", {"motifs": "1"}, {})  # 1 key: [:N>=1] returns it
    build([s], sample=2)
    assert s.built == [{"motifs"}]


def test_sample_then_full_completes_without_rebuild():
    # No churn: a later full build finishes the leftover keys and does NOT rebuild the sampled N.
    s = FakeStage("corpus", {"a": "1", "b": "2", "c": "3"}, {})
    build([s], sample=2)
    sampled = set(s.built[0])
    build([s])
    assert s.built[1] == {"a", "b", "c"} - sampled
    assert len(s.actual()) == 3


def test_targets_build_only_named_not_stale_upstream():
    # Literal scope: corpus is missing but not a target → not built; only graphs is.
    corpus = FakeStage("corpus", {"d": "1"}, {})
    graphs = FakeStage("graphs", {"d": "1"}, {}, deps=[corpus])
    build([corpus, graphs], targets={"graphs"})
    assert corpus.built == []          # upstream present only to wire/order — not rebuilt
    assert graphs.built == [{"d"}]


def test_build_runs_in_topological_order():
    calls = []
    corpus = FakeStage("corpus", {"d": "1"}, {})
    emb = FakeStage("emb", {"d": "1"}, {}, deps=[corpus])
    for st in (corpus, emb):
        orig = st.build
        st.build = (lambda name, o: (lambda keys: (calls.append(name), o(keys))[1]))(st.name, orig)
    build([emb, corpus])
    assert calls == ["corpus", "emb"]


# --- clean (two levels) --------------------------------------------------------------------

def test_clean_level1_reaps_orphan_keys():
    s = FakeStage("s", {"live": "1"}, {"live": "1", "dead": "9"})
    report = clean([s], apply=True)
    assert report.level1 == {"s": {"dead"}}
    assert s.deleted == [{"dead"}]


def test_clean_dry_run_does_not_delete():
    s = FakeStage("s", {"live": "1"}, {"live": "1", "dead": "9"})
    report = clean([s], apply=False)
    assert report.level1 == {"s": {"dead"}}
    assert s.deleted == []


def test_clean_level2_reaps_unowned_store_artifacts():
    # Store holds three collections; only two are claimed by live stages → one L2 orphan.
    store = FakeStore({"model_a", "model_b", "dropped_model"})
    a = FakeStage("emb:a", {}, {}, store=store, id="model_a")
    b = FakeStage("emb:b", {}, {}, store=store, id="model_b")
    report = clean([a, b], apply=True)
    assert report.level2 == {"FakeStore": {"dropped_model"}}
    assert store.deleted == ["dropped_model"]


def test_clean_level2_scoped_to_member_spares_sibling_orphans():
    # family-granular level-2: a single-member scope must NOT sweep a sibling's dropped collection;
    # the whole-family scope and an unscoped clean still reap it.
    def fresh():
        store = FakeStore({"model_a", "model_b", "dropped_model"})
        a = FakeStage("emb:a", {}, {}, store=store, id="model_a")
        b = FakeStage("emb:b", {}, {}, store=store, id="model_b")
        return store, [a, b]

    store, stages = fresh()
    clean(stages, apply=True, targets={"emb:a"})            # single member → spare siblings
    assert store.deleted == []

    store, stages = fresh()
    clean(stages, apply=True, targets={"emb:a", "emb:b"})   # whole family → reap
    assert store.deleted == ["dropped_model"]

    store, stages = fresh()
    clean(stages, apply=True)                                # unscoped → reap
    assert store.deleted == ["dropped_model"]


def test_clean_empty_when_nothing_orphaned():
    store = FakeStore({"m"})
    s = FakeStage("s", {"k": "1"}, {"k": "1"}, store=store, id="m")
    assert clean([s], apply=True).empty


def test_build_reports_only_actually_built_keys():
    """#6: `built` is the post-build actual ∩ todo — a silently-failed key (no fp stamp) drops out,
    so the reported count is honest, not the attempted count."""
    s = FakeStage("s", desired={"a": "1", "b": "1", "c": "1"}, actual={})

    def partial(keys):                      # simulate 'c' failing: only a, b become actual
        s.built.append(set(keys))
        for k in keys:
            if k != "c":
                s._actual[k] = s._desired[k]

    s.build = partial
    [p] = build([s])
    assert p.to_build == {"a", "b", "c"}    # all three were attempted
    assert p.built == {"a", "b"}            # only the two that actually landed are counted


def test_clean_level2_keyed_by_store_label_not_class():
    """#5: two stores are distinguished by their .label, so their orphans never collide in the
    level-2 report (class-name keying would clobber one)."""
    st1 = FakeStore(["m1", "orphanA"]); st1.label = "FileStore(projections)"
    st2 = FakeStore(["m2", "orphanB"]); st2.label = "FileStore(graphs)"
    a = FakeStage("projections:m1", {"m1": "1"}, {"m1": "1"}, store=st1, id="m1")
    b = FakeStage("graphs:m2", {"m2": "1"}, {"m2": "1"}, store=st2, id="m2")
    report = clean([a, b])
    assert set(report.level2) == {"FileStore(projections)", "FileStore(graphs)"}
    assert report.level2["FileStore(projections)"] == {"orphanA"}
    assert report.level2["FileStore(graphs)"] == {"orphanB"}
