"""Startup dependency health checks.

Call ``check_all_connections()`` during FastAPI lifespan startup to verify
that all critical infrastructure is reachable before accepting requests.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass



@dataclass
class HealthResult:
    """Per-service connectivity status."""

    postgres: bool = False
    redis: bool = False

    def all_ok(self) -> bool:
        """Return True if all checked services are healthy."""
        return self.postgres and self.redis

    def failed_services(self) -> list[str]:
        """Return names of services that are not healthy."""
        return [name for name, ok in self.__dict__.items() if not ok]


# ── Service check registry ───────────────────────────────────────────────
# Composition code registers probes; check_all_connections() runs them.

_CHECK_REGISTRY: dict[str, Callable[[], Awaitable[bool]]] = {}


def register_health_check(name: str, check: Callable[[], Awaitable[bool]]) -> None:
    """Register a connectivity probe under a service name."""
    _CHECK_REGISTRY[name] = check


async def check_all_connections(
    services: list[str] | None = None,
) -> HealthResult:
    """Check infrastructure connections.

    Args:
        services: Service names to check (defaults to all registered).

    Returns:
        HealthResult with per-service connectivity status. Services not in
        the ``services`` filter default to ``False``.
    """
    to_check = services or list(_CHECK_REGISTRY.keys())
    # Default all registered services to False so the result is always complete
    results: dict[str, bool] = {name: False for name in _CHECK_REGISTRY}
    for name in to_check:
        check_fn = _CHECK_REGISTRY.get(name)
        if check_fn is not None:
            results[name] = await check_fn()
    return HealthResult(**results)
