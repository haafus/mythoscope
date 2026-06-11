import importlib.util
import os
import sys
import time
import types

psutil_stub = types.ModuleType("psutil")
psutil_stub.Process = type("Process", (), {  # type: ignore[attr-defined]
    "memory_info": lambda self: types.SimpleNamespace(rss=100 * 1024 * 1024)
})
psutil_stub.NoSuchProcess = type("NoSuchProcess", (Exception,), {})  # type: ignore[attr-defined]
psutil_stub.AccessDenied = type("AccessDenied", (Exception,), {})  # type: ignore[attr-defined]
sys.modules["psutil"] = psutil_stub

_spec = importlib.util.spec_from_file_location(
    "02_embed.performance_metrics",
    os.path.join(os.path.dirname(__file__), "..", "src", "02_embed", "performance_metrics.py"),
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

PerformanceMetrics = _mod.PerformanceMetrics


class TestPerformanceMetrics:
    def test_start_and_end_operation(self):
        pm = PerformanceMetrics(track_memory=False)
        pm.start_operation("test_op")
        result = pm.end_operation("test_op")
        assert "duration_seconds" in result
        assert result["duration_seconds"] >= 0

    def test_track_context_manager(self):
        pm = PerformanceMetrics(track_memory=False)
        with pm.track("ctx_op"):
            time.sleep(0.01)
        summary = pm.get_summary("ctx_op")
        assert summary["total_operations"] == 1
        assert summary["total_time_seconds"] >= 0.01

    def test_get_summary_empty(self):
        pm = PerformanceMetrics(track_memory=False)
        assert pm.get_summary("nonexistent") == {}

    def test_get_summary_multiple_operations(self):
        pm = PerformanceMetrics(track_memory=False)
        for _ in range(3):
            pm.start_operation("multi")
            pm.end_operation("multi")
        summary = pm.get_summary("multi")
        assert summary["total_operations"] == 3

    def test_reset(self):
        pm = PerformanceMetrics(track_memory=False)
        pm.start_operation("op")
        pm.end_operation("op")
        pm.reset()
        assert pm.get_summary("op") == {}
        assert pm.current_operation is None

    def test_end_operation_without_start(self):
        pm = PerformanceMetrics(track_memory=False)
        result = pm.end_operation("no_start")
        assert result == {}

    def test_get_summary_all_operations(self):
        pm = PerformanceMetrics(track_memory=False)
        with pm.track("a"):
            pass
        with pm.track("b"):
            pass
        summary = pm.get_summary()
        assert summary["total_operations"] == 2
