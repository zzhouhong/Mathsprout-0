"""
Tests for the token-bucket rate limiter.
Run: cd backend; python -m pytest tests/test_rate_limiter.py -v
"""

import time
import pytest
from app.core.rate_limiter import TokenBucket, Tier, RateLimiter, _get_tier_for_path


class TestTokenBucket:
    """Unit tests for the TokenBucket algorithm."""

    def test_initial_capacity(self):
        bucket = TokenBucket(rate=1.0, capacity=5.0)
        assert bucket.available == pytest.approx(5.0)

    def test_consume_allows_up_to_capacity(self):
        bucket = TokenBucket(rate=0.0, capacity=5.0)  # zero refill
        for _ in range(5):
            assert bucket.consume() is True
        # 6th should fail
        assert bucket.consume() is False

    def test_consume_refills_over_time(self):
        bucket = TokenBucket(rate=100.0, capacity=5.0)  # 100 tokens/sec
        # Consume all
        for _ in range(5):
            bucket.consume()
        assert bucket.available < 1.0
        # Wait for refill
        time.sleep(0.06)  # ~6 tokens refilled
        assert bucket.available > 1.0
        assert bucket.consume() is True

    def test_capacity_caps_refill(self):
        bucket = TokenBucket(rate=1000.0, capacity=3.0)
        time.sleep(0.1)  # would refill 100 tokens, but capped at 3
        assert bucket.available == pytest.approx(3.0)

    def test_consume_cost_greater_than_one(self):
        bucket = TokenBucket(rate=0.0, capacity=5.0)
        assert bucket.consume(cost=3.0) is True
        assert bucket.available == pytest.approx(2.0)
        assert bucket.consume(cost=3.0) is False  # not enough


class TestTierRouting:
    """Test that paths route to the correct tier."""

    def test_analysis_routes_to_ai(self):
        tier = _get_tier_for_path("/api/v1/analysis/demo-assessment")
        assert tier.name == "ai"

    def test_worksheets_routes_to_ai(self):
        tier = _get_tier_for_path("/api/v1/worksheets/upload")
        assert tier.name == "ai"

    def test_auth_routes_to_auth(self):
        tier = _get_tier_for_path("/api/v1/auth/login")
        assert tier.name == "auth"

    def test_children_routes_to_default(self):
        tier = _get_tier_for_path("/api/v1/children")
        assert tier.name == "default"

    def test_health_check_to_default(self):
        tier = _get_tier_for_path("/api/health")
        assert tier.name == "default"


class TestRateLimiter:
    """Integration-style tests for the RateLimiter middleware class."""

    def test_client_key_uses_x_forwarded_for(self):
        from unittest.mock import MagicMock
        limiter = RateLimiter()
        mock_req = MagicMock()
        mock_req.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        assert limiter._client_key(mock_req) == "10.0.0.1"

    def test_client_key_falls_back_to_client_host(self):
        from unittest.mock import MagicMock
        limiter = RateLimiter()
        mock_req = MagicMock()
        mock_req.headers = {}
        mock_req.client.host = "127.0.0.1"
        assert limiter._client_key(mock_req) == "127.0.0.1"

    def test_bucket_is_reused_for_same_key(self):
        limiter = RateLimiter()
        tier = Tier(name="test", rate=1.0, capacity=5, window_human="test")
        b1 = limiter._get_bucket("test:10.0.0.1", tier)
        b2 = limiter._get_bucket("test:10.0.0.1", tier)
        assert b1 is b2

    def test_buckets_differ_per_ip(self):
        limiter = RateLimiter()
        tier = Tier(name="test", rate=1.0, capacity=5, window_human="test")
        b1 = limiter._get_bucket("test:10.0.0.1", tier)
        b2 = limiter._get_bucket("test:10.0.0.2", tier)
        assert b1 is not b2
