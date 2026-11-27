"""Validation rules of the v2 API contracts."""

import pytest
from pydantic import ValidationError

from src.api.v2 import contracts as c


@pytest.mark.parametrize("directory", ["../etc", "/abs/path", "a/../../b", "   "])
def test_directory_run_rejects_escaping_paths(directory: str) -> None:
    with pytest.raises(ValidationError):
        c.DirectoryRunRequest(directory=directory)


def test_directory_run_normalises_relative_path() -> None:
    request = c.DirectoryRunRequest(directory="cases/2026-11/")
    assert request.directory == "cases/2026-11"
    assert request.filename_patterns == ["*.pdf", "*.docx"]


def test_agent_result_union_uses_kind_discriminator() -> None:
    parsing = c.AgentJobResultResponse.model_validate(
        {
            "job_id": "3f1c0e6a-5c17-4f6a-9a0e-3d9f0f1c2b3a",
            "result": {"kind": "parsing", "documents": [], "failed": []},
        }
    )
    assert isinstance(parsing.result, c.ParsingResult)

    feedback = c.AgentJobResultResponse.model_validate(
        {
            "job_id": "3f1c0e6a-5c17-4f6a-9a0e-3d9f0f1c2b3a",
            "result": {"kind": "review_feedback", "evidence_id": "e1", "status": "accepted"},
        }
    )
    assert isinstance(feedback.result, c.ReviewFeedbackResult)


def test_fact_chain_source_requires_one_input() -> None:
    with pytest.raises(ValidationError):
        c.FactChainSource()
    with pytest.raises(ValidationError):
        c.FactChainSource(md_path="a.md")
    assert c.FactChainSource(document_id="doc-1").document_id == "doc-1"


def test_review_feedback_correction_requires_value() -> None:
    with pytest.raises(ValidationError):
        c.ReviewFeedbackRequest(evidence_id="e1", action="correct", field_name="gene")
    request = c.ReviewFeedbackRequest(
        evidence_id="e1", action="correct", field_name="gene", corrected_value="BRCA1"
    )
    assert request.corrected_value == "BRCA1"


def test_acquisition_modes_require_their_inputs() -> None:
    with pytest.raises(ValidationError):
        c.AcquisitionRequest(mode="online")
    with pytest.raises(ValidationError):
        c.AcquisitionRequest(mode="files")
    with pytest.raises(ValidationError):
        c.AcquisitionRequest(mode="directory")
    assert c.AcquisitionRequest(mode="directory", directory="inbox").mode == "directory"
