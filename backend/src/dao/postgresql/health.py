"""PostgreSQL connectivity probe for startup health checks."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def ping_postgres(engine: AsyncEngine) -> bool:
    """Execute a lightweight query to verify the engine can connect."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True
