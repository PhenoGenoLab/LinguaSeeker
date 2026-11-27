"""Tests for node-level progress recorded by the LangGraph topology."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.runs.contracts import (
    stage_name,
    stage_status_field,
    PermanentPhaseError,
    PhaseStatus,
    PhaseStatusDetail,
    PipelineGraphState,
    PipelineMode,
    SourceType,
)
from src.pipeline.graph.progress import NodeProgress, record_node
from src.pipeline.graph.topology import PipelineOrchestrator


def _state() -> PipelineGraphState:
    return PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )


def _orchestrator(retry: MagicMock) -> PipelineOrchestrator:
    adapters = {stage_name(n): MagicMock(run=AsyncMock()) for n in range(1, 5)}
    persistence = MagicMock(save=AsyncMock())
    return PipelineOrchestrator(adapters, persistence, retry)


def test_record_node_preserves_existing_summary() -> None:
    status = PhaseStatusDetail(status=PhaseStatus.COMPLETED, summary={"facts": 2})

    record_node(status, NodeProgress(node="acquisition", status="completed", detail="ok"))

    assert status.summary == {
        "facts": 2,
        "nodes": [
            {
                "node": "acquisition",
                "status": "completed",
                "started_at": None,
                "completed_at": None,
                "duration_seconds": None,
                "detail": "ok",
            }
        ],
    }


def test_record_node_appends_multiple_entries() -> None:
    status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
    record_node(status, NodeProgress(node="acquisition", status="completed"))
    record_node(status, NodeProgress(node="acquisition", status="completed"))

    assert [node["status"] for node in status.summary["nodes"]] == ["completed", "completed"]


def test_failed_node_tolerates_malformed_started_at() -> None:
    node = NodeProgress.failed("acquisition", started_at="not-a-timestamp", detail="PermanentPhaseError")

    assert node.duration_seconds is None
    assert node.completed_at is not None


@pytest.mark.asyncio
async def test_successful_phase_records_completed_node() -> None:
    result = _state()
    result.acquisition_status = PhaseStatusDetail(
        status=PhaseStatus.COMPLETED,
        started_at="2026-11-18T10:00:00",
        completed_at="2026-11-18T10:00:01",
        duration_seconds=1.0,
        summary={"pdf": "/tmp/a.pdf"},
    )
    retry = MagicMock(execute_with_retry=AsyncMock(return_value=result))
    orchestrator = _orchestrator(retry)

    updated = await orchestrator._node_acquisition(_state())

    nodes = updated.acquisition_status.summary["nodes"]
    assert nodes == [
        {
            "node": "acquisition",
            "status": "completed",
            "started_at": "2026-11-18T10:00:00",
            "completed_at": "2026-11-18T10:00:01",
            "duration_seconds": 1.0,
            "detail": "",
        }
    ]
    assert updated.acquisition_status.summary["pdf"] == "/tmp/a.pdf"


@pytest.mark.asyncio
async def test_full_run_records_one_node_per_phase() -> None:
    state = _state()
    for phase in range(1, 5):
        setattr(
            state,
            stage_status_field(phase),
            PhaseStatusDetail.complete(started_at="2026-11-18T10:00:00", summary={"phase": phase}),
        )
    retry = MagicMock(execute_with_retry=AsyncMock(return_value=state))
    orchestrator = _orchestrator(retry)

    updated = await orchestrator.run(state)

    assert updated.pipeline_status.value == "completed"
    for phase in range(1, 5):
        summary = getattr(updated, stage_status_field(phase)).summary
        assert summary["phase"] == phase
        assert [node["node"] for node in summary["nodes"]] == [stage_name(phase)]
        assert summary["nodes"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_failed_phase_records_failed_node() -> None:
    retry = MagicMock(execute_with_retry=AsyncMock(side_effect=PermanentPhaseError("boom", phase=1)))
    orchestrator = _orchestrator(retry)

    updated = await orchestrator._node_acquisition(_state())

    assert updated.acquisition_status.status == PhaseStatus.FAILED
    node = updated.acquisition_status.summary["nodes"][0]
    assert node["node"] == "acquisition"
    assert node["status"] == "failed"
    assert node["detail"] == "PermanentPhaseError"
