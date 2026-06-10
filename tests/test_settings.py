import os
from pathlib import Path

import pytest


def test_default_paths():
    from settings import Settings

    s = Settings()
    assert s.corpus_dir == Path("corpus")
    assert s.chroma_dir == Path("chroma_db")
    assert s.cache_dir == Path("cache")
    assert s.analysis_dir == Path("analysis")
    assert s.logs_dir == Path("logs")


def test_derived_paths():
    from settings import Settings

    s = Settings()
    assert s.corpus_metadata_path == Path("corpus/corpus_metadata.json")
    assert s.corpus_catalog_path == Path("corpus/corpus_catalog.csv")
    assert s.processed_urls_path == Path("corpus/processed_urls.json")


def test_model_output_dir():
    from settings import Settings

    s = Settings()
    assert s.model_output_dir("BAAI/bge-m3") == Path("analysis/BAAI_bge-m3")
    assert s.model_output_dir("sentence-transformers/LaBSE") == Path("analysis/sentence-transformers_LaBSE")


def test_env_override(monkeypatch):
    monkeypatch.setenv("MYTHO_CORPUS_DIR", "/tmp/my_corpus")
    monkeypatch.setenv("MYTHO_LOG_LEVEL", "DEBUG")

    from settings import Settings

    s = Settings()
    assert s.corpus_dir == Path("/tmp/my_corpus")
    assert s.log_level == "DEBUG"
    assert s.corpus_metadata_path == Path("/tmp/my_corpus/corpus_metadata.json")


def test_env_override_chroma(monkeypatch):
    monkeypatch.setenv("MYTHO_CHROMA_DIR", "/data/chroma")

    from settings import Settings

    s = Settings()
    assert s.chroma_dir == Path("/data/chroma")


def test_default_embedding_model():
    from settings import Settings

    s = Settings()
    assert s.default_embedding_model == "BAAI/bge-m3"
    assert s.default_chunking == "paragraph"


def test_ensure_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("MYTHO_CORPUS_DIR", str(tmp_path / "corpus"))
    monkeypatch.setenv("MYTHO_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("MYTHO_ANALYSIS_DIR", str(tmp_path / "analysis"))
    monkeypatch.setenv("MYTHO_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("MYTHO_GRAPHS_DIR", str(tmp_path / "graphs"))
    monkeypatch.setenv("MYTHO_CORPUS_CHUNKED_DIR", str(tmp_path / "chunked"))

    from settings import Settings

    s = Settings()
    s.ensure_dirs()

    assert (tmp_path / "corpus").is_dir()
    assert (tmp_path / "cache").is_dir()
    assert (tmp_path / "analysis").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "graphs").is_dir()
    assert (tmp_path / "chunked").is_dir()
