"""In-memory run state store (process lifetime only)."""

from __future__ import annotations

from datetime import datetime

from src.runs.contracts import (
    PhaseStatus,
    PipelineGraphState,
    RunSummary,
    stage_status_field,
)


def _summary(state: PipelineGraphState) -> RunSummary:
    completed = 0
    for phase in (1, 2, 3, 4):
        status = getattr(state, stage_status_field(phase)).status
        if status in (PhaseStatus.COMPLETED, PhaseStatus.SKIPPED):
            completed += 1
    title = state.query or (", ".join(state.identifiers[:5]) if state.identifiers else None) or state.source_key
    return RunSummary(
        processing_run_id=state.processing_run_id,
        owner_user_id=state.owner_user_id,
        pipeline_status=state.pipeline_status.value,
        source_key=state.source_key,
        started_at=state.started_at,
        completed_at=state.completed_at,
        title=title,
        current_phase=None,
        completed_phases=completed,
        total_phases=4,
    )


class InMemoryRunStateStore:
    """Keep run states in a dict; no crash recovery or cross-worker sharing."""

    def __init__(self) -> None:
        self._states: dict[str, PipelineGraphState] = {}

    async def save(
        self,
        state: PipelineGraphState,
        *,
        owner_worker_id: str | None = None,
        heartbeat_at: datetime | None = None,
    ) -> None:
        del owner_worker_id, heartbeat_at
        self._states[state.processing_run_id] = state.model_copy(deep=True)

    async def load(self, processing_run_id: str) -> PipelineGraphState | None:
        state = self._states.get(processing_run_id)
        return state.model_copy(deep=True) if state is not None else None

    async def reset_phase_rerun_artifacts(
        self,
        *,
        processing_run_id: str,
        source_document_id: str | None,
        owner_user_id: str | None = None,
        target_phase: int,
    ) -> None:
        del processing_run_id, source_document_id, owner_user_id, target_phase

    async def recover_orphaned_runs(self, *, heartbeat_timeout_seconds: int = 300) -> int:
        del heartbeat_timeout_seconds
        return 0

    async def heartbeat(self, processing_run_id: str, owner_worker_id: str) -> bool:
        del owner_worker_id
        return processing_run_id in self._states

    async def has_active_source_key(self, source_key: str, owner_user_id: str | None = None) -> bool:
        return any(
            state.source_key == source_key
            and state.owner_user_id == owner_user_id
            and state.pipeline_status.value in ("pending", "running")
            for state in self._states.values()
        )

    async def finalize_review(self, processing_run_id: str) -> PipelineGraphState | None:
        return await self.load(processing_run_id)

    async def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
        owner_user_id: str | None = None,
    ) -> tuple[list[RunSummary], int]:
        summaries = [_summary(state) for state in self._states.values()]
        if status:
            summaries = [item for item in summaries if item.pipeline_status == status]
        if owner_user_id:
            summaries = [item for item in summaries if item.owner_user_id == owner_user_id]
        if search:
            needle = search.casefold()
            summaries = [item for item in summaries if needle in (item.title or "").casefold()]
        summaries.sort(key=lambda item: item.processing_run_id, reverse=True)
        return summaries[offset : offset + limit], len(summaries)
