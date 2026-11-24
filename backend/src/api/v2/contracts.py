"""Pydantic models for the v2 API.

Design notes live in ``docs/active/2026-11-24-api-v2-design.md``.
A v2 run covers a whole directory: one batch id groups one run per document.
Every sub-agent can be invoked on its own through the agent job endpoints.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.tools.extraction.contracts import ExtractionTarget

AgentName = Literal["acquisition", "parsing", "fact_chain", "standardization", "review", "graph_retrieval"]
StageName = Literal["acquisition", "parsing", "fact_chain", "standardization"]
RunStatus = Literal["pending", "queued", "running", "completed", "failed", "skipped"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
PipelineModeName = Literal["full", "stage"]


# ── Shared envelopes ────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Uniform error body for v2 routes."""

    code: str
    message: str
    details: dict[str, object] | None = None


class StageErrorResponse(BaseModel):
    """Classified stage error."""

    message: str
    retryable: bool
    attempt: int
    max_retries: int


class StageSummaryResponse(BaseModel):
    """Stage summary payload; keys are stage-specific."""

    model_config = ConfigDict(extra="allow")


class StageNodeResponse(BaseModel):
    """Fine-grained node status inside a stage."""

    node_id: str
    label: str
    status: str
    progress: float | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    count: int | None = None
    metrics: dict[str, object] | None = None
    error: StageErrorResponse | str | None = None


class StageStatusResponse(BaseModel):
    """One stage's status inside a run."""

    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    error: StageErrorResponse | None = None
    summary: StageSummaryResponse | None = None
    nodes: list[StageNodeResponse] = Field(default_factory=list)
    count: int | None = None


class StagesResponse(BaseModel):
    """The four pipeline stages, keyed by stage name."""

    acquisition: StageStatusResponse
    parsing: StageStatusResponse
    fact_chain: StageStatusResponse
    standardization: StageStatusResponse


# ── Directory runs ──────────────────────────────────────────────────────


class DirectoryRunRequest(BaseModel):
    """Start one run per document found in a server-side directory."""

    directory: str = Field(min_length=1, description="Directory relative to the configured pipeline input root")
    recursive: bool = True
    filename_patterns: list[str] = Field(default_factory=lambda: ["*.pdf", "*.docx"])
    max_documents: int = Field(default=200, ge=1, le=2000)
    fail_fast: bool = False
    dry_run: bool = False

    # Extraction options shared by every document in the batch.
    extraction_target: ExtractionTarget | None = None
    extraction_profile: str = "none"
    extraction_mode: Literal["broad", "catalog"] = "broad"
    ablation_disable_review: bool = False
    ablation_disable_target_guard: bool = False
    ablation_disable_grounding: bool = False
    ablation_original_only: bool = False
    review_reject_policy: Literal["hard_veto", "soft_veto", "tristate_review"] = "tristate_review"
    extraction_track_mode: Literal["dual", "original_only", "english_pivot"] = "dual"

    @field_validator("directory")
    @classmethod
    def _relative_directory(cls, value: str) -> str:
        raw = value.strip().replace("\\", "/")
        if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
            raise ValueError("directory must be relative to the pipeline input root")
        normalized = raw.strip("/")
        if not normalized or ".." in normalized.split("/"):
            raise ValueError("directory must be a relative path without '..'")
        return normalized

    @field_validator("filename_patterns")
    @classmethod
    def _patterns(cls, value: list[str]) -> list[str]:
        cleaned = [pattern.strip() for pattern in value if pattern and pattern.strip()]
        if not cleaned:
            raise ValueError("filename_patterns must contain at least one pattern")
        return cleaned


class RunHandle(BaseModel):
    """Handle for one document run inside a batch."""

    processing_run_id: str
    source_document_id: str | None = None
    relative_path: str
    status: RunStatus
    status_url: str


class DirectoryRunResponse(BaseModel):
    """Accepted directory run (202)."""

    batch_id: str
    status: Literal["queued", "accepted", "cached", "dry_run"]
    directory: str
    documents: list[RunHandle] = Field(default_factory=list)
    status_url: str


class BatchCounts(BaseModel):
    """Per-status counts for a batch."""

    total: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0


class BatchStatusResponse(BaseModel):
    """Aggregate status of a directory run."""

    batch_id: str
    directory: str
    status: RunStatus
    counts: BatchCounts
    created_at: str | None = None
    completed_at: str | None = None
    documents: list[RunHandle] = Field(default_factory=list)


class RunStatusResponse(BaseModel):
    """Status of a single document run."""

    processing_run_id: str
    source_document_id: str
    batch_id: str | None = None
    relative_path: str | None = None
    pipeline_status: RunStatus
    current_stage: StageName | None = None
    skip_standardization_reason: str | None = None
    stages: StagesResponse
    error_message: str | None = None
    error_stage: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    elapsed_seconds: float | None = None
    title: str | None = None
    status_url: str | None = None


