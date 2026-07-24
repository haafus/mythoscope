from click.testing import CliRunner

from cli import mytho

runner = CliRunner()


class TestMythoTopLevel:
    def test_help(self):
        result = runner.invoke(mytho, ["--help"])
        assert result.exit_code == 0
        assert "MythoScope" in result.output

    def test_lists_all_commands(self):
        result = runner.invoke(mytho, ["--help"])
        for cmd in ["build", "status", "clean", "refresh", "export", "server"]:
            assert cmd in result.output


class TestStatusCommand:
    def test_help(self):
        result = runner.invoke(mytho, ["status", "--help"])
        assert result.exit_code == 0
        # Scope is the single addressing mechanism across the pipeline commands.
        assert "SCOPE" in result.output.upper()


class TestCleanCommand:
    def test_help(self):
        result = runner.invoke(mytho, ["clean", "--help"])
        assert result.exit_code == 0
        assert "--apply" in result.output


class TestServerCommand:
    def test_help(self):
        result = runner.invoke(mytho, ["server", "--help"])
        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output


class TestBuildCommand:
    def test_help(self):
        result = runner.invoke(mytho, ["build", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output
        # Stages are addressed by scope, not a dedicated option.
        assert "SCOPE" in result.output.upper()


class TestRefreshCommand:
    def test_help(self):
        result = runner.invoke(mytho, ["refresh", "--help"])
        assert result.exit_code == 0
        assert "--apply" in result.output

    def test_listed_in_top_level(self):
        result = runner.invoke(mytho, ["--help"])
        assert "refresh" in result.output

    def test_rejects_unknown_target(self):
        result = runner.invoke(mytho, ["refresh", "banana"])
        assert result.exit_code != 0

    def test_documents_preview(self, monkeypatch):
        # Preview renders the RefreshResult without touching the network directly.
        from corpus.refresh import RefreshResult

        monkeypatch.setattr("corpus.refresh.refresh_corpus",
                            lambda **kw: RefreshResult(unchanged=2, changed=["A"]))
        result = runner.invoke(mytho, ["refresh", "documents"])
        assert result.exit_code == 0
        assert "changed" in result.output
        assert "--apply" in result.output

    def test_summary_flags_kept_pinned_not_all_clear(self, monkeypatch):
        # A degraded/unreachable source must not be summarised as "everything current".
        from corpus.refresh import RefreshResult

        monkeypatch.setattr("corpus.refresh.refresh_corpus",
                            lambda **kw: RefreshResult(degraded=[("A", "empty-body")]))
        result = runner.invoke(mytho, ["refresh", "documents", "--apply"])
        assert result.exit_code == 0
        assert "kept pinned" in result.output
        assert "everything current" not in result.output

    def test_motifs_preview_does_not_refetch(self, monkeypatch):
        called = []
        monkeypatch.setattr("cli._build_motifs", lambda **kw: called.append(kw))
        result = runner.invoke(mytho, ["refresh", "motifs"])
        assert result.exit_code == 0
        assert called == []  # preview only, no re-scrape
