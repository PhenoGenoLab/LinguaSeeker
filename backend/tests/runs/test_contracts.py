"""Tests for pipeline orchestrator contracts."""

from src.runs.contracts import (
    PipelineGraphState,
    PhaseStatus,
    PipelineMode,
    SourceType,
    PipelineStatus,
    AcquisitionOutput,
    ParseOutput,
    TranslationExtractionOutput,
    StandardizationOutput,
    PhaseErrorDetail,
    PhaseStatusDetail,
    PhaseError,
    RetryablePhaseError,
    PermanentPhaseError,
    SkipStandardizationReason,
)


def test_pipeline_graph_state_creation():
    """State can be created with minimal fields."""
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )
    assert state.processing_run_id == "run-123"
    assert state.source_document_id == "doc-456"
    assert state.acquisition_status.status == PhaseStatus.PENDING
    assert state.parsing_status.status == PhaseStatus.PENDING
    assert state.fact_chain_status.status == PhaseStatus.PENDING
    assert state.standardization_status.status == PhaseStatus.PENDING
    assert state.error_message is None
    assert state.pipeline_status == PipelineStatus.PENDING


def test_pipeline_graph_state_with_structured_error():
    """State can record structured error details per phase."""
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )
    state.acquisition_status = PhaseStatusDetail(
        status=PhaseStatus.FAILED,
        error=PhaseErrorDetail(
            message="Acquisition failed: PDF download timeout",
            retryable=True,
            attempt=2,
            max_retries=2,
        ),
    )
    assert state.acquisition_status.status == PhaseStatus.FAILED
    assert state.acquisition_status.error.retryable is True
    assert state.acquisition_status.error.attempt == 2


def test_pipeline_graph_state_serialization():
    """State serializes to dict for LangGraph persistence."""
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
    )
    data = state.model_dump()
    assert data["processing_run_id"] == "run-123"
    assert data["acquisition_status"]["status"] == "pending"


def test_phase_status_enum():
    """PhaseStatus enum has expected values."""
    assert PhaseStatus.PENDING == "pending"
    assert PhaseStatus.RUNNING == "running"
    assert PhaseStatus.COMPLETED == "completed"
    assert PhaseStatus.SKIPPED == "skipped"
    assert PhaseStatus.FAILED == "failed"


def test_pipeline_status_enum():
    """PipelineStatus enum has expected values."""
    assert PipelineStatus.PENDING == "pending"
    assert PipelineStatus.RUNNING == "running"
    assert PipelineStatus.COMPLETED == "completed"
    assert PipelineStatus.FAILED == "failed"


def test_skip_standardization_reason_enum():
    """SkipStandardizationReason enum captures all skip conditions."""
    assert SkipStandardizationReason.NOT_RELEVANT == "not_relevant"
    assert SkipStandardizationReason.NO_ENTITIES == "no_entities"
    assert SkipStandardizationReason.NO_CANDIDATES == "no_candidates"


def test_phase1_output_typed():
    """AcquisitionOutput (Phase 1) is a typed model, not a bare dict."""
    output = AcquisitionOutput(pdf_path="/tmp/test.pdf")
    assert output.pdf_path == "/tmp/test.pdf"


def test_phase2_output_typed():
    """ParseOutput (Phase 2) is a typed model, not a bare dict."""
    output = ParseOutput(
        md_path="/tmp/test.md",
        metadata_path="/tmp/test.json",
        output_dir="/tmp/parsing",
        images_dir="/tmp/images",
    )
    assert output.metadata_path == "/tmp/test.json"


def test_phase3_output_typed():
    """TranslationExtractionOutput (Phase 3) is a typed model, not a bare dict."""
    output = TranslationExtractionOutput(
        output_dir="/tmp/fact_chain",
        original_json_path="/tmp/original.json",
        translated_json_path="/tmp/translated.json",
        extraction_result_path="/tmp/extraction.json",
        source_language="zh",
    )
    assert output.source_language == "zh"


def test_phase4_output_typed():
    """StandardizationOutput (Phase 4) is a typed model, not a bare dict."""
    output = StandardizationOutput(
        match_count=10,
        standardized_count=8,
        ambiguous_count=1,
        unmapped_count=1,
    )
    assert output.match_count == 10


