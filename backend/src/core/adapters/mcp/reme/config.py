"""Resolve the ReMe service settings from the pipeline config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReMeSettings:
    """Validated connection settings for the external service."""

    base_url: str
    api_key: str = ""
    timeout: float = 0.8
    top_k: int = 5


def reme_settings(cfg: Any) -> ReMeSettings | None:
    """Return settings when memory is enabled and a URL is configured."""
    memory = getattr(getattr(cfg, "pipeline", None), "memory", None)
    if memory is None or not getattr(memory, "enabled", False):
        return None
    url = str(getattr(memory, "url", "") or "").strip().rstrip("/")
    if not url:
        return None
    return ReMeSettings(
        base_url=url,
        api_key=str(getattr(memory, "api_key", "") or ""),
        timeout=float(getattr(memory, "timeout", 0.8)),
        top_k=max(1, int(getattr(memory, "top_k", 5))),
    )


__all__ = ["ReMeSettings", "reme_settings"]
