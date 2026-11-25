"""In-memory processing cache (process lifetime only)."""

from __future__ import annotations

from src.runs.contracts import PipelineGraphState
from src.runs.ports import CachedRun


class InMemoryProcessingCache:
    """Store completed run states by content hash in process memory."""

    def __init__(self) -> None:
        self._entries: dict[str, PipelineGraphState] = {}

    async def get_cached_result(self, content_hash: str) -> CachedRun | None:
        state = self._entries.get(content_hash)
        return CachedRun(state=state.model_copy(deep=True), source="memory") if state is not None else None

    async def cache_result(self, content_hash: str, state: PipelineGraphState) -> None:
        self._entries[content_hash] = state.model_copy(deep=True)
