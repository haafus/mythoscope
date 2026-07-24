"""ProjectionsStage: desired() = _fingerprint_from_metas over the model's chunk metadata;
actual() = the stored .input-fp when every plot is present. Fake collection, no umap."""

import pipeline.stages.projections as proj_mod
import settings as settings_mod
from pipeline import plan
from pipeline.stages import ProjectionsStage
from pipeline.stores import FileStore
from projections import PROJECTION_METHODS
from projections.build_projections import _fingerprint_from_metas

METAS = [
    {"document_id": "a", "chunk_index": 0, "fingerprint": "fa"},
    {"document_id": "a", "chunk_index": 1, "fingerprint": "fa"},
    {"document_id": "b", "chunk_index": 0, "fingerprint": "fb"},
]


class FakeEmbeddings:
    name, store = "embeddings:v1", None

    def inputs(self):
        return []

    desired = actual = lambda self: {}
    build = delete = lambda self, keys: None


class FakeCollection:
    def __init__(self, metas):
        self._metas = metas

    def get(self, include=None):
        return {"metadatas": self._metas}


def _stage(monkeypatch, metas):
    monkeypatch.setattr(proj_mod.chroma_manager, "get_collection", lambda k: FakeCollection(metas))
    return ProjectionsStage("v1", FakeEmbeddings(), store=object())


def _write_plots(tmp_path, model, fp):
    d = tmp_path / model
    d.mkdir(parents=True)
    (d / ".input-fp").write_text(fp, encoding="utf-8")
    for m in PROJECTION_METHODS:
        (d / f"{m['key']}.json").write_text("{}", encoding="utf-8")


def test_clean_when_input_fp_matches(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    _write_plots(tmp_path, "v1", _fingerprint_from_metas(METAS))
    assert plan(_stage(monkeypatch, METAS)).clean


def test_missing_when_no_plots(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    assert plan(_stage(monkeypatch, METAS)).missing == {"v1"}


def test_missing_when_a_plot_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    _write_plots(tmp_path, "v1", _fingerprint_from_metas(METAS))
    (tmp_path / "v1" / f"{PROJECTION_METHODS[0]['key']}.json").unlink()  # incomplete
    assert plan(_stage(monkeypatch, METAS)).missing == {"v1"}


def test_stale_when_embeddings_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    _write_plots(tmp_path, "v1", _fingerprint_from_metas(METAS))
    edited = [{**METAS[0], "fingerprint": "fa2"}, *METAS[1:]]  # a text edit
    assert plan(_stage(monkeypatch, edited)).stale == {"v1"}


def test_delete_removes_model_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    _write_plots(tmp_path, "v1", "x")
    _stage(monkeypatch, METAS).delete({"v1"})
    assert not (tmp_path / "v1").exists()


def test_filestore_lists_and_deletes_subdirs(tmp_path):
    (tmp_path / "v1").mkdir()
    (tmp_path / "v2").mkdir()
    store = FileStore(tmp_path)
    assert store.ids() == {"v1", "v2"}
    store.delete("v1")
    assert store.ids() == {"v2"}
