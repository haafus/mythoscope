"""build_corpus self-prunes orphan .txt (a document dropped from config), symmetric to how
build_embeddings prunes orphan chunks. The raw archive is never touched."""

import settings as settings_mod
from corpus.builder import _prune_orphan_texts


def test_prunes_txt_not_in_catalog_keeps_referenced_and_raw(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "corpus_dir", tmp_path)
    (tmp_path / "Region" / "Trad").mkdir(parents=True)
    kept = tmp_path / "Region" / "Trad" / "Kept.txt"
    stray = tmp_path / "Region" / "Trad" / "Stray.txt"
    kept.write_text("k", encoding="utf-8")
    stray.write_text("s", encoding="utf-8")
    (tmp_path / "raw").mkdir()
    raw = tmp_path / "raw" / "deadbeef"           # pinned raw, no .txt suffix — must survive
    raw.write_bytes(b"raw")

    _prune_orphan_texts([{"path": "Region/Trad/Kept.txt"}])

    assert kept.exists()
    assert not stray.exists()
    assert raw.exists()
