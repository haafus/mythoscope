import json


def test_default_rebuilds_from_cache_without_llm(tmp_path, monkeypatch):
    """The default build rebuilds graph files from a complete extraction cache and
    makes no LLM call (the processor is constructed lazily, so it works offline /
    with no API key when nothing needs extracting)."""
    from chunk_cache import append_cache, chunk_hash
    from embeddings.chunking import chunk_text
    from settings import settings

    corpus = tmp_path / "corpus"
    graphs = tmp_path / "graphs"
    corpus.mkdir()
    graphs.mkdir()
    monkeypatch.setattr(settings, "corpus_dir", corpus)
    monkeypatch.setattr(settings, "graphs_dir", graphs)

    text = "Moses led the people out. Aaron spoke to Pharaoh in Egypt."
    doc_id = "book0000fp"  # graphs are keyed by document_id (D1), not the title
    (corpus / "book.txt").write_text(text, encoding="utf-8")
    (corpus / "corpus.json").write_text(
        json.dumps([{"title": "Book", "path": "book.txt", "document_id": doc_id}]), encoding="utf-8"
    )

    book_dir = graphs / doc_id
    book_dir.mkdir(parents=True)
    cache_path = book_dir / "extraction_cache.jsonl"
    chunks = chunk_text(text, settings.graphs.chunk_size, settings.graphs.chunk_overlap)
    for c in chunks:
        append_cache(
            cache_path,
            chunk_hash(c),
            {
                "beings": [{"Name": "Moses"}, {"Name": "Aaron"}],
                "relations": [{"Subject": "Moses", "Object": "Aaron", "Relation": "leads"}],
                "locations": [{"Name": "Egypt"}],
                "times": [{"Name": "Exodus"}],
            },
        )

    from graphs.build_graphs import build_graphs

    build_graphs()  # cache complete -> no LLM constructed, no network

    for fname in ("beings.json", "realms.json", "ages.json"):
        assert (book_dir / fname).exists()
    beings = json.loads((book_dir / "beings.json").read_text(encoding="utf-8"))
    ids = {n["id"] for n in beings["nodes"]}
    assert {"Moses", "Aaron"} <= ids
