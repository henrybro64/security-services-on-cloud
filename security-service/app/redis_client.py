import os
import logging

import redis

logger = logging.getLogger("security-service.redis")

def get_redis_client() -> redis.Redis:
    """
    Create and return a Redis client.


    Works in two modes:

    1. Local dev (docker-compose):
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - REDIS_SSL=false
    - REDIS_PASSWORD not set

    2. Azure Cache for Redis:
    - REDIS_HOST=<your-redis-host>.redis.cache.windows.net
    - REDIS_PORT=6380
    - REDIS_SSL=true
    - REDIS_PASSWORD=<primary/secondary key>
    """
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    password = os.environ.get("REDIS_PASSWORD")  # can be None for local
    use_ssl = os.environ.get("REDIS_SSL", "false").lower() == "true"

    logger.info(
        "Initializing Redis client: host=%s port=%s ssl=%s has_password=%s",
        host,
        port,
        use_ssl,
        bool(password),
    )

    client = redis.Redis(
        host=host,
        port=port,
        password=password,
        ssl=use_ssl,
        decode_responses=True,  # get strings instead of bytes
        socket_timeout=5,
        socket_connect_timeout=5,
    )

    # Optional: light sanity check on startup (won't crash app if fails)
    try:
        client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.warning("Could not ping Redis on startup: %s", e)

    return client

