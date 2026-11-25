"""API rate limiting singleton.

Uses Redis-backed storage in production (shared across workers/instances)
with automatic fallback to in-memory storage for local development.

The module-level ``limiter`` is created once and never replaced —
``init_limiter()`` reconfigures its storage so that decorators applied
at import time always reference the same object.
"""

from __future__ import annotations

from limits.storage import MemoryStorage, Storage
from slowapi import Limiter
from slowapi.util import get_remote_address

# Module-level singleton — created once, never replaced.
# Starts with in-memory storage; init_limiter() may upgrade to Redis.
limiter: Limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")


def init_limiter(storage: Storage | None = None) -> Limiter:
    """Reconfigure the module-level *limiter*'s storage backend.

    Called from ``create_app()`` after config is loaded.  Because decorators
    already captured a reference to *limiter*, we must update both
    ``_storage`` and ``_limiter`` (the internal RateLimiter that holds
    a direct reference to the storage object).
    """
    # NOTE: _storage, _limiter, _strategy are slowapi internals.
    # Tested with slowapi 0.1.x. If upgrading slowapi, verify these
    # attributes still exist (smoke test: test_rate_limiting.py).
    from slowapi.extension import STRATEGIES

    strategy = limiter._strategy or "fixed-window"  # noqa: SLF001

    # Update both the storage and the internal RateLimiter that references it
    limiter._storage = storage or MemoryStorage()  # noqa: SLF001
    limiter._limiter = STRATEGIES[strategy](limiter._storage)  # noqa: SLF001
    return limiter
