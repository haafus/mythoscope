import logging
import threading
import time

logger = logging.getLogger(__name__)

# How often (in requests) the governor logs a mid-run usage/utilization snapshot.
USAGE_LOG_EVERY = 25


class DailyLimitReached(Exception):
    """Rate limiting is no longer recovering (likely a daily quota) — stop the run cleanly.

    Distinct from FatalLLMError: not a failure, just "come back later". Persistent
    caches let the next run resume where this one stopped.
    """


class TokenBucket:
    """Thread-safe token bucket.

    Holds up to `capacity` tokens, refilled continuously at `capacity/60` per second
    (i.e. capacity is a per-minute budget). A larger refill rate can be passed for
    tests so waits stay short.
    """

    def __init__(self, capacity: float, refill_per_sec: float | None = None) -> None:
        self.capacity = float(capacity)
        self.rate = refill_per_sec if refill_per_sec is not None else self.capacity / 60.0
        self._level = float(capacity)
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        self._level = min(self.capacity, self._level + (now - self._updated) * self.rate)
        self._updated = now

    def acquire(self, amount: float) -> float:
        """Block until `amount` tokens are available, then consume them; return seconds waited.

        A request larger than the whole bucket can never fully fit, so we only wait
        for it to fill to capacity, then let the level go negative — future acquires
        simply wait longer while it refills.
        """
        target = min(amount, self.capacity)
        waited = 0.0
        while True:
            with self._lock:
                self._refill()
                if self._level >= target:
                    self._level -= amount
                    return waited
                sleep_for = (target - self._level) / self.rate
            time.sleep(sleep_for)
            waited += sleep_for

    def adjust(self, delta: float) -> None:
        """Correct consumption after the fact (delta > 0 consumes more, delta < 0 refunds)."""
        with self._lock:
            self._refill()
            self._level -= delta


class RateGovernor:
    """Per-model request/token rate limiter plus a rate-limit circuit breaker.

    Two buckets enforce RPM and TPM directly (token cost is reconciled against the
    actual `usage` reported by the response). When configured limits are absent the
    buckets are disabled and only the breaker stays active, so an unconfigured
    provider still stops cleanly if it keeps returning 429s.
    """

    def __init__(
        self,
        model: str,
        rpm: int | None = None,
        tpm: int | None = None,
        rpd: int | None = None,
        breaker_threshold: int = 3,
    ) -> None:
        self.model = model
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd
        self._req_bucket = TokenBucket(rpm) if rpm else None
        self._tok_bucket = TokenBucket(tpm) if tpm else None
        self._breaker_threshold = breaker_threshold

        self._lock = threading.Lock()
        self._consecutive_rl = 0
        self._tripped = False

        # metrics
        self._start = time.monotonic()
        self._requests = 0
        self._tokens = 0
        self._est_tokens = 0
        self._wait = 0.0

    @property
    def enabled(self) -> bool:
        return self._req_bucket is not None or self._tok_bucket is not None

    @property
    def tripped(self) -> bool:
        return self._tripped

    def acquire(self, est_tokens: int) -> None:
        """Reserve capacity for one request before sending it.

        Raises DailyLimitReached if the breaker has tripped.
        """
        if self._tripped:
            raise DailyLimitReached(f"rate limit not recovering for {self.model}")
        waited = 0.0
        if self._req_bucket is not None:
            waited += self._req_bucket.acquire(1)
        if self._tok_bucket is not None:
            waited += self._tok_bucket.acquire(est_tokens)
        with self._lock:
            self._requests += 1
            self._est_tokens += est_tokens
            self._wait += waited
            should_log = self._requests % USAGE_LOG_EVERY == 0
        # summary() takes the same lock, so log outside the critical section.
        if should_log:
            logger.info("LLM usage [%s]: %s", self.model, self.summary())

    def reconcile(self, est_tokens: int, actual_tokens: int) -> None:
        """Correct the token bucket once the real usage is known."""
        if actual_tokens:
            if self._tok_bucket is not None:
                self._tok_bucket.adjust(actual_tokens - est_tokens)
            with self._lock:
                self._tokens += actual_tokens

    def note_success(self) -> None:
        with self._lock:
            self._consecutive_rl = 0

    def note_rate_limited(self) -> bool:
        """Record a call that exhausted its retries on a rate-limit error.

        Returns True if this tripped the breaker.
        """
        with self._lock:
            self._consecutive_rl += 1
            if not self._tripped and self._consecutive_rl >= self._breaker_threshold:
                self._tripped = True
                logger.warning(
                    "Rate limit not recovering after %d calls for %s; stopping run",
                    self._consecutive_rl,
                    self.model,
                )
            return self._tripped

    def stats(self) -> dict:
        with self._lock:
            elapsed = max(time.monotonic() - self._start, 1e-9)
            return {
                "requests": self._requests,
                "tokens": self._tokens,
                "req_per_min": self._requests / elapsed * 60.0,
                "tokens_per_min": self._tokens / elapsed * 60.0,
                "wait_fraction": self._wait / elapsed,
                "est_error": (self._est_tokens - self._tokens) / self._tokens if self._tokens else 0.0,
            }

    def summary(self) -> str:
        """One-line usage summary; shows %-of-limit utilization where limits are set."""
        s = self.stats()
        parts = [f"{s['requests']} requests", f"{s['tokens']:,} tokens", f"~{s['req_per_min']:.0f} req/min"]
        if self.tpm:
            parts.append(f"{s['tokens_per_min'] / self.tpm * 100:.0f}% TPM")
        if self.rpm:
            parts.append(f"{s['req_per_min'] / self.rpm * 100:.0f}% RPM")
        parts.append(f"throttled {s['wait_fraction'] * 100:.0f}%")
        return ", ".join(parts)


_governors: dict[str, RateGovernor] = {}
_governors_lock = threading.Lock()


def get_governor(
    key: str,
    model: str,
    rpm: int | None = None,
    tpm: int | None = None,
    rpd: int | None = None,
) -> RateGovernor:
    """Return the process-wide governor for `key` (one shared budget per model)."""
    with _governors_lock:
        gov = _governors.get(key)
        if gov is None:
            gov = RateGovernor(model, rpm, tpm, rpd)
            _governors[key] = gov
            if gov.enabled:
                logger.info(
                    "Rate limits for %s: RPM=%s, TPM=%s%s",
                    model,
                    rpm,
                    tpm,
                    f", RPD={rpd} (reference)" if rpd else "",
                )
            else:
                logger.info("No rate limits configured for %s — concurrency only", model)
        return gov
