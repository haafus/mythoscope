"""Unit tests for EmbeddingEncoder model loading: snapshot cache-first, ST-config
injection for models that ship none, and dtype selection."""

import torch

from embeddings import model_manager
from embeddings.model_manager import EmbeddingEncoder, _resolve_dtype


class _FakeModel:
    device = "cpu"


def _cfg(alias="m", model="hf/m", dtype="auto"):
    return {"alias": alias, "model": model, "dtype": dtype,
            "query_prompt": "", "document_prompt": "", "batch_size": None}


def _setup(monkeypatch, tmp_path, *, native_modules, cfg, with_overrides=False):
    snap = tmp_path / "snap"
    snap.mkdir()
    if native_modules:
        (snap / "modules.json").write_text("[]")

    monkeypatch.setattr("huggingface_hub.snapshot_download", lambda hf_id, **k: str(snap))

    ov_root = tmp_path / "st_overrides"
    monkeypatch.setattr(model_manager, "ST_OVERRIDES", ov_root)
    if with_overrides:
        d = ov_root / cfg["alias"]
        (d / "1_Pooling").mkdir(parents=True)
        (d / "modules.json").write_text('["injected"]')
        (d / "1_Pooling" / "config.json").write_text("{}")
        (d / "README.md").write_text("provenance, must not be copied")

    monkeypatch.setattr(model_manager, "embedding_config", lambda n: cfg)

    captured: dict = {}

    def loader(path, **kwargs):
        captured["path"] = path
        captured["kwargs"] = kwargs
        return _FakeModel()

    monkeypatch.setattr(model_manager, "SentenceTransformer", loader)
    return snap, captured


def test_native_st_config_loads_without_injection(monkeypatch, tmp_path):
    snap, cap = _setup(monkeypatch, tmp_path, native_modules=True, cfg=_cfg())
    EmbeddingEncoder().load("m")
    assert cap["path"] == str(snap)
    assert not (snap / "1_Pooling").exists()  # nothing injected


def test_injects_overrides_when_model_lacks_st_config(monkeypatch, tmp_path):
    snap, cap = _setup(monkeypatch, tmp_path, native_modules=False,
                       cfg=_cfg(), with_overrides=True)
    EmbeddingEncoder().load("m")
    assert (snap / "modules.json").read_text() == '["injected"]'
    assert (snap / "1_Pooling" / "config.json").exists()
    assert not (snap / "README.md").exists()  # README is provenance, not injected


def test_warns_when_overrides_missing(monkeypatch, tmp_path, caplog):
    _setup(monkeypatch, tmp_path, native_modules=False, cfg=_cfg(), with_overrides=False)
    with caplog.at_level("WARNING"):
        EmbeddingEncoder().load("m")
    assert any("not found" in r.message for r in caplog.records)


def test_explicit_dtype_passed_as_model_kwargs(monkeypatch, tmp_path):
    _, cap = _setup(monkeypatch, tmp_path, native_modules=True, cfg=_cfg(dtype="float16"))
    EmbeddingEncoder().load("m")
    assert cap["kwargs"]["model_kwargs"]["torch_dtype"] is torch.float16


def test_auto_dtype_on_cpu_leaves_default(monkeypatch, tmp_path):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    _, cap = _setup(monkeypatch, tmp_path, native_modules=True, cfg=_cfg(dtype="auto"))
    EmbeddingEncoder().load("m")
    assert "model_kwargs" not in cap["kwargs"]  # None dtype → no override, stays fp32


def test_resolve_dtype_explicit_values():
    assert _resolve_dtype("bfloat16") is torch.bfloat16
    assert _resolve_dtype("fp16") is torch.float16
    assert _resolve_dtype("float32") is torch.float32
