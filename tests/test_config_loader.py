import yaml

from corpus.config import CorpusConfig, load_config
from settings import _flatten, load_yaml_config


class TestFlatten:
    def test_flat_dict_unchanged(self):
        assert _flatten({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_nested_dict(self):
        result = _flatten({"build": {"max_workers": 10}})
        assert result == {"build_max_workers": 10}

    def test_deeply_nested(self):
        result = _flatten({"a": {"b": {"c": 42}}})
        assert result == {"a_b_c": 42}

    def test_empty_dict(self):
        assert _flatten({}) == {}

    def test_mixed_nesting(self):
        result = _flatten({"x": 1, "y": {"z": 2}})
        assert result == {"x": 1, "y_z": 2}


class TestCorpusConfigDefaults:
    def test_default_max_workers(self):
        cfg = CorpusConfig()
        assert cfg.max_workers == 10

    def test_default_timeouts(self):
        cfg = CorpusConfig()
        assert cfg.timeout_connect == 10
        assert cfg.timeout_read == 30

    def test_default_retry(self):
        cfg = CorpusConfig()
        assert cfg.retry_total == 4
        assert cfg.retry_backoff_factor == 1.5
        assert cfg.retry_status_forcelist == [429, 500, 502, 503, 504]

    def test_default_parsing(self):
        cfg = CorpusConfig()
        assert cfg.html_include_comments is False
        assert cfg.html_include_tables is True
        assert cfg.pdf_extract_tables is False
        assert cfg.pdf_preserve_layout is True

    def test_paths_from_settings(self):
        cfg = CorpusConfig()
        assert cfg.corpus_dir is not None
        assert cfg.download_list_file is not None
        assert cfg.metadata_file is not None
        assert cfg.catalog_file is not None
        assert cfg.processed_urls_file is not None


class TestCorpusConfigOverride:
    def test_override_from_yaml(self, tmp_path):
        yaml_path = tmp_path / "test_config.yaml"
        yaml_path.write_text(
            yaml.dump({"build": {"max_workers": 20}, "downloader": {"timeout_connect": 5}})
        )
        cfg = load_yaml_config(CorpusConfig, "corpus", str(yaml_path))
        assert cfg.max_workers == 20
        assert cfg.timeout_connect == 5
        assert cfg.timeout_read == 30  # unchanged default

    def test_partial_override(self, tmp_path):
        yaml_path = tmp_path / "test_config.yaml"
        yaml_path.write_text(yaml.dump({"downloader": {"retry_total": 8}}))
        cfg = load_yaml_config(CorpusConfig, "corpus", str(yaml_path))
        assert cfg.retry_total == 8
        assert cfg.max_workers == 10  # unchanged default

    def test_empty_yaml(self, tmp_path):
        yaml_path = tmp_path / "test_config.yaml"
        yaml_path.write_text("")
        cfg = load_yaml_config(CorpusConfig, "corpus", str(yaml_path))
        assert cfg.max_workers == 10  # all defaults

    def test_missing_yaml_uses_defaults(self):
        cfg = load_yaml_config(CorpusConfig, "nonexistent_module_xyz")
        assert cfg.max_workers == 10

    def test_unknown_keys_ignored(self, tmp_path):
        yaml_path = tmp_path / "test_config.yaml"
        yaml_path.write_text(yaml.dump({"unknown_section": {"foo": "bar"}}))
        cfg = load_yaml_config(CorpusConfig, "corpus", str(yaml_path))
        assert cfg.max_workers == 10


class TestLoadConfig:
    def test_load_config_returns_instance(self):
        cfg = load_config()
        assert isinstance(cfg, CorpusConfig)

    def test_load_config_with_path(self, tmp_path):
        yaml_path = tmp_path / "custom.yaml"
        yaml_path.write_text(yaml.dump({"build": {"max_workers": 99}}))
        cfg = load_config(str(yaml_path))
        assert cfg.max_workers == 99
