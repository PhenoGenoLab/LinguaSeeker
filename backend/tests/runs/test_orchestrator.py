"""Tests for main orchestrator graph."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.runs.contracts import (
    stage_status_field,
    PipelineGraphState,
    PhaseStatus,
    PipelineMode,
    SourceType,
    PipelineStatus,
    PhaseStatusDetail,
    AcquisitionOutput,
    ParseOutput,
    SkipStandardizationReason,
    PermanentPhaseError,
)
from src.pipeline.graph.topology import PipelineOrchestrator

PARSE_OUTPUT = ParseOutput(
    md_path="/tmp/test.md",
    metadata_path="/tmp/test.json",
    output_dir="/tmp/output",
)


@pytest.fixture
def sample_state() -> PipelineGraphState:
    return PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )


@pytest.fixture
def mock_adapters():
    return {
        "acquisition": MagicMock(run=AsyncMock()),
        "parsing": MagicMock(run=AsyncMock()),
        "fact_chain": MagicMock(run=AsyncMock()),
        "standardization": MagicMock(run=AsyncMock()),
    }


@pytest.fixture
def mock_persistence():
    return MagicMock(save=AsyncMock())


@pytest.fixture
def mock_retry_executor():
    return MagicMock(execute_with_retry=AsyncMock())


def _completed(sample_state: PipelineGraphState, phase: int) -> PipelineGraphState:
    """Return a copy of the state with phases 1..phase marked COMPLETED (with outputs)."""
    state = sample_state.model_copy(deep=True)
    state.acquisition_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
    state.acquisition_output = AcquisitionOutput(pdf_path="/tmp/test.pdf")
    if phase >= 2:
        state.parsing_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
        state.parsing_output = PARSE_OUTPUT
    for p in range(3, phase + 1):
        setattr(state, stage_status_field(p), PhaseStatusDetail(status=PhaseStatus.COMPLETED))
    return state


@pytest.mark.asyncio
async def test_orchestrator_runs_all_phases(sample_state, mock_adapters, mock_persistence, mock_retry_executor):
    """Orchestrator runs all 4 phases in sequence."""
    state_after_1 = _completed(sample_state, 1)
    state_after_2 = _completed(sample_state, 2)
    state_after_3 = _completed(sample_state, 3)
    state_after_4 = _completed(sample_state, 4)

    mock_adapters["acquisition"].run.return_value = state_after_1
    mock_adapters["parsing"].run.return_value = state_after_2
    mock_adapters["fact_chain"].run.return_value = state_after_3
    mock_adapters["standardization"].run.return_value = state_after_4

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    result_state = await orchestrator.run(sample_state)

    assert result_state.acquisition_status.status == PhaseStatus.COMPLETED
    assert result_state.parsing_status.status == PhaseStatus.COMPLETED
    assert result_state.fact_chain_status.status == PhaseStatus.COMPLETED
    assert result_state.standardization_status.status == PhaseStatus.COMPLETED
    assert result_state.pipeline_status == PipelineStatus.COMPLETED


@pytest.mark.asyncio
async def test_orchestrator_skips_standardization_when_not_relevant(
    sample_state, mock_adapters, mock_persistence, mock_retry_executor
):
    """Orchestrator skips Phase 4 when skip_standardization_reason is set by Phase 3."""
    state_after_1 = _completed(sample_state, 1)
    state_after_2 = _completed(sample_state, 2)

    state_after_3 = state_after_2.model_copy(deep=True)
    state_after_3.fact_chain_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
    state_after_3.skip_standardization_reason = SkipStandardizationReason.NOT_RELEVANT

    state_after_4 = state_after_3.model_copy(deep=True)
    state_after_4.standardization_status = PhaseStatusDetail(status=PhaseStatus.SKIPPED)

    mock_adapters["acquisition"].run.return_value = state_after_1
    mock_adapters["parsing"].run.return_value = state_after_2
    mock_adapters["fact_chain"].run.return_value = state_after_3
    mock_adapters["standardization"].run.return_value = state_after_4

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    result_state = await orchestrator.run(sample_state)

    assert result_state.standardization_status.status == PhaseStatus.SKIPPED
    mock_adapters["standardization"].run.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_stops_on_permanent_failure(
    sample_state, mock_adapters, mock_persistence, mock_retry_executor
):
    """Orchestrator stops execution when a phase raises PermanentPhaseError."""
    mock_adapters["acquisition"].run.side_effect = PermanentPhaseError("Acquisition failed", phase=1)

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    result_state = await orchestrator.run(sample_state)

    assert result_state.acquisition_status.status == PhaseStatus.FAILED
    assert result_state.pipeline_status == PipelineStatus.FAILED
    mock_adapters["parsing"].run.assert_not_called()
    mock_adapters["fact_chain"].run.assert_not_called()
    mock_adapters["standardization"].run.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_validates_upstream_for_phase_mode(mock_adapters, mock_persistence, mock_retry_executor):
    """Orchestrator rejects single-phase mode when upstream phases haven't completed."""
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.PHASE,
        source_type=SourceType.LOCAL,
        target_phase=3,
        acquisition_status=PhaseStatusDetail(status=PhaseStatus.PENDING),
        parsing_status=PhaseStatusDetail(status=PhaseStatus.PENDING),
    )

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    result_state = await orchestrator.run(state)

    assert result_state.pipeline_status == PipelineStatus.FAILED
    assert "upstream" in result_state.error_message.lower()


