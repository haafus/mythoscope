import pytest

from llm.concurrency import map_concurrent
from llm.rate_limiter import DailyLimitReached


def test_empty_returns_completed():
    assert map_concurrent([], lambda x: x, 2) is True


def test_runs_all_items():
    results = []
    completed = map_concurrent(
        [1, 2, 3], lambda x: x * 2, 2, on_result=lambda item, r: results.append(r)
    )
    assert completed is True
    assert sorted(results) == [2, 4, 6]


def test_on_result_receives_item_and_result():
    pairs = []
    map_concurrent([1, 2], lambda x: x + 10, 1, on_result=lambda item, r: pairs.append((item, r)))
    assert sorted(pairs) == [(1, 11), (2, 12)]


def test_stops_on_daily_limit():
    seen = []

    def fn(x):
        if x == 2:
            raise DailyLimitReached("stop")
        return x

    # concurrency=1 keeps completion order deterministic
    completed = map_concurrent([1, 2, 3, 4], fn, 1, on_result=lambda item, r: seen.append(item))
    assert completed is False
    assert 1 in seen  # first item processed
    assert 3 not in seen and 4 not in seen  # pending work cancelled


def test_other_exceptions_propagate():
    def fn(x):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        map_concurrent([1], fn, 1)


def test_keyboard_interrupt_propagates_with_hint(caplog):
    def fn(x):
        raise KeyboardInterrupt

    with caplog.at_level("WARNING", logger="llm.concurrency"), pytest.raises(KeyboardInterrupt):
        map_concurrent([1], fn, 1)
    assert "Interrupted" in caplog.text