def test_retryable_phase_error():
    """RetryablePhaseError is an Exception with retry metadata."""
    err = RetryablePhaseError("API timeout", phase=1, attempt=1)
    assert isinstance(err, Exception)
    assert isinstance(err, PhaseError)
    assert isinstance(err, RetryablePhaseError)
    assert err.phase == 1
    assert err.attempt == 1
    assert str(err) == "API timeout"


def test_permanent_phase_error():
    """PermanentPhaseError is an Exception with phase metadata."""
    err = PermanentPhaseError("Configuration error", phase=2)
    assert isinstance(err, Exception)
    assert isinstance(err, PhaseError)
    assert isinstance(err, PermanentPhaseError)
    assert err.phase == 2
    assert str(err) == "Configuration error"


def test_phase_status_detail():
    """PhaseStatusDetail tracks timing and errors per phase."""
    detail = PhaseStatusDetail(
        status=PhaseStatus.COMPLETED,
        started_at="2026-05-29T10:00:00",
        completed_at="2026-05-29T10:05:00",
        duration_seconds=300.0,
    )
    assert detail.status == PhaseStatus.COMPLETED
    assert detail.duration_seconds == 300.0
    assert detail.error is None


def test_pipeline_graph_state_carries_extraction_target() -> None:
    from src.core.tools.extraction.contracts import (
        ExtractionTarget,
    )

    target = ExtractionTarget(gene_symbol="ABCA3", disease_name="ABCA3 deficiency")
    state = PipelineGraphState(
        processing_run_id="run-123",
        source_document_id="doc-456",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
        extraction_target=target,
    )

    assert state.extraction_target == target
    assert state.model_dump()["extraction_target"]["gene_symbol"] == "ABCA3"


def test_legacy_three_phase_state_maps_to_current_stages() -> None:
    """Pre-4-phase rows keep acquisition/parsing/fact-chain/standardization status."""
    legacy = {
        "processing_run_id": "run-legacy",
        "source_document_id": "doc-legacy",
        "mode": "full",
        "source_type": "local",
        "pipeline_status": "completed",
        "phase_1_status": {
            "status": "completed",
            "duration_seconds": 1.0,
            "summary": {"source": "pre_parsed_markdown"},
        },
        "phase_2_status": {
            "status": "completed",
            "duration_seconds": 20.0,
            "summary": {"relevant": True, "target_gene": "ABCA4"},
        },
        "phase_3_status": {
            "status": "completed",
            "duration_seconds": 5.0,
            "summary": {"match_count": 4, "standardized_count": 3},
        },
        "phase_1_output": {
            "md_path": "phase_1/output.md",
            "metadata_path": "phase_1/metadata.json",
            "output_dir": "phase_1",
            "pdf_path": "",
        },
        "phase_2_output": {
            "output_dir": "phase_2",
            "original_json_path": "phase_2/original.json",
            "translated_json_path": "phase_2/translated.json",
            "source_language": "en",
            "extraction_result_path": "phase_2/extraction.json",
        },
        "phase_3_output": {
            "match_count": 4,
            "standardized_count": 3,
            "ambiguous_count": 0,
            "unmapped_count": 1,
        },
    }

    state = PipelineGraphState.model_validate(legacy)

    assert state.acquisition_status.status == PhaseStatus.COMPLETED
    assert state.parsing_status.status == PhaseStatus.COMPLETED
    assert state.fact_chain_status.status == PhaseStatus.COMPLETED
    assert state.standardization_status.status == PhaseStatus.COMPLETED
    assert state.fact_chain_status.duration_seconds == 20.0
    assert state.standardization_status.summary["standardized_count"] == 3
    assert state.parsing_output is not None
    assert state.fact_chain_output is not None
    assert state.standardization_output is not None


def test_legacy_four_phase_state_maps_one_to_one() -> None:
    """Rows using phase_1..phase_4 keep the direct stage mapping."""
    legacy = {
        "processing_run_id": "run-four",
        "source_document_id": "doc-four",
        "mode": "full",
        "source_type": "local",
        "pipeline_status": "completed",
        **{
            f"phase_{number}_status": {"status": "completed", "duration_seconds": float(number)}
            for number in range(1, 5)
        },
    }

    state = PipelineGraphState.model_validate(legacy)

    assert state.acquisition_status.duration_seconds == 1.0
    assert state.parsing_status.duration_seconds == 2.0
    assert state.fact_chain_status.duration_seconds == 3.0
    assert state.standardization_status.duration_seconds == 4.0
