"""PostgreSQL + Redis adapter for the document processing cache.

L1 is Redis (fast, volatile), L2 is PostgreSQL (durable). Callers depend on
``src.runs.ports.ProcessingCache``; this module is an implementation detail of
``src.dao``.
"""

from __future__ import annotations

import json
from uuid import UUID

from loguru import logger
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.runs.contracts import PipelineGraphState
from src.runs.ports import CachedRun
from src.dao.postgresql.models import DocumentProcessingCache


# ── Constants ───────────────────────────────────────────────────────────────

_CACHE_PREFIX = "lingseeker:docproc"
_L1_TTL_SECONDS = 3600  # 1 hour


class PostgresProcessingCache:
    """Two-tier cache for document processing results.

    L1 is Redis (fast, volatile), L2 is PostgreSQL (durable). The service
    transparently falls back to L2 when L1 misses, and backfills L1 on
    L2 hits so subsequent lookups are fast.
    """

    def __init__(
        self,
        redis_client: AsyncRedis,
        session_factory: async_sessionmaker[AsyncSession],
        l1_ttl_seconds: int = _L1_TTL_SECONDS,
    ) -> None:
        self._redis = redis_client
        self._session_factory = session_factory
        self._l1_ttl = l1_ttl_seconds

    # ── Public API ──────────────────────────────────────────────────────

    async def get_cached_result(self, content_hash: str) -> CachedRun | None:
        """Look up a cached processing result by content hash.

        Checks L1 (Redis) first, then L2 (PostgreSQL). On L2 hit,
        backfills L1 so subsequent lookups are fast.

        Args:
            content_hash: The 64-char hex SHA-256 content hash.

        Returns:
            CachedRun with the cached PipelineGraphState and its
            source tier, or None if both caches miss.
        """
        # ── L1: Redis ───────────────────────────────────────────────────
        l1_key = self._l1_key(content_hash)
        try:
            raw = await self._redis.get(l1_key)
            if raw is not None:
                state = self._deserialize_state(raw)
                if state is not None:
                    logger.debug("Processing cache L1 hit: hash={}", content_hash[:12])
                    return CachedRun(state=state, source="l1_redis")
        except Exception:
            logger.warning(
                "L1 cache read failed for hash={}, falling back to L2",
                content_hash[:12],
            )

        # ── L2: PostgreSQL ──────────────────────────────────────────────
        l2_result = await self._l2_get(content_hash)
        if l2_result is not None:
            # Backfill L1 so next lookup is fast
            await self._l1_set(content_hash, l2_result.model_dump(mode="json"))
            logger.debug(
                "Processing cache L2 hit (L1 backfilled): hash={}",
                content_hash[:12],
            )
            return CachedRun(state=l2_result, source="l2_postgres")

        return None

    async def cache_result(
        self,
        content_hash: str,
        state: PipelineGraphState,
    ) -> None:
        """Cache a completed pipeline result in both L1 and L2.

        Args:
            content_hash: The 64-char hex content hash.
            state: The final PipelineGraphState to cache.
        """
        state_json = state.model_dump(mode="json")

        # ── L2: PostgreSQL (durable) ────────────────────────────────────
        await self._l2_upsert(content_hash, state)

        # ── L1: Redis (volatile) ────────────────────────────────────────
        await self._l1_set(content_hash, state_json)

        logger.info(
            "Cached processing result: hash={}, run={}",
            content_hash[:12],
            state.processing_run_id,
        )

    # ── L1 Redis helpers ────────────────────────────────────────────────

    def _l1_key(self, content_hash: str) -> str:
        """Build the Redis key for a content hash."""
        return f"{_CACHE_PREFIX}:{content_hash}"

    def _serialize_state(self, state_json: dict) -> bytes:
        """Serialize state dict to bytes for Redis storage."""
        return json.dumps(state_json, ensure_ascii=False).encode("utf-8")

    def _deserialize_state(self, raw: bytes) -> PipelineGraphState | None:
        """Deserialize Redis bytes back to PipelineGraphState."""
        try:
            data = json.loads(raw)
            return PipelineGraphState.model_validate(data)
        except Exception:
            logger.exception("Failed to deserialize cached pipeline state")
            return None

    async def _l1_set(self, content_hash: str, state_json: dict) -> None:
        """Set the L1 Redis cache entry."""
        try:
            await self._redis.set(
                self._l1_key(content_hash),
                self._serialize_state(state_json),
                ex=self._l1_ttl,
            )
        except Exception:
            logger.warning("L1 cache write failed for hash={}", content_hash[:12])

    # ── L2 PostgreSQL helpers ───────────────────────────────────────────

    async def _l2_get(self, content_hash: str) -> PipelineGraphState | None:
        """Query L2 PostgreSQL for a cached result."""
        try:
            async with self._session_factory() as session:
                stmt = select(DocumentProcessingCache.result_state).where(
                    DocumentProcessingCache.content_hash == content_hash
                )
                row = (await session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    return None
                try:
                    return PipelineGraphState.model_validate(row)
                except Exception:
                    logger.exception(
                        "Failed to deserialize L2 cached state for hash={}",
                        content_hash[:12],
                    )
                    return None
        except Exception:
            logger.exception("L2 cache read failed for hash={}", content_hash[:12])
            return None

    async def _l2_upsert(
        self,
        content_hash: str,
        state: PipelineGraphState,
    ) -> None:
        """Upsert a cached result into L2 PostgreSQL."""
        try:
            async with self._session_factory() as session:
                stmt = (
                    pg_insert(DocumentProcessingCache)
                    .values(
                        content_hash=content_hash,
                        source_key=state.source_key,
                        processing_run_id=UUID(state.source_document_id),
                        result_state=state.model_dump(mode="json"),
                    )
                    .on_conflict_do_update(
                        index_elements=["content_hash"],
                        set_={
                            "source_key": state.source_key,
                            "processing_run_id": UUID(state.source_document_id),
                            "result_state": state.model_dump(mode="json"),
                            "updated_at": func.now(),
                        },
                    )
                )
                await session.execute(stmt)
                await session.commit()
        except Exception:
            logger.exception("L2 cache write failed for hash={}", content_hash[:12])
