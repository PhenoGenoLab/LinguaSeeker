"""External-service client registry for the pipeline domain layer."""

from __future__ import annotations

from typing import Any

from src.core.adapters.mcp.reme.client import HttpMemoryClient, MemoryClient, NullMemoryClient
from src.core.adapters.mcp.reme.config import reme_settings


def build_memory_client(cfg: Any) -> MemoryClient:
    """Return a ReMe client, or an inert one when memory is disabled."""
    settings = reme_settings(cfg)
    if settings is None:
        return NullMemoryClient()
    return HttpMemoryClient(
        base_url=settings.base_url,
        api_key=settings.api_key,
        timeout=settings.timeout,
    )


__all__ = ["build_memory_client"]