class RunListResponse(BaseModel):
    """Paginated run list."""

    items: list[RunStatusResponse] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


class StageRerunRequest(BaseModel):
    """Re-run one stage of an existing document run."""

    stage: StageName
    force: bool = False


# ── Agent jobs ──────────────────────────────────────────────────────────


class AgentJobError(BaseModel):
    """Terminal error of an agent job."""

    kind: Literal["transient", "permanent"]
    message: str
    stage: str | None = None


class AgentJobAccepted(BaseModel):
    """202 response for any agent invocation."""

    job_id: str
    agent: AgentName
    status: JobStatus = "queued"
    status_url: str
    result_url: str


class AgentJobStatus(BaseModel):
    """Polling payload for an agent job."""

    job_id: str
    agent: AgentName
    status: JobStatus
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error: AgentJobError | None = None
    result_url: str | None = None


# ── acquisition ─────────────────────────────────────────────────────────


class AcquisitionRequest(BaseModel):
    """Acquire literature either online, from files, or from a directory."""

    mode: Literal["online", "files", "directory"]
    query: str | None = None
    identifiers: list[str] | None = None
    files: list[str] | None = None
    directory: str | None = None
    recursive: bool = True
    relevance_gate: bool = True
    literature_types: list[str] | None = None
    download_pdfs: bool = True

    @model_validator(mode="after")
    def _require_mode_inputs(self) -> AcquisitionRequest:
        if self.mode == "online" and not (self.query or self.identifiers):
            raise ValueError("mode='online' requires query or identifiers")
        if self.mode == "files" and not self.files:
            raise ValueError("mode='files' requires files")
        if self.mode == "directory" and not self.directory:
            raise ValueError("mode='directory' requires directory")
        return self


class AcquiredDocument(BaseModel):
    """One acquired document."""

    path: str
    sha256: str | None = None
    title: str | None = None
    source: Literal["online", "local", "directory"]
    source_document_id: str | None = None


class AcquisitionResult(BaseModel):
    """Result of an acquisition agent job."""

    kind: Literal["acquisition"] = "acquisition"
    agent: Literal["acquisition"] = "acquisition"
    documents: list[AcquiredDocument] = Field(default_factory=list)
    skipped: int = 0


# ── parsing ─────────────────────────────────────────────────────────────


class ParsingRequest(BaseModel):
    """Parse local files or a directory with MinerU."""

    files: list[str] | None = None
    directory: str | None = None
    recursive: bool = True
    output_dir: str | None = None
    force: bool = False

    @model_validator(mode="after")
    def _require_inputs(self) -> ParsingRequest:
        if not self.files and not self.directory:
            raise ValueError("parsing requires files or directory")
        return self


class ParsedDocument(BaseModel):
    """One parsed document artifact set."""

    document_id: str | None = None
    source_path: str
    md_path: str
    metadata_path: str
    images_dir: str | None = None
    pages: int | None = None


class ParsingResult(BaseModel):
    """Result of a parsing agent job."""

    kind: Literal["parsing"] = "parsing"
    agent: Literal["parsing"] = "parsing"
    documents: list[ParsedDocument] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)


# ── fact_chain ──────────────────────────────────────────────────────────


class FactChainSource(BaseModel):
    """Input document, by stored id or by parsed artifact paths."""

    document_id: str | None = None
    md_path: str | None = None
    metadata_path: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> FactChainSource:
        if not self.document_id and not (self.md_path and self.metadata_path):
            raise ValueError("source requires document_id or both md_path and metadata_path")
        return self


class FactChainRequest(BaseModel):
    """Run extraction -> verification -> fact English on one document."""

    source: FactChainSource
    extraction_target: ExtractionTarget | None = None
    extraction_profile: str = "none"
    extraction_mode: Literal["broad", "catalog"] = "broad"
    window_chars: int = Field(default=6000, ge=500)
    window_overlap: int = Field(default=400, ge=0)
    max_provider_calls: int = Field(default=0, ge=0)


class FactChainResult(BaseModel):
    """Result of a fact-chain agent job."""

    kind: Literal["fact_chain"] = "fact_chain"
    agent: Literal["fact_chain"] = "fact_chain"
    document_id: str | None = None
    chain_run_path: str | None = None
    projection_path: str | None = None
    facts: int = 0
    verifications: dict[str, int] = Field(default_factory=dict)
    rejections: list[str] = Field(default_factory=list)
    prompt_versions: dict[str, str] = Field(default_factory=dict)


# ── standardization ─────────────────────────────────────────────────────


class StandardizationSource(BaseModel):
    """Input for standardization, by run id or projection path."""

    document_id: str | None = None
    dual_result_path: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> StandardizationSource:
        if not self.document_id and not self.dual_result_path:
            raise ValueError("source requires document_id or dual_result_path")
        return self


class StandardizationRequest(BaseModel):
    """Standardize entities from one extraction result."""

    source: StandardizationSource
    force: bool = False


