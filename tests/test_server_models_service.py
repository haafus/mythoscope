import json

from server.config import ProjectPaths
from server.services.models import (
    get_model_info,
    get_model_output_dir,
    key_to_model,
    list_model_summaries,
    list_models_raw,
    model_to_key,
)


def _paths_with_analysis(tmp_path):
    return ProjectPaths(
        project_root=tmp_path,
        ui_root=tmp_path,
        web_root=tmp_path,
        assets_dir=tmp_path,
        analysis_dir=tmp_path,
        template_dir=tmp_path,
        corpus_dir=tmp_path,
        corpus_chunked_dir=tmp_path,
    )


class TestModelToKey:
    def test_slash_replaced(self):
        assert model_to_key("BAAI/bge-m3") == "BAAI_bge-m3"

    def test_backslash_replaced(self):
        assert model_to_key("path\\model") == "path_model"

    def test_no_special_chars(self):
        assert model_to_key("simple-model") == "simple-model"

    def test_empty(self):
        assert model_to_key("") == ""


class TestKeyToModel:
    def test_passthrough_with_slash(self):
        assert key_to_model("BAAI/bge-m3") == "BAAI/bge-m3"

    def test_empty_string(self):
        assert key_to_model("") == ""

    def test_finds_in_models_list(self):
        result = key_to_model("BAAI_bge-m3", models=["BAAI/bge-m3", "other/model"])
        assert result == "BAAI/bge-m3"

    def test_fallback_replaces_underscore(self):
        result = key_to_model("unknown_xyz_abc", models=[])
        assert result == "unknown/xyz/abc"

    def test_first_match_wins(self):
        result = key_to_model("a_b", models=["a/b", "a_b"])
        assert result == "a/b"


class TestListModelsRaw:
    def test_reads_models_json(self, tmp_path, monkeypatch):
        models_json = tmp_path / "models.json"
        models_json.write_text(json.dumps(["model/a", "model/b"]))
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))

        result = list_models_raw()
        assert result == ["model/a", "model/b"]

    def test_fallback_to_dirs(self, tmp_path, monkeypatch):
        model_dir = tmp_path / "model_a"
        model_dir.mkdir()
        (model_dir / "model_info.json").write_text(json.dumps({"model_name": "author/model_a"}))
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))

        result = list_models_raw()
        assert "author/model_a" in result

    def test_empty_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))
        assert list_models_raw() == []


class TestListModelSummaries:
    def test_returns_dicts_with_keys(self, tmp_path, monkeypatch):
        models_json = tmp_path / "models.json"
        models_json.write_text(json.dumps(["BAAI/bge-m3"]))
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))

        result = list_model_summaries()
        assert len(result) == 1
        assert result[0]["name"] == "BAAI/bge-m3"
        assert result[0]["key"] == "BAAI_bge-m3"
        assert result[0]["safe_dir"] == "BAAI_bge-m3"


class TestGetModelInfo:
    def test_existing_info(self, tmp_path, monkeypatch):
        model_dir = tmp_path / "test_model"
        model_dir.mkdir()
        info = {"model_name": "test/model", "dim": 768}
        (model_dir / "model_info.json").write_text(json.dumps(info))
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))

        result = get_model_info("test_model")
        assert result["model_name"] == "test/model"

    def test_missing_info(self, tmp_path, monkeypatch):
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))
        assert get_model_info("nonexistent") == {}


class TestGetModelOutputDir:
    def test_returns_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr("server.services.models.paths", _paths_with_analysis(tmp_path))
        result = get_model_output_dir("BAAI_bge-m3")
        assert result.parent == tmp_path
