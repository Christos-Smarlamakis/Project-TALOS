# -*- coding: utf-8 -*-
"""
Module: test_rate_limiter.py
Project: TALOS v5.24.0
Description:
    Unit tests for the proactive token-bucket rate limiter
    (src/services/cognitive_mesh/rate_limiter.py). Verifies the mathematical
    refill model, token exhaustion, infinite local rate, and smooth micro-sleep
    delay computation using an injectable clock and a recording sleep function.

Dependencies:
    - pytest: test framework.
    - src.services.cognitive_mesh.rate_limiter: TokenBucketRateLimiter and
      get_rate_specs.
"""

import pytest

from src.services.cognitive_mesh.rate_limiter import (
    TokenBucketRateLimiter,
    get_rate_specs,
)


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class TestRateSpecs:
    def test_specs_include_documented_providers(self):
        specs = get_rate_specs()
        assert specs["groq"] == 30.0
        assert specs["cerebras"] == 60.0
        assert specs["gemini"] == 15.0
        assert specs["sambanova"] == 20.0
        assert specs["deepseek"] == 60.0
        assert specs["openrouter"] == 20.0
        assert specs["ollama"] == float("inf")


class TestTokenBucketRateLimiter:
    def _make(self, clock):
        sleeps = []
        limiter = TokenBucketRateLimiter(
            sleep_fn=lambda d: sleeps.append(d), clock=clock
        )
        return limiter, sleeps

    def test_first_acquire_no_sleep(self):
        clock = _FakeClock()
        limiter, sleeps = self._make(clock)
        assert limiter.acquire("groq") == 0.0
        assert sleeps == []

    def test_token_exhaustion_requires_refill_delay(self):
        # groq refill rate r = 30/60 = 0.5 tokens/sec, capacity B = max(1.0, 0.5).
        clock = _FakeClock()
        limiter, sleeps = self._make(clock)
        assert limiter.acquire("groq") == 0.0  # consumes the single initial token
        # bucket now empty: next immediate request needs 1/0.5 = 2.0 seconds.
        assert limiter.acquire("groq") == pytest.approx(2.0, abs=1e-6)
        assert sleeps == [pytest.approx(2.0, abs=1e-6)]

    def test_refill_over_time_avoids_sleep(self):
        clock = _FakeClock()
        limiter, sleeps = self._make(clock)
        limiter.acquire("gemini")  # r = 15/60 = 0.25, capacity 1.0
        clock.advance(4.0)  # 4.0 * 0.25 = 1.0 token refilled
        assert limiter.acquire("gemini") == 0.0
        assert sleeps == []

    def test_ollama_unbounded_never_sleeps(self):
        clock = _FakeClock()
        limiter, sleeps = self._make(clock)
        for _ in range(100):
            assert limiter.acquire("ollama") == 0.0
        assert sleeps == []

    def test_provider_status_reports_fill(self):
        clock = _FakeClock()
        limiter, _ = self._make(clock)
        limiter.acquire("deepseek")  # r = 60/60 = 1.0, capacity 1.0
        status = limiter.get_provider_status()
        assert "deepseek" in status
        assert status["deepseek"]["rpm"] == 60.0
        assert status["deepseek"]["fill_pct"] == 0.0

    def test_case_insensitive_provider_name(self):
        clock = _FakeClock()
        limiter, sleeps = self._make(clock)
        assert limiter.acquire("GROQ") == 0.0
        assert limiter.acquire("groq") == pytest.approx(2.0, abs=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
