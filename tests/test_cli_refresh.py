"""`mytho refresh` scope resolution + the §9 per-source table, and that motifs fans out to each
source's own refresh (no network — the stage refresh is stubbed)."""

import pytest

import cli
from motifs.refresh import CHANGED, DEGRADED, NEW, NOT_CHANGED, Outcome, RefreshResult


def test_scope_resolution():
    assert cli._resolve_refresh(()) == (True, ["berezkin", "tmi", "atu"])          # all
    assert cli._resolve_refresh(("corpus",)) == (True, None)                        # corpus only
    assert cli._resolve_refresh(("motifs",)) == (False, ["berezkin", "tmi", "atu"])  # all sources
    assert cli._resolve_refresh(("motifs:source:atu",)) == (False, ["atu"])         # one source
    # multiple picks come back in canonical order, corpus alongside
    assert cli._resolve_refresh(("motifs:source:tmi", "corpus", "motifs:source:berezkin")) \
        == (True, ["berezkin", "tmi"])


@pytest.mark.parametrize("bad", ["bogus", "motifs:source:xyz", "graphs"])
def test_scope_rejects_unknown(bad):
    with pytest.raises(ValueError):
        cli._resolve_refresh((bad,))


def test_table_preview_lists_actionable_and_footer(capsys):
    r = RefreshResult(outcomes=[Outcome("res_changed", CHANGED), Outcome("res_degraded", DEGRADED),
                                Outcome("res_unchanged", NOT_CHANGED), Outcome("res_new", NEW)])
    cli._render_refresh_table(r, apply=False)
    out = capsys.readouterr().out
    assert "res_changed" in out and "adopt on apply" in out
    assert "res_degraded" in out and "keep cached" in out         # degraded row kept-pinned
    assert "res_unchanged" not in out                             # not-changed collapsed, not a row
    assert "4 checked: 1 changed, 1 degraded, 1 new, 1 not changed" in out
    assert "1 kept pinned" in out
    assert "adopt 2" in out                                       # changed + new pending


def test_table_apply_reports_adopted(capsys):
    r = RefreshResult(outcomes=[Outcome("a", CHANGED)], adopted=["a"])
    cli._render_refresh_table(r, apply=True)
    out = capsys.readouterr().out
    assert "adopted 1 — run `mytho build`" in out


def test_refresh_motifs_dispatches_per_source(monkeypatch, capsys):
    called = []

    def fake_refresh(self, *, apply=False):
        called.append((self.source, apply))
        return RefreshResult(outcomes=[Outcome(f"{self.source}/x", NOT_CHANGED)])

    from pipeline.stages.motifs import AtuSource, BerezkinSource, TmiSource
    for cls in (BerezkinSource, TmiSource, AtuSource):
        monkeypatch.setattr(cls, "refresh", fake_refresh)

    cli._refresh_motifs(apply=True, sources=["tmi", "atu"])
    assert called == [("tmi", True), ("atu", True)]              # only the selected sources, each its own
    out = capsys.readouterr().out
    assert "motifs:source:tmi" in out and "motifs:source:atu" in out
    assert "motifs:source:berezkin" not in out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
