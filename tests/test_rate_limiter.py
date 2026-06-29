import logging

import pytest

from llm import rate_limiter as rl
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

    def test_success_decays_breaker(self):
        g = RateGovernor("m", breaker_threshold=2)
        g.note_rate_limited()
        g.note_success()
        assert g.note_rate_limited() is False  # pressure decayed below threshold

    def test_breaker_trips_despite_interleaved_successes(self):
        # A steady 429 wall must still trip even if some requests succeed in between;
        # a hard reset-on-success would never trip here.
        g = RateGovernor("m", breaker_threshold=4)
        for _ in range(3):
            g.note_rate_limited()  # pressure 3
        g.note_success()  # decay -> 2 (a reset would drop to 0)
        assert g.note_rate_limited() is False  # 3
        assert g.note_rate_limited() is True  # 4 -> trips

    def test_refund_returns_token_estimate(self):
        g = RateGovernor("m", tpm=1000)
        g.acquire(800)
        g.refund(800)  # estimate returned; bucket back near capacity
        assert g._tok_bucket.acquire(900) == 0.0  # would wait if the 800 weren't refunded

    def test_reconcile_tracks_tokens(self):
        g = RateGovernor("m", tpm=100000)
        g.acquire(500)
        g.reconcile(500, 800)
        assert g.stats()["tokens"] == 800

    def test_summary_shows_utilization_with_limits(self):
        g = RateGovernor("m", rpm=500, tpm=200000)
        g.acquire(1000)
        g.reconcile(1000, 1500)
        s = g.summary()
        assert "requests" in s and "% TPM" in s and "% RPM" in s

    def test_summary_omits_percent_without_limits(self):
        s = RateGovernor("m").summary()
        assert "TPM" not in s and "RPM" not in s

    def test_acquire_logs_usage_periodically(self, caplog):
        g = RateGovernor("m", rpm=100000, tpm=100000)
        with caplog.at_level(logging.INFO, logger="llm.rate_limiter"):
            for _ in range(rl.USAGE_LOG_EVERY):
                g.acquire(10)
        assert "LLM usage" in caplog.text


class TestGetGovernor:
    def test_singleton_per_key(self):
        a = get_governor("k1::model", "model", rpm=10)
        b = get_governor("k1::model", "model", rpm=10)
        assert a is b

    def test_distinct_keys(self):
        a = get_governor("k2::model", "model")
        b = get_governor("k3::model", "model")
        assert a is not b
