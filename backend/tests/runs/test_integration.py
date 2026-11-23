"""Integration test for full pipeline orchestrator."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.runs.contracts import (
    stage_name,
    stage_status_field,
    PipelineGraphState,
    PipelineMode,
    SourceType,
    PhaseStatus,
    PipelineStatus,
    PhaseStatusDetail,
    AcquisitionOutput,
    ParseOutput,
    SkipStandardizationReason,
)
from src.pipeline.graph.topology import PipelineOrchestrator
from src.runs.concurrency import RetryablePhaseExecutor


def _make_adapters(**returns) -> dict:
    adapters = {stage_name(i): MagicMock(run=AsyncMock()) for i in range(1, 5)}
    for name, state in returns.items():
        adapters[name].run.return_value = state
    return adapters


def _state_after(state: PipelineGraphState, phase: int) -> PipelineGraphState:
    """Copy of state with phases 1..phase COMPLETED (with outputs)."""
    new = state.model_copy(deep=True)
    new.acquisition_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
    new.acquisition_output = AcquisitionOutput(pdf_path="/tmp/test.pdf")
    if phase >= 2:
        new.parsing_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
        new.parsing_output = ParseOutput(
            md_path="/tmp/test.md",
            metadata_path="/tmp/test.json",
            output_dir="/tmp/output",
        )
    for p in range(3, phase + 1):
        setattr(new, stage_status_field(p), PhaseStatusDetail(status=PhaseStatus.COMPLETED))
    return new


@pytest.mark.asyncio
async def test_graph_compiles_and_routes():
    """Orchestrator graph compiles and has correct structure."""
    mock_adapters = _make_adapters()
    mock_persistence = MagicMock(save=AsyncMock())
    retry_executor = RetryablePhaseExecutor(max_retries=0, backoff_base=0.01)

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=retry_executor,
    )

    assert orchestrator._graph is not None

    initial_state = PipelineGraphState(
        processing_run_id="test-run",
        source_document_id="test-doc",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )

    assert initial_state.acquisition_status.status == PhaseStatus.PENDING
    assert initial_state.pipeline_status == PipelineStatus.PENDING


@pytest.mark.asyncio
async def test_upstream_validation_rejects_missing_prerequisites():
    """Orchestrator rejects phase-mode runs without completed upstream."""
    mock_adapters = _make_adapters()
    mock_persistence = MagicMock(save=AsyncMock())
    retry_executor = RetryablePhaseExecutor(max_retries=0, backoff_base=0.01)

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=retry_executor,
    )

    state = PipelineGraphState(
        processing_run_id="test-run",
        source_document_id="test-doc",
        mode=PipelineMode.PHASE,
        source_type=SourceType.LOCAL,
        target_phase=3,
    )

    result = await orchestrator.run(state)

    assert result.pipeline_status == PipelineStatus.FAILED
    assert "upstream" in result.error_message.lower()
    mock_adapters["fact_chain"].run.assert_not_called()


@pytest.mark.asyncio
async def test_persistence_called_after_each_phase():
    """State is persisted to PostgreSQL after each phase completes."""
    state = PipelineGraphState(
        processing_run_id="test-run",
        source_document_id="test-doc",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )

    state_after_1 = _state_after(state, 1)
    state_after_2 = _state_after(state, 2)
    state_after_3 = _state_after(state, 3)
    state_after_4 = _state_after(state, 4)

    mock_adapters = _make_adapters(
        acquisition=state_after_1,
        parsing=state_after_2,
        fact_chain=state_after_3,
        standardization=state_after_4,
    )
    mock_persistence = MagicMock(save=AsyncMock())
    retry_executor = RetryablePhaseExecutor(max_retries=0, backoff_base=0.01)

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=retry_executor,
    )

    await orchestrator.run(state)

    # save() called after each phase + final COMPLETED save
    assert mock_persistence.save.call_count >= 4


@pytest.mark.asyncio
async def test_skip_standardization_reason_flows_through():
    """skip_standardization_reason set by Phase 3 flows to Phase 4 adapter."""
    state = PipelineGraphState(
        processing_run_id="test-run",
        source_document_id="test-doc",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )

    state_after_1 = _state_after(state, 1)
    state_after_2 = _state_after(state, 2)

    state_after_3 = state_after_2.model_copy(deep=True)
    state_after_3.skip_standardization_reason = SkipStandardizationReason.NOT_RELEVANT

    state_after_4 = state_after_3.model_copy(deep=True)
    state_after_4.standardization_status = PhaseStatusDetail(
        status=PhaseStatus.SKIPPED,
        summary={"reason": "not_relevant"},
    )

    mock_adapters = _make_adapters(
        acquisition=state_after_1,
        parsing=state_after_2,
        fact_chain=state_after_3,
        standardization=state_after_4,
    )
    mock_persistence = MagicMock(save=AsyncMock())
    retry_executor = RetryablePhaseExecutor(max_retries=0, backoff_base=0.01)

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=retry_executor,
    )

    result = await orchestrator.run(state)

    assert result.skip_standardization_reason == SkipStandardizationReason.NOT_RELEVANT
    assert result.standardization_status.status == PhaseStatus.SKIPPED
