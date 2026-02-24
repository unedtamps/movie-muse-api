import os

from flask_caching import Cache

# Cache 1: Fast cache (1 hour timeout)
cache = Cache(
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": os.environ.get("REDIS_HOST", "localhost"),
        "CACHE_REDIS_PORT": int(os.environ.get("REDIS_PORT", "6379")),
        "CACHE_REDIS_DB": 0,
        "CACHE_DEFAULT_TIMEOUT": 360,  # 1 hour
    }
)

# Cache 2: Slow cache (24 hours timeout)
cache_slow = Cache(
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": os.environ.get("REDIS_SLOW_HOST", os.environ.get("REDIS_HOST", "localhost")),
        "CACHE_REDIS_PORT": int(os.environ.get("REDIS_SLOW_PORT", os.environ.get("REDIS_PORT", "6378"))),
        "CACHE_REDIS_DB": 1,
        "CACHE_DEFAULT_TIMEOUT": 604800,  # 24 hours
    }
)
