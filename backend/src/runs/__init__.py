"""Pipeline run lifecycle.

Public surface only: import from ``src.runs`` (or ``src.runs.contracts`` /
``src.runs.ports``). Modules under ``runtime/`` are implementation details and
must not be imported by other packages.
"""

from __future__ import annotations

from src.runs.contracts import (
    PhaseStatus,
    PipelineGraphState,
    PipelineMode,
    PipelineStatus,
    RunSummary,
    SourceType,
    derive_error_phase,
    stage_output_field,
    stage_status_field,
)
from src.runs.ports import (
    AgentJob,
    AgentJobStore,
    CachedRun,
    ProcessingCache,
    RunJob,
    RunJobQueue,
    RunStateStore,
)
from src.runs.runtime.agent_worker import AgentExecutor, AgentJobFailure, AgentJobWorker
from src.runs.runtime.concurrency import PipelineSemaphore, RetryablePhaseExecutor
from src.runs.runtime.content_hash import compute_content_hash, normalize_identifier
from src.runs.runtime.dispatcher import SingleJobDispatcher
from src.runs.runtime.runner import PipelineRunner

__all__ = [
    "AgentExecutor",
    "AgentJob",
    "AgentJobFailure",
    "AgentJobStore",
    "AgentJobWorker",
    "CachedRun",
    "PhaseStatus",
    "PipelineGraphState",
    "PipelineMode",
    "PipelineRunner",
    "PipelineSemaphore",
    "PipelineStatus",
    "ProcessingCache",
    "RetryablePhaseExecutor",
    "RunJob",
    "RunJobQueue",
    "RunStateStore",
    "RunSummary",
    "SingleJobDispatcher",
    "SourceType",
    "compute_content_hash",
    "derive_error_phase",
    "normalize_identifier",
    "stage_output_field",
    "stage_status_field",
]
