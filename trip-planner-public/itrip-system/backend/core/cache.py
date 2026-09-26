from cachetools import TTLCache
from typing import Any

import os
TTL = int(os.getenv("CACHE_TTL", "300"))
cache = TTLCache(maxsize=256, ttl=TTL)

def get_cache(key: str) -> Any | None:
    return cache.get(key)

def set_cache(key: str, value: Any) -> None:
    cache[key] = value
