"""Unit tests for Redis cache security/performance hardening."""
import asyncio
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cache.redis_client import CacheManager, RedisCache


class FakeRedisClient:
    """Small async fake for Redis operations used by cache tests."""

    def __init__(self):
        self.store = {}
        self.deleted_keys = []

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, ttl, value):
        self.store[key] = value
        return True

    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                self.deleted_keys.append(key)
                deleted += 1
        return deleted

    async def scan_iter(self, match, count=200):
        for key in list(self.store.keys()):
            if fnmatch.fnmatch(key, match):
                yield key

    async def keys(self, _pattern):
        raise AssertionError("delete_pattern must not call KEYS")


class FakeCacheLookup:
    """Fake cache used to validate key lookup order and legacy fallback."""

    def __init__(self, legacy_key, legacy_value):
        self.legacy_key = legacy_key
        self.legacy_value = legacy_value
        self.calls = []

    async def get(self, key, prefix):
        self.calls.append((key, prefix))
        if key == self.legacy_key:
            return self.legacy_value
        return None


def test_set_and_get_uses_safe_json_envelope():
    cache = RedisCache()
    cache.redis_client = FakeRedisClient()

    payload = {"a": 1, "b": [1, 2, 3]}
    success = asyncio.run(cache.set("k1", payload, "api", ttl=30))

    assert success is True
    raw = cache.redis_client.store["api:k1"]
    parsed = json.loads(raw)
    assert parsed["__cache_format"] == "json-v1"
    assert parsed["value"] == payload

    loaded = asyncio.run(cache.get("k1", "api"))
    assert loaded == payload


def test_get_fallbacks_for_legacy_json_and_non_json_values():
    cache = RedisCache()
    cache.redis_client = FakeRedisClient()
    cache.redis_client.store["api:legacy_json"] = '{"x": 10}'
    cache.redis_client.store["api:legacy_raw"] = "not-json-at-all"

    legacy_json = asyncio.run(cache.get("legacy_json", "api"))
    legacy_raw = asyncio.run(cache.get("legacy_raw", "api"))

    assert legacy_json == {"x": 10}
    assert legacy_raw == "not-json-at-all"


def test_delete_pattern_uses_scan_iter_and_deletes_matching_keys():
    cache = RedisCache()
    cache.redis_client = FakeRedisClient()
    cache.redis_client.store = {
        "api:/v1/a": "1",
        "api:/v1/b": "2",
        "other:/v1/c": "3",
    }

    deleted = asyncio.run(cache.delete_pattern("/v1/*", "api"))

    assert deleted == 2
    assert "api:/v1/a" not in cache.redis_client.store
    assert "api:/v1/b" not in cache.redis_client.store
    assert "other:/v1/c" in cache.redis_client.store


def test_get_cached_api_response_falls_back_to_legacy_key():
    manager = CacheManager()
    params = {"b": 2, "a": 1}
    legacy_hash = hash(str(sorted(params.items())))
    legacy_key = f"/endpoint:{legacy_hash}"
    manager.cache = FakeCacheLookup(legacy_key=legacy_key, legacy_value={"ok": True})

    value = asyncio.run(manager.get_cached_api_response("/endpoint", params))

    assert value == {"ok": True}
    assert len(manager.cache.calls) == 2


def test_stable_hash_is_deterministic_for_reordered_dicts():
    manager = CacheManager()

    hash_a = manager._stable_hash({"endpoint": "/x", "params": {"a": 1, "b": 2}})
    hash_b = manager._stable_hash({"params": {"b": 2, "a": 1}, "endpoint": "/x"})

    assert hash_a == hash_b
