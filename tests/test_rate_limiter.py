import pytest

from llm.rate_limiter import DailyLimitReached, RateGovernor, TokenBucket, get_governor


class TestTokenBucket:
    def test_acquire_within_capacity_no_wait(self):
        b = TokenBucket(100)
        assert b.acquire(50) == 0.0
        assert b.acquire(50) == 0.0

    def test_over_capacity_waits(self):
        b = TokenBucket(10, refill_per_sec=1000.0)  # fast refill so the test stays quick
        b.acquire(10)  # drain
        waited = b.acquire(5)  # must wait for ~5 tokens to refill
        assert waited > 0

    def test_adjust_refunds(self):
        b = TokenBucket(10, refill_per_sec=0.0)  # no refill: isolate adjust()
        b.acquire(10)
        b.adjust(-10)  # refund everything
        assert b.acquire(10) == 0.0


class TestRateGovernor:
    def test_disabled_without_limits(self):
        g = RateGovernor("m")
        assert not g.enabled
        g.acquire(1000)  # no buckets -> no-op, no raise

    def test_enabled_with_any_limit(self):
        assert RateGovernor("m", rpm=10).enabled
        assert RateGovernor("m", tpm=1000).enabled

    def test_breaker_trips_and_blocks(self):
        g = RateGovernor("m", rpm=1000, breaker_threshold=2)
        assert g.note_rate_limited() is False
        assert g.note_rate_limited() is True  # trips on the threshold
        assert g.tripped
        with pytest.raises(DailyLimitReached):
            g.acquire(1)

    def test_success_resets_breaker(self):
        g = RateGovernor("m", breaker_threshold=2)
        g.note_rate_limited()
        g.note_success()
        assert g.note_rate_limited() is False  # counter was reset, not tripped

    def test_reconcile_tracks_tokens(self):
        g = RateGovernor("m", tpm=100000)
        g.acquire(500)
        g.reconcile(500, 800)
        assert g.stats()["tokens"] == 800


class TestGetGovernor:
    def test_singleton_per_key(self):
        a = get_governor("k1::model", "model", rpm=10)
        b = get_governor("k1::model", "model", rpm=10)
        assert a is b

    def test_distinct_keys(self):
        a = get_governor("k2::model", "model")
        b = get_governor("k3::model", "model")
        assert a is not b
