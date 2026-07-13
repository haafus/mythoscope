from log_setup import _prune_old_logs


def _make_logs(dir_, stamps):
    for s in stamps:
        (dir_ / f"app-{s}.log").write_text("x", encoding="utf-8")


def test_prune_keeps_newest_n(tmp_path):
    stamps = [f"20260101-0000{i:02d}-1" for i in range(5)]
    _make_logs(tmp_path, stamps)

    _prune_old_logs(tmp_path, keep=2)

    remaining = sorted(p.name for p in tmp_path.glob("app-*.log"))
    assert remaining == [f"app-{stamps[3]}.log", f"app-{stamps[4]}.log"]


def test_prune_keep_all_when_non_positive(tmp_path):
    _make_logs(tmp_path, ["20260101-000001-1", "20260101-000002-1"])

    _prune_old_logs(tmp_path, keep=0)

    assert len(list(tmp_path.glob("app-*.log"))) == 2


def test_prune_ignores_unrelated_files(tmp_path):
    _make_logs(tmp_path, ["20260101-000001-1", "20260101-000002-1", "20260101-000003-1"])
    # Legacy single log and any other file must survive: they don't match app-*.log.
    (tmp_path / "app.log").write_text("legacy", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("keep", encoding="utf-8")

    _prune_old_logs(tmp_path, keep=1)

    assert (tmp_path / "app.log").exists()
    assert (tmp_path / "notes.txt").exists()
    assert len(list(tmp_path.glob("app-*.log"))) == 1


def test_prune_never_raises_on_missing_dir(tmp_path):
    _prune_old_logs(tmp_path / "does-not-exist", keep=3)  # must not raise
