"""Concrete infrastructure probes for startup health checks."""

from __future__ import annotations

from src.utils.health import register_health_check
from src.utils.logger import get_logger


async def check_postgres() -> bool:
    """Ping PostgreSQL using the wiring singleton engine."""
    logger = get_logger()
    try:
        from sqlalchemy import text

        from src.api.wiring import get_engine

        engine = get_engine()
        if engine is None:
            logger.warning("PostgreSQL health check skipped: engine not initialized")
            return False
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("PostgreSQL health check failed: {}", exc)
        return False


async def check_redis() -> bool:
    """Ping Redis using the wiring singleton client."""
    logger = get_logger()
    try:
        from src.api.wiring import get_redis_client

        client = get_redis_client()
        if client is None:
            logger.debug("Redis health check skipped: client not initialized")
            return False
        pong = await client.ping()
        return bool(pong)
    except Exception as exc:
        logger.debug("Redis health check failed: {}", exc)
        return False


def register_default_health_checks() -> None:
    """Register probes for the services this application depends on."""
    register_health_check("postgres", check_postgres)
    register_health_check("redis", check_redis)
