"""
Tests for the cache service.

Covers: LRUDict eviction semantics, CacheService image/assessment/prompt
caching (memory + disk), hash helpers, and stats/clear utilities.
"""

import pytest
from app.services.cache_service import LRUDict, CacheService


# ─── LRUDict ─────────────────────────────────────────────────────────

class TestLRUDict:
    def test_set_and_get(self):
        d = LRUDict(max_size=3)
        d["a"] = 1
        assert d["a"] == 1

    def test_evicts_oldest_when_full(self):
        d = LRUDict(max_size=2)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3  # should evict "a"
        assert "a" not in d
        assert d["b"] == 2
        assert d["c"] == 3

    def test_access_does_not_move_to_end(self):
        # NOTE: LRUDict.__getitem__ is not overridden, so reads do NOT update
        # recency. This documents the current (arguably buggy) behaviour —
        # only writes/reassigns affect eviction order.
        d = LRUDict(max_size=2)
        d["a"] = 1
        d["b"] = 2
        _ = d["a"]  # read does NOT move "a" to end
        d["c"] = 3  # evicts oldest = "a" (not "b")
        assert "b" in d
        assert "a" not in d

    def test_reassign_moves_to_end(self):
        d = LRUDict(max_size=2)
        d["a"] = 1
        d["b"] = 2
        d["a"] = 10  # reassign → "a" moves to end, "b" becomes oldest
        d["c"] = 3
        assert d["a"] == 10
        assert "b" not in d

    def test_respects_max_size_boundary(self):
        d = LRUDict(max_size=1)
        d["a"] = 1
        d["b"] = 2
        assert len(d) == 1
        assert "a" not in d


# ─── CacheService: hash helpers ──────────────────────────────────────

class TestHashHelpers:
    def test_hash_bytes_deterministic(self):
        h1 = CacheService.hash_bytes(b"hello")
        h2 = CacheService.hash_bytes(b"hello")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_bytes_different_input(self):
        assert CacheService.hash_bytes(b"a") != CacheService.hash_bytes(b"b")

    def test_hash_dict_deterministic(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        # Order-independent
        assert CacheService.hash_dict(d1) == CacheService.hash_dict(d2)

    def test_hash_dict_different_values(self):
        assert CacheService.hash_dict({"a": 1}) != CacheService.hash_dict({"a": 2})


# ─── CacheService: image cache ───────────────────────────────────────

class TestImageCache:
    @pytest.mark.asyncio
    async def test_put_then_get_memory(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        data = b"\x89PNG fake image bytes"
        h = CacheService.hash_bytes(data)
        await cache.put_image(h, data)
        result = await cache.get_image(h)
        assert result == data

    @pytest.mark.asyncio
    async def test_miss_returns_none(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        assert await cache.get_image("nonexistent") is None

    @pytest.mark.asyncio
    async def test_survives_memory_clear_via_disk(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        data = b"image data here"
        h = CacheService.hash_bytes(data)
        await cache.put_image(h, data)
        cache.clear_memory()
        # Should still hit disk
        result = await cache.get_image(h)
        assert result == data


# ─── CacheService: assessment cache ──────────────────────────────────

class TestAssessmentCache:
    @pytest.mark.asyncio
    async def test_put_then_get_assessment(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        payload = {"score": 85, "level": "L3", "dimension": "counting"}
        h = "ws_hash_123"
        await cache.put_assessment(h, payload)
        assert await cache.get_assessment(h) == payload

    @pytest.mark.asyncio
    async def test_assessment_miss_returns_none(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        assert await cache.get_assessment("nope") is None

    @pytest.mark.asyncio
    async def test_assessment_survives_memory_clear(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        payload = {"score": 50}
        h = "ws_hash_456"
        await cache.put_assessment(h, payload)
        cache.clear_memory()
        assert await cache.get_assessment(h) == payload


# ─── CacheService: prompt cache ──────────────────────────────────────

class TestPromptCache:
    def test_put_then_get_prompt(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        cache.put_prompt("p1", "You are a teacher.")
        assert cache.get_prompt("p1") == "You are a teacher."

    def test_prompt_miss_returns_none(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        assert cache.get_prompt("missing") is None


# ─── CacheService: stats & clear ─────────────────────────────────────

class TestStatsAndClear:
    @pytest.mark.asyncio
    async def test_stats_reflect_state(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        await cache.put_image("h1", b"data")
        cache.put_prompt("p1", "prompt")
        stats = cache.stats()
        assert stats["memory"]["images"] == 1
        assert stats["memory"]["prompts"] == 1
        assert "disk" in stats

    @pytest.mark.asyncio
    async def test_clear_memory_resets_counts(self, tmp_path):
        cache = CacheService(cache_dir=str(tmp_path / "cache"))
        await cache.put_image("h1", b"data")
        await cache.put_assessment("a1", {"x": 1})
        cache.put_prompt("p1", "prompt")
        counts = cache.clear_memory()
        assert counts["images"] == 1
        assert counts["assessments"] == 1
        assert counts["prompts"] == 1
        # All memory caches now empty
        assert cache.stats()["memory"]["images"] == 0

    def test_creates_cache_directories(self, tmp_path):
        cache_dir = tmp_path / "newcache"
        CacheService(cache_dir=str(cache_dir))
        assert (cache_dir / "images").is_dir()
        assert (cache_dir / "assessments").is_dir()
