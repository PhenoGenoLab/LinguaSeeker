"""Phase status bookkeeping shared by the graph adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.runs.contracts import (
    PhaseStatus,
    PhaseStatusDetail,
    PipelineGraphState,
    stage_status_field,
)


def _phase_status(state: PipelineGraphState, phase: int) -> PhaseStatusDetail:
    return getattr(state, stage_status_field(phase))


def begin_phase(state: PipelineGraphState, phase: int) -> None:
    """Mark *phase* as RUNNING with a fresh start timestamp."""
    setattr(
        state,
        stage_status_field(phase),
        PhaseStatusDetail(status=PhaseStatus.RUNNING, started_at=datetime.now().isoformat()),
    )


def complete_phase(state: PipelineGraphState, phase: int, *, summary: dict[str, Any] | None = None) -> None:
    """Mark *phase* as COMPLETED, preserving its start timestamp."""
    setattr(
        state,
        stage_status_field(phase),
        PhaseStatusDetail.complete(started_at=_phase_status(state, phase).started_at, summary=summary),
    )


def skip_phase(state: PipelineGraphState, phase: int, *, summary: dict[str, Any]) -> None:
    """Mark *phase* as SKIPPED, preserving its start timestamp when present."""
    started_at = _phase_status(state, phase).started_at or datetime.now().isoformat()
    setattr(
        state,
        stage_status_field(phase),
        PhaseStatusDetail(
            status=PhaseStatus.SKIPPED,
            started_at=started_at,
            completed_at=datetime.now().isoformat(),
            summary=summary,
        ),
    )
