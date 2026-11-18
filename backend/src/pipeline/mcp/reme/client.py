"""HTTP client for the external ReMe service.

The contract is intentionally small and failure-tolerant: recall degrades to an
empty result and writes report a rejected receipt instead of raising, so a ReMe
outage can never block the clinical evidence path.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx
from loguru import logger

from src.pipeline.mcp.reme.contracts import MemoryCard, MemoryWriteReceipt, RecallResult


class MemoryClient(Protocol):
    """Read/write interface used by the fact-chain skill."""

    def search(self, query: str, *, top_k: int) -> RecallResult: ...

    def auto_memory(self, *, session_id: str, text: str) -> MemoryWriteReceipt: ...

    def auto_resource(self, *, path: str, content: str) -> MemoryWriteReceipt: ...

    def health(self) -> bool: ...


class NullMemoryClient:
    """Inert client used when memory is disabled or unconfigured."""

    def search(self, query: str, *, top_k: int) -> RecallResult:
        return RecallResult()

    def auto_memory(self, *, session_id: str, text: str) -> MemoryWriteReceipt:
        return MemoryWriteReceipt(accepted=False, detail="memory disabled")

    def auto_resource(self, *, path: str, content: str) -> MemoryWriteReceipt:
        return MemoryWriteReceipt(accepted=False, detail="memory disabled")

    def health(self) -> bool:
        return False


class HttpMemoryClient:
    """ReMe HTTP contract: ``/search``, ``/auto_memory``, ``/auto_resource``, ``/health``."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        timeout: float = 0.8,
        client: httpx.Client | None = None,
    ) -> None:
        self._headers = {"X-API-Key": api_key} if api_key else {}
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout, headers=self._headers)

    def search(self, query: str, *, top_k: int) -> RecallResult:
        try:
            response = self._client.post("/search", json={"query": query, "top_k": top_k}, headers=self._headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return RecallResult(
                cards=[MemoryCard.model_validate(card) for card in payload.get("cards", [])],
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("reme search failed, continuing without memory: {}", exc)
            return RecallResult()

    def auto_memory(self, *, session_id: str, text: str) -> MemoryWriteReceipt:
        return self._write("/auto_memory", {"session_id": session_id, "text": text})

    def auto_resource(self, *, path: str, content: str) -> MemoryWriteReceipt:
        return self._write("/auto_resource", {"path": path, "content": content})

    def health(self) -> bool:
        try:
            return self._client.get("/health", headers=self._headers).status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("reme health check failed: {}", exc)
            return False

    def _write(self, endpoint: str, body: dict[str, Any]) -> MemoryWriteReceipt:
        try:
            response = self._client.post(endpoint, json=body, headers=self._headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return MemoryWriteReceipt(
                accepted=bool(payload.get("accepted", True)),
                detail=str(payload.get("detail", "")),
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("reme write failed ({}): {}", endpoint, exc)
            return MemoryWriteReceipt(accepted=False, detail=str(exc))


__all__ = ["HttpMemoryClient", "MemoryClient", "NullMemoryClient"]