class StandardizationResult(BaseModel):
    """Result of a standardization agent job."""

    kind: Literal["standardization"] = "standardization"
    agent: Literal["standardization"] = "standardization"
    document_id: str | None = None
    standardized: int = 0
    unstandardized: int = 0
    ambiguous: int = 0
    output_path: str | None = None
    skipped_reason: str | None = None


# ── graph_retrieval ─────────────────────────────────────────────────────


class GraphRetrievalRequest(BaseModel):
    """Retrieve or question-answer over the literature graph."""

    mode: Literal["retrieve", "qa"] = "retrieve"
    query: str = Field(min_length=1)
    extraction_target: ExtractionTarget | None = None
    hops: int = Field(default=2, ge=1, le=5)


class GraphNode(BaseModel):
    """A node in the returned sub-graph."""

    node_id: str
    node_type: str
    label: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """An edge in the returned sub-graph."""

    source_id: str
    target_id: str
    relation: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphRetrievalResult(BaseModel):
    """Result of a graph-retrieval agent job."""

    kind: Literal["graph_retrieval"] = "graph_retrieval"
    agent: Literal["graph_retrieval"] = "graph_retrieval"
    answer: str | None = None
    context: str | None = None
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


# ── review ──────────────────────────────────────────────────────────────


class ReviewSearchRequest(BaseModel):
    """Evidence search over persisted results."""

    query: str = ""
    document_id: str | None = None
    group_id: str | None = None
    limit: int = Field(default=20, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ReviewFeedbackRequest(BaseModel):
    """Expert feedback on one evidence item."""

    evidence_id: str
    action: Literal["confirm", "reject", "correct"] = "confirm"
    field_name: str | None = None
    corrected_value: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _correction_requires_value(self) -> ReviewFeedbackRequest:
        if self.action == "correct" and not (self.field_name and self.corrected_value):
            raise ValueError("action='correct' requires field_name and corrected_value")
        return self


class ReviewChatRequest(BaseModel):
    """Chat turn grounded in reviewed evidence."""

    session_id: str | None = None
    document_id: str | None = None
    message: str = Field(min_length=1)
    stream: bool = False


class ReviewEvidenceHit(BaseModel):
    """One search hit."""

    evidence_id: str
    document_id: str | None = None
    group_id: str | None = None
    field_name: str | None = None
    snippet: str | None = None
    score: float | None = None


class ReviewSearchResult(BaseModel):
    """Result of a review search job."""

    kind: Literal["review_search"] = "review_search"
    agent: Literal["review"] = "review"
    action: Literal["search"] = "search"
    hits: list[ReviewEvidenceHit] = Field(default_factory=list)
    total: int = 0


class ReviewFeedbackResult(BaseModel):
    """Result of a review feedback job."""

    kind: Literal["review_feedback"] = "review_feedback"
    agent: Literal["review"] = "review"
    action: Literal["feedback"] = "feedback"
    evidence_id: str
    status: str
    delta_id: str | None = None


class ReviewChatResult(BaseModel):
    """Result of a review chat job."""

    kind: Literal["review_chat"] = "review_chat"
    agent: Literal["review"] = "review"
    action: Literal["chat"] = "chat"
    session_id: str
    reply: str
    message_id: str | None = None


# ── Discriminated result union ──────────────────────────────────────────


AgentResult = Annotated[
    AcquisitionResult
    | ParsingResult
    | FactChainResult
    | StandardizationResult
    | GraphRetrievalResult
    | ReviewSearchResult
    | ReviewFeedbackResult
    | ReviewChatResult,
    Field(discriminator="kind"),
]


class AgentJobResultResponse(BaseModel):
    """Result envelope for a finished agent job."""

    job_id: UUID
    result: AgentResult


__all__ = [
    "AcquiredDocument",
    "AcquisitionRequest",
    "AcquisitionResult",
    "AgentJobAccepted",
    "AgentJobError",
    "AgentJobResultResponse",
    "AgentJobStatus",
    "AgentName",
    "AgentResult",
    "BatchCounts",
    "BatchStatusResponse",
    "DirectoryRunRequest",
    "DirectoryRunResponse",
    "ErrorResponse",
    "FactChainRequest",
    "FactChainResult",
    "FactChainSource",
    "GraphEdge",
    "GraphNode",
    "GraphRetrievalRequest",
    "GraphRetrievalResult",
    "ParsedDocument",
    "ParsingRequest",
    "ParsingResult",
    "ReviewChatRequest",
    "ReviewChatResult",
    "ReviewEvidenceHit",
    "ReviewFeedbackRequest",
    "ReviewFeedbackResult",
    "ReviewSearchRequest",
    "ReviewSearchResult",
    "RunHandle",
    "RunListResponse",
    "RunStatus",
    "RunStatusResponse",
    "StageName",
    "StageNodeResponse",
    "StageRerunRequest",
    "StageStatusResponse",
    "StagesResponse",
    "StandardizationRequest",
    "StandardizationResult",
    "StandardizationSource",
]