@pytest.mark.asyncio
async def test_orchestrator_persists_state_after_each_phase(
    sample_state, mock_adapters, mock_persistence, mock_retry_executor
):
    """Orchestrator calls state_persistence.save() after each phase completes."""
    state_after_1 = _completed(sample_state, 1)

    mock_adapters["acquisition"].run.return_value = state_after_1
    mock_adapters["parsing"].run.return_value = state_after_1
    mock_adapters["fact_chain"].run.return_value = state_after_1
    mock_adapters["standardization"].run.return_value = state_after_1

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    await orchestrator.run(sample_state)

    assert mock_persistence.save.call_count >= 4


@pytest.mark.asyncio
async def test_orchestrator_notifies_on_state_change(
    sample_state, mock_adapters, mock_persistence, mock_retry_executor
):
    """on_state_change callback fires after each phase for real-time status updates."""
    state_after_1 = _completed(sample_state, 1)
    state_after_2 = _completed(sample_state, 2)
    state_after_3 = _completed(sample_state, 3)
    state_after_4 = _completed(sample_state, 4)

    mock_adapters["acquisition"].run.return_value = state_after_1
    mock_adapters["parsing"].run.return_value = state_after_2
    mock_adapters["fact_chain"].run.return_value = state_after_3
    mock_adapters["standardization"].run.return_value = state_after_4

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through

    orchestrator = PipelineOrchestrator(
        phase_adapters=mock_adapters,
        state_persistence=mock_persistence,
        retry_executor=mock_retry_executor,
    )

    notifications: list[str] = []
    orchestrator.on_state_change = lambda _run_id, state: notifications.append(state.pipeline_status.value)

    await orchestrator.run(sample_state)

    # Should notify after each of the 4 phases + final COMPLETED update
    assert len(notifications) >= 4
    # Final notification should be "completed"
    assert notifications[-1] == "completed"


@pytest.mark.asyncio
async def test_phase_mode_target_1_stops_after_acquisition(
    sample_state, mock_adapters, mock_persistence, mock_retry_executor
):
    """Phase mode with target_phase=1 runs only Phase 1 and stops."""
    state = sample_state.model_copy(update={"mode": PipelineMode.PHASE, "target_phase": 1})
    state_after_1 = _completed(state, 1)
    mock_adapters["acquisition"].run.return_value = state_after_1

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through
    orchestrator = PipelineOrchestrator(mock_adapters, mock_persistence, mock_retry_executor)

    result = await orchestrator.run(state)

    assert result.acquisition_status.status == PhaseStatus.COMPLETED
    assert result.pipeline_status == PipelineStatus.COMPLETED
    mock_adapters["parsing"].run.assert_not_called()
    mock_adapters["fact_chain"].run.assert_not_called()
    mock_adapters["standardization"].run.assert_not_called()


@pytest.mark.asyncio
async def test_phase_mode_target_2_starts_at_parsing_when_upstream_complete(
    mock_adapters, mock_persistence, mock_retry_executor
):
    """Phase mode with target_phase=2 starts at Phase 2 when Phase 1 is complete."""
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.PHASE,
        source_type=SourceType.LOCAL,
        target_phase=2,
        acquisition_status=PhaseStatusDetail(status=PhaseStatus.COMPLETED),
        acquisition_output=AcquisitionOutput(pdf_path="/tmp/test.pdf"),
    )

    state_after_2 = state.model_copy(deep=True)
    state_after_2.parsing_status = PhaseStatusDetail(status=PhaseStatus.COMPLETED)
    state_after_2.parsing_output = PARSE_OUTPUT
    mock_adapters["parsing"].run.return_value = state_after_2

    async def _pass_through(**kw):
        return await kw["operation"](kw["state"])

    mock_retry_executor.execute_with_retry.side_effect = _pass_through
    orchestrator = PipelineOrchestrator(mock_adapters, mock_persistence, mock_retry_executor)

    result = await orchestrator.run(state)

    assert result.parsing_status.status == PhaseStatus.COMPLETED
    assert result.pipeline_status == PipelineStatus.COMPLETED
    mock_adapters["acquisition"].run.assert_not_called()
    mock_adapters["parsing"].run.assert_called_once()
    mock_adapters["fact_chain"].run.assert_not_called()
    mock_adapters["standardization"].run.assert_not_called()
