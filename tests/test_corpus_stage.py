"""CorpusStage: desired() from pinned raw (offline), actual() from the catalog, and the diff
the driver reads. Uses a tiny on-disk fixture so no network/model is involved."""

import json

import settings as settings_mod
from corpus.fingerprint import source_fingerprint
from corpus.locator import corpus_raw_path, document_id
from pipeline import plan
from pipeline.stages import CorpusStage

URL_A = "file:a.txt"
URL_B = "file:b.txt"


def _fixture(tmp_path, monkeypatch, *, write_txt=(URL_A, URL_B), with_source_fp=True):
    monkeypatch.setattr(settings_mod.settings, "corpus_dir", tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir(parents=True)
    raw = {URL_A: b"raw A", URL_B: b"raw B"}
    for url, data in raw.items():
        corpus_raw_path(raw_root, url).write_bytes(data)

    rows = []
    for url in (URL_A, URL_B):
        did = document_id(url)
        rel = f"{did}.txt"
        row = {"url": url, "document_id": did, "path": rel, "fingerprint": f"out-{did}"}
        if with_source_fp:
            row["source_fp"] = source_fingerprint(raw[url], None, None)
        rows.append(row)
        if url in write_txt:
            (tmp_path / rel).write_text("cleaned", encoding="utf-8")
    (tmp_path / "corpus.json").write_text(json.dumps(rows), encoding="utf-8")

    items = [{"url": URL_A}, {"url": URL_B}]
    monkeypatch.setattr("pipeline.stages.corpus.load_download_list", lambda: items)
    return raw


def test_clean_when_catalog_matches_pinned_raw(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    assert plan(CorpusStage()).clean


def test_missing_when_txt_absent(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch, write_txt=(URL_A,))  # B has a row but no .txt
    p = plan(CorpusStage())
    assert p.missing == {document_id(URL_B)}


def test_stale_when_raw_changes(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    # Re-deliver A's local source with different bytes → its offline source_fp flips.
    corpus_raw_path(tmp_path / "raw", URL_A).write_bytes(b"raw A EDITED")
    p = plan(CorpusStage())
    assert p.stale == {document_id(URL_A)}


def test_fp_init_row_without_source_fp_is_stale(tmp_path, monkeypatch):
    # A pre-source_fp row: .txt present but no stored fp → not in actual() → missing (rebuilds).
    _fixture(tmp_path, monkeypatch, with_source_fp=False)
    p = plan(CorpusStage())
    assert p.missing == {document_id(URL_A), document_id(URL_B)}


def test_doc_fingerprints_exposes_output_fp(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    fps = CorpusStage().doc_fingerprints()
    assert fps == {document_id(URL_A): f"out-{document_id(URL_A)}", document_id(URL_B): f"out-{document_id(URL_B)}"}


def test_delete_removes_txt_and_row(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    CorpusStage().delete({document_id(URL_A)})
    rows = json.loads((tmp_path / "corpus.json").read_text())
    assert [r["document_id"] for r in rows] == [document_id(URL_B)]
    assert not (tmp_path / f"{document_id(URL_A)}.txt").exists()
