"""build_pipeline() wires a valid DAG whose topological order reproduces the historical
sequence: Corpus → Embeddings → Projections → Graphs → Motifs (with per-model fan-out)."""

from pipeline import build_pipeline, topo_order


def test_pipeline_topo_orders_by_the_historical_sequence():
    order = [s.name for s in topo_order(build_pipeline())]  # raises on a cycle / unknown input

    def rank(name):
        for i, prefix in enumerate(("corpus", "embeddings:", "projections:", "graphs", "motifs")):
            if name.startswith(prefix):
                return i
        raise AssertionError(f"unexpected stage {name!r}")

    ranks = [rank(n) for n in order]
    assert ranks == sorted(ranks)                 # every family in sequence
    assert order[0] == "corpus" and order[-1] == "motifs"


def test_every_projection_follows_its_own_model_embeddings():
    order = [s.name for s in topo_order(build_pipeline())]
    for name in order:
        if name.startswith("projections:"):
            model = name.split(":", 1)[1]
            assert order.index(f"embeddings:{model}") < order.index(name)
