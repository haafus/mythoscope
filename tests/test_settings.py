from pathlib import Path


def test_default_paths():
    from settings import Settings

    s = Settings()
    assert s.corpus_dir == Path("outputs/corpus")
    assert s.embeddings_dir == Path("outputs/embeddings")
    assert s.projections_dir == Path("outputs/projections")
    assert s.logs_dir == Path("outputs/logs")


def test_env_override(monkeypatch):
    monkeypatch.setenv("MYTHO_CORPUS_DIR", "/tmp/my_corpus")
    monkeypatch.setenv("MYTHO_LOG_LEVEL", "DEBUG")

    from settings import Settings

    s = Settings()
    assert s.corpus_dir == Path("/tmp/my_corpus")
    assert s.log_level == "DEBUG"


def test_env_override_embeddings_dir(monkeypatch):
    monkeypatch.setenv("MYTHO_EMBEDDINGS_DIR", "/data/embeddings")

    from settings import Settings

    s = Settings()
    assert s.embeddings_dir == Path("/data/embeddings")
# (embedding-default and active-model assertions live authoritatively in
# test_config_manager.py and test_model_registry.py — not duplicated here.)
