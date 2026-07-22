"""Smoke tests for the one-off region-migration scripts (scripts/rekey_raw.py,
scripts/validate_migration.py). They run on the user's real data, so the core logic —
the sha1→blake2b re-key plan and the fail-loud gate — is pinned here."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import rekey_raw  # noqa: E402
import validate_migration as vm  # noqa: E402

from corpus.locator import document_id  # noqa: E402


def _sha1(url):
    return hashlib.sha1(url.encode()).hexdigest()


class TestRekeyPlan:
    def test_rename_then_idempotent(self, tmp_path):
        raw = tmp_path / "raw"
        raw.mkdir()
        url = "https://x/iliad"
        (raw / _sha1(url)).write_bytes(b"epic")  # pre-migration sha1-keyed raw
        config = [{"title": "Iliad", "url": url}]

        plan = rekey_raw.plan_rekey(config, raw)
        assert plan[0]["status"] == "rename"
        assert plan[0]["new"].name == document_id(url)

        plan[0]["old"].rename(plan[0]["new"])  # simulate --apply
        assert rekey_raw.plan_rekey(config, raw)[0]["status"] == "already-rekeyed"

    def test_document_id_collision_flagged(self, tmp_path):
        # Two locators normalizing to one id: the second is 'collision', never renamed.
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / _sha1("https://X.com/i/")).write_bytes(b"a")
        (raw / _sha1("https://x.com/i")).write_bytes(b"b")
        plan = rekey_raw.plan_rekey(
            [{"title": "A", "url": "https://X.com/i/"}, {"title": "B", "url": "https://x.com/i"}], raw)
        assert plan[0]["status"] == "rename"
        assert plan[1]["status"] == "collision"

    def test_missing_raw_is_flagged_not_fatal(self, tmp_path):
        raw = tmp_path / "raw"
        raw.mkdir()
        plan = rekey_raw.plan_rekey([{"title": "New", "url": "https://x/new"}], raw)
        assert plan[0]["status"] == "missing-raw"

    def test_bytes_preserved_by_rename(self, tmp_path):
        raw = tmp_path / "raw"
        raw.mkdir()
        url = "file:local.txt"
        (raw / _sha1(url)).write_bytes(b"body")
        plan = rekey_raw.plan_rekey([{"title": "L", "url": url}], raw)
        plan[0]["old"].rename(plan[0]["new"])
        assert plan[0]["new"].read_bytes() == b"body"  # same bytes, new name


class TestValidateGates:
    def _env(self, tmp_path, monkeypatch, tree, config):
        import json

        from settings import settings
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "traditions.json").write_text(json.dumps(tree))
        (cfg / "corpus.json").write_text(json.dumps(config))
        monkeypatch.setattr(settings, "config_dir", cfg)
        monkeypatch.setattr(settings, "corpus_dir", tmp_path / "corpus")

    def test_fail_loud_passes_valid(self, tmp_path, monkeypatch):
        self._env(tmp_path, monkeypatch,
                  {"Europe": {"traditions": {"Greek": {}}}},
                  [{"title": "Iliad", "tradition": "Greek", "url": "https://x/i"}])
        assert vm.gate_fail_loud() == []

    def test_fail_loud_flags_document_id_collision(self, tmp_path, monkeypatch):
        # Two docs whose locators normalize to one id (host case + trailing slash).
        self._env(tmp_path, monkeypatch,
                  {"Europe": {"traditions": {"Greek": {}}}},
                  [{"title": "A", "tradition": "Greek", "url": "https://X.com/i/"},
                   {"title": "B", "tradition": "Greek", "url": "https://x.com/i"}])
        problems = vm.gate_fail_loud()
        assert any("collision" in p for p in problems)

    def test_fail_loud_flags_unknown_tradition(self, tmp_path, monkeypatch):
        self._env(tmp_path, monkeypatch,
                  {"Europe": {"traditions": {"Greek": {}}}},
                  [{"title": "X", "tradition": "Klingon", "url": "https://x/k"}])
        assert vm.gate_fail_loud()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
