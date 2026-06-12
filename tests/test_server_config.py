import yaml

from server.config import ServerConfig
from settings import load_yaml_config


class TestServerConfigDefaults:
    def test_host(self):
        cfg = ServerConfig()
        assert cfg.host == "127.0.0.1"

    def test_port(self):
        cfg = ServerConfig()
        assert cfg.port == 8000

    def test_gzip_minimum_size(self):
        cfg = ServerConfig()
        assert cfg.gzip_minimum_size == 1024

    def test_cache_max_age(self):
        cfg = ServerConfig()
        assert cfg.cache_max_age == 86400

    def test_search_defaults(self):
        cfg = ServerConfig()
        assert cfg.search_job_ttl_seconds == 1800
        assert cfg.search_max_workers == 1

    def test_frozen(self):
        import dataclasses

        assert dataclasses.fields(ServerConfig)
        cfg = ServerConfig()
        try:
            cfg.port = 9999  # type: ignore[misc]
            assert False, "Should be frozen"
        except dataclasses.FrozenInstanceError:
            pass


class TestServerConfigYamlOverride:
    def test_override_host_and_port(self, tmp_path):
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml.dump({"server": {"host": "0.0.0.0", "port": 9000}}))
        cfg = load_yaml_config(ServerConfig, "server", str(yaml_path))
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 9000

    def test_partial_override(self, tmp_path):
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml.dump({"server": {"search_max_workers": 4}}))
        cfg = load_yaml_config(ServerConfig, "server", str(yaml_path))
        assert cfg.search_max_workers == 4
        assert cfg.host == "127.0.0.1"

    def test_missing_yaml_uses_defaults(self):
        cfg = load_yaml_config(ServerConfig, "nonexistent_server_config_xyz")
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8000


class TestProjectPaths:
    def test_paths_are_set(self):
        from server.config import paths

        assert paths.project_root is not None
        assert paths.ui_root is not None
        assert paths.web_root is not None
