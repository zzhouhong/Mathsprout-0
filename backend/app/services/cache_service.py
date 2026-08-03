"""
Cache service for the math education agent.

Layered caching strategy:
1. In-memory LRU cache — hot results, instant lookup
2. Disk cache — processed images, survives restarts (I/O offloaded to thread pool)
3. Claude Ephemeral Cache — system prompt reuse (handled by worksheet_recognizer)

Usage:
    cache = CacheService(cache_dir="./cache", max_memory_entries=128)

    # Cache processed images
    cached = await cache.get_image(image_hash)
    if cached is None:
        processed = await process_image(raw)
        await cache.put_image(image_hash, processed)

    # Cache assessment results
    cached = await cache.get_assessment(worksheet_hash)
    if cached is None:
        assessment = await run_assessment(vision_result)
        await cache.put_assessment(worksheet_hash, assessment)
"""

import os
import json
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from collections import OrderedDict
from datetime import datetime, timedelta
import logging

import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

# Small thread pool for disk I/O offload
_IO_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)


class LRUDict(OrderedDict):
    """Simple LRU dict with max capacity."""
    def __init__(self, max_size: int = 128, *args, **kwargs):
        self.max_size = max_size
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.max_size:
            self.popitem(last=False)


class CacheService:
    """
    Layered cache for image processing and assessment results.

    In-memory cache for hot data, disk cache for durability across restarts.
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        max_memory_entries: int = 128,
        disk_cache_ttl_days: int = 7,
    ):
        self.cache_dir = Path(cache_dir)
        self.max_memory_entries = max_memory_entries
        self.disk_cache_ttl = timedelta(days=disk_cache_ttl_days)

        # In-memory caches
        self._image_cache = LRUDict(max_size=max_memory_entries)
        self._assessment_cache = LRUDict(max_size=max_memory_entries // 4)
        self._prompt_cache: Dict[str, str] = {}

        # Ensure cache directories exist
        (self.cache_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "assessments").mkdir(parents=True, exist_ok=True)

    # ─── Image Cache ──────────────────────────────────────────────────

    async def get_image(self, image_hash: str) -> Optional[bytes]:
        """Get processed image from cache."""
        # Check memory first
        if image_hash in self._image_cache:
            logger.debug(f"Image cache hit (memory): {image_hash[:16]}")
            return self._image_cache[image_hash]

        # Check disk
        disk_path = self.cache_dir / "images" / f"{image_hash}.png"
        if disk_path.exists():
            # Check TTL
            mtime = datetime.fromtimestamp(disk_path.stat().st_mtime)
            if datetime.now() - mtime < self.disk_cache_ttl:
                logger.debug(f"Image cache hit (disk): {image_hash[:16]}")
                loop = asyncio.get_running_loop()
                data = await loop.run_in_executor(_IO_POOL, disk_path.read_bytes)
                # Promote to memory
                self._image_cache[image_hash] = data
                return data
            else:
                # Expired — clean up
                await loop.run_in_executor(_IO_POOL, disk_path.unlink, True)

        return None

    async def put_image(self, image_hash: str, data: bytes) -> None:
        """Store processed image in cache."""
        # Memory
        self._image_cache[image_hash] = data

        # Disk (offloaded to thread pool)
        disk_path = self.cache_dir / "images" / f"{image_hash}.png"
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(_IO_POOL, disk_path.write_bytes, data)
        except OSError as e:
            logger.warning(f"Failed to write image cache: {e}")

    # ─── Assessment Cache ─────────────────────────────────────────────

    async def get_assessment(self, worksheet_hash: str) -> Optional[Dict]:
        """Get cached assessment result."""
        if worksheet_hash in self._assessment_cache:
            logger.debug(f"Assessment cache hit (memory): {worksheet_hash[:16]}")
            return self._assessment_cache[worksheet_hash]

        disk_path = self.cache_dir / "assessments" / f"{worksheet_hash}.json"
        if disk_path.exists():
            mtime = datetime.fromtimestamp(disk_path.stat().st_mtime)
            if datetime.now() - mtime < self.disk_cache_ttl:
                logger.debug(f"Assessment cache hit (disk): {worksheet_hash[:16]}")
                try:
                    loop = asyncio.get_running_loop()
                    text = await loop.run_in_executor(_IO_POOL, lambda: disk_path.read_text(encoding="utf-8"))
                    data = json.loads(text)
                    self._assessment_cache[worksheet_hash] = data
                    return data
                except (json.JSONDecodeError, OSError):
                    await loop.run_in_executor(_IO_POOL, disk_path.unlink, True)

        return None

    async def put_assessment(self, worksheet_hash: str, data: Dict) -> None:
        """Store assessment result in cache."""
        self._assessment_cache[worksheet_hash] = data

        disk_path = self.cache_dir / "assessments" / f"{worksheet_hash}.json"
        try:
            loop = asyncio.get_running_loop()
            text = json.dumps(data, ensure_ascii=False, default=str)
            await loop.run_in_executor(_IO_POOL, lambda: disk_path.write_text(text, encoding="utf-8"))
        except OSError as e:
            logger.warning(f"Failed to write assessment cache: {e}")

    # ─── Prompt Cache ─────────────────────────────────────────────────

    def get_prompt(self, prompt_hash: str) -> Optional[str]:
        """Get cached system prompt."""
        return self._prompt_cache.get(prompt_hash)

    def put_prompt(self, prompt_hash: str, prompt: str) -> None:
        """Cache a system prompt."""
        self._prompt_cache[prompt_hash] = prompt

    # ─── Utility ──────────────────────────────────────────────────────

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Compute SHA-256 hash for cache keys."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_dict(data: Dict) -> str:
        """Compute a stable hash for a dictionary."""
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    async def clear_expired(self) -> int:
        """Clear expired disk cache entries. Returns count removed."""
        removed = 0
        now = datetime.now()

        for subdir in ["images", "assessments"]:
            disk_dir = self.cache_dir / subdir
            if not disk_dir.exists():
                continue
            for entry in disk_dir.iterdir():
                if entry.is_file():
                    mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                    if now - mtime > self.disk_cache_ttl:
                        entry.unlink()
                        removed += 1

        return removed

    def clear_memory(self) -> Dict[str, int]:
        """Clear all in-memory caches. Returns counts per cache type."""
        counts = {
            "images": len(self._image_cache),
            "assessments": len(self._assessment_cache),
            "prompts": len(self._prompt_cache),
        }
        self._image_cache.clear()
        self._assessment_cache.clear()
        self._prompt_cache.clear()
        return counts

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        image_disk_count = 0
        image_disk_dir = self.cache_dir / "images"
        if image_disk_dir.exists():
            image_disk_count = sum(1 for _ in image_disk_dir.iterdir())

        assessment_disk_count = 0
        assessment_disk_dir = self.cache_dir / "assessments"
        if assessment_disk_dir.exists():
            assessment_disk_count = sum(1 for _ in assessment_disk_dir.iterdir())

        return {
            "memory": {
                "images": len(self._image_cache),
                "assessments": len(self._assessment_cache),
                "prompts": len(self._prompt_cache),
            },
            "disk": {
                "images": image_disk_count,
                "assessments": assessment_disk_count,
            },
            "max_memory_entries": self.max_memory_entries,
            "disk_ttl_days": self.disk_cache_ttl.days,
        }
